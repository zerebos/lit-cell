#!/usr/bin/env python3
"""Build Lit Cell's generated files from its design tokens.

The tokens in tokens/ are the source of truth, in the W3C Design Tokens
format (2025.10). This script:

  1. Fills in every color token's components from its hex, and computes the
     hex of every mixed color from its recipe.
  2. Checks the palette: contrast for text colors, readable surfaces, fills
     that really are fills, and that both variants define the same tokens.
  3. Writes src/*.yml (the iTerm2-Color-Schemes source for every terminal
     port), the generated tables in SPEC.md and README.md, and palette.svg.

Usage:
  python tools/build.py           write everything
  python tools/build.py --check   change nothing; fail if anything is out of date

Standard library only. The terminal ports themselves are generated from
src/*.yml by tools/ports.sh.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKENS = ROOT / "tokens"
VARIANTS = ["lit-cell", "lit-cell-light"]
EXT = "dev.zincterminal"
TEXT_MIN = 4.5

problems: list[str] = []


# ── Colors ────────────────────────────────────────────────────────────────

def rgb(hex_: str) -> tuple[int, int, int]:
    h = hex_.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def to_hex(c: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*c)


def mix(color: str, into: str, amount: float) -> str:
    """`amount` of `color` mixed into `into`, in sRGB, rounded per channel."""
    a, b = rgb(color), rgb(into)
    return to_hex(tuple(round(y + (x - y) * amount) for x, y in zip(a, b)))


def luminance(hex_: str) -> float:
    def lin(v: int) -> float:
        s = v / 255
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in rgb(hex_))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def ratio(a: str, b: str) -> str:
    # Text colors are checked against the unrounded ratio, so a "4.5" here is never really 4.46.
    return f"{contrast(a, b):.1f}"


# ── Tokens ────────────────────────────────────────────────────────────────

class Variant:
    def __init__(self, file: str):
        self.file = file
        self.path = TOKENS / f"{file}.tokens.json"
        self.doc = json.loads(self.path.read_text(encoding="utf-8"))
        meta = self.doc["$extensions"][EXT]
        self.name, self.kind, self.author = meta["name"], meta["variant"], meta["author"]

    def groups(self):
        for gname, group in self.doc.items():
            if not gname.startswith("$"):
                yield gname, group

    def tokens(self):
        for gname, group in self.groups():
            for tname, tok in group.items():
                if not tname.startswith("$"):
                    yield f"{gname}.{tname}", tok

    def token(self, path: str) -> dict:
        g, t = path.split(".", 1)
        return self.doc[g][t]

    def hex(self, ref: str) -> str:
        """The hex of `{group.name}` or `group.name`."""
        return self.token(ref.strip("{}"))["$value"]["hex"]

    def ext(self, path: str) -> dict:
        return self.token(path).get("$extensions", {}).get(EXT, {})

    def resolve(self):
        """Compute mixed colors (in order, so mixes can build on mixes) and components."""
        for path, tok in self.tokens():
            v = tok["$value"]
            recipe = self.ext(path).get("mix")
            if recipe:
                v["hex"] = mix(self.hex(recipe["color"]), self.hex(recipe["into"]), recipe["amount"])
            v["hex"] = v["hex"].upper()
            if not re.fullmatch(r"#[0-9A-F]{6}", v["hex"]):
                problems.append(f"{self.file}: {path} has an invalid hex {v['hex']!r}")
                continue
            v["colorSpace"] = "srgb"
            v["components"] = [round(c / 255, 4) for c in rgb(v["hex"])]

    def serialize(self) -> str:
        return dump(self.doc)


def dump(doc) -> str:
    text = json.dumps(doc, indent=2, ensure_ascii=False)
    # Keep each color value on one line: {"colorSpace": ..., "components": [...], "hex": ...}
    text = re.sub(
        r'\{\s*"colorSpace": "(\w+)",\s*"components": \[\s*([^\]]*?)\s*\],\s*"hex": "(#\w+)"\s*\}',
        lambda m: '{ "colorSpace": "%s", "components": [%s], "hex": "%s" }'
        % (m[1], ", ".join(x.strip() for x in m[2].split(",")), m[3]),
        text,
    )
    return text + "\n"


def check(v: Variant):
    bg = v.hex("base.background")
    fg = v.hex("base.foreground")
    for path, _ in v.tokens():
        e = v.ext(path)
        use = e.get("use")
        here = v.hex(path)
        if use == "text":
            on = v.hex(e.get("on", "base.background"))
            if contrast(here, on) < TEXT_MIN:
                problems.append(f"{v.file}: {path} is text but only {ratio(here, on)}:1")
        elif use == "fill":
            if contrast(here, bg) >= TEXT_MIN:
                problems.append(f"{v.file}: {path} is marked fill but reaches {ratio(here, bg)}:1; mark it text")
        elif use == "surface":
            text = v.hex(e.get("text", "base.foreground"))
            if contrast(text, here) < TEXT_MIN:
                problems.append(f"{v.file}: text on {path} is only {ratio(text, here)}:1")


def check_pair(a: Variant, b: Variant):
    ta, tb = dict(a.tokens()), dict(b.tokens())
    if ta.keys() != tb.keys():
        problems.append(f"{a.file} and {b.file} define different tokens: {sorted(ta.keys() ^ tb.keys())}")
        return
    for path in ta:
        for field in ("$description",):
            if ta[path].get(field) != tb[path].get(field):
                problems.append(f"{path}: {field} differs between {a.file} and {b.file}")
        ma, mb = a.ext(path).get("mix"), b.ext(path).get("mix")
        if ma != mb:
            problems.append(f"{path}: mix recipe differs between {a.file} and {b.file}")


def check_roles(roles: dict, variants: list[Variant]):
    for gname, group in roles.items():
        if gname.startswith("$"):
            continue
        for tname, tok in group.items():
            if tname.startswith("$"):
                continue
            ref = tok["$value"]
            if not re.fullmatch(r"\{[\w-]+\.[\w-]+\}", ref):
                problems.append(f"roles: {gname}.{tname} must be a reference, not {ref!r}")
                continue
            for v in variants:
                try:
                    v.hex(ref)
                except KeyError:
                    problems.append(f"roles: {gname}.{tname} refers to {ref}, which {v.file} doesn't define")


# ── src/*.yml ─────────────────────────────────────────────────────────────

def yaml_for(v: Variant) -> str:
    h = v.hex
    lines = [
        f'name: "{v.name}"',
        f'author: "{v.author}"',
        f'variant: "{v.kind}"',
        "",
    ]
    ansi = [n for n, _ in v.tokens() if n.startswith("ansi.")]
    ansi.sort(key=lambda p: v.ext(p)["slot"])
    for i, path in enumerate(ansi):
        lines.append(f'color_{i + 1:02d}: "{h(path)}"')
        if i == 7:
            lines.append("")
    lines += [
        "",
        f'background: "{h("base.background")}"',
        f'foreground: "{h("base.foreground")}"',
        f'cursor: "{h("base.cursor")}"',
        f'cursor_text: "{h("base.cursor-text")}"',
        f'selection: "{h("base.selection")}"',
        f'selection_text: "{h("base.selection-text")}"',
    ]
    return "\n".join(lines) + "\n"


# ── SPEC.md tables ────────────────────────────────────────────────────────

def plain(ref: str) -> str:
    """How SPEC.md names a token: ANSI colors in words, the rest as code."""
    group, name = ref.strip("{}").split(".")
    return name.replace("-", " ") if group == "ansi" else f"`{name}`"


def sentence(desc: str) -> str:
    return desc[:-1] if desc.endswith(".") else desc


def cell(v: Variant, path: str) -> str:
    """The contrast cell beside a color: its ratio if it's text, 'fill', or nothing."""
    e = v.ext(path)
    if e.get("use") == "text":
        star = "*" if "on" in e else ""
        return ratio(v.hex(path), v.hex(e.get("on", "base.background"))) + star
    if e.get("use") == "fill":
        return "fill"
    return ""


def table(head: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def styled(tok: dict, underline_column: bool = False) -> str:
    text = plain(tok["$value"])
    style = tok.get("$extensions", {}).get(EXT, {}).get("style", {})
    if style.get("bold"):
        text += ", bold"
    if style.get("italic"):
        text += ", italic"
    u = style.get("underline")
    if u and not underline_column:
        text += ", underlined" if u == "solid" else f", {u} underline"
    return text


def role_rows(group: dict, underline_column=False):
    for name, tok in group.items():
        if name.startswith("$"):
            continue
        row = [sentence(tok["$description"]), styled(tok, underline_column)]
        if underline_column:
            row.append(tok["$extensions"][EXT]["style"]["underline"])
        yield row


def spec_sections(d: Variant, l: Variant, roles: dict) -> dict[str, str]:
    s = {}
    paths = lambda g: [p for p, _ in d.tokens() if p.startswith(g + ".")]
    desc = lambda p: sentence(d.token(p)["$description"])

    s["base"] = table(
        ["Role", d.name, "", l.name, "", "Use"],
        [[f"`{p.split('.')[1]}`", f"`{d.hex(p)}`", cell(d, p), f"`{l.hex(p)}`", cell(l, p), desc(p)]
         for p in paths("base")],
    )

    ansi = sorted(paths("ansi"), key=lambda p: d.ext(p)["slot"])
    s["ansi"] = table(
        ["Slot", "Name", d.name, "", l.name, "", "Meaning"],
        [[str(d.ext(p)["slot"]), plain("{%s}" % p), f"`{d.hex(p)}`", cell(d, p), f"`{l.hex(p)}`", cell(l, p), desc(p)]
         for p in ansi],
    )

    s["ui"] = table(
        ["Role", "Mix", d.name, "", l.name, "", "Use"],
        [[f"`{p.split('.')[1]}`", f"{round(d.ext(p)['mix']['amount'] * 100)}%",
          f"`{d.hex(p)}`", cell(d, p), f"`{l.hex(p)}`", cell(l, p), desc(p)]
         for p in paths("ui")],
    )

    def tint_mix(p):
        m = d.ext(p)["mix"]
        return f"{plain(m['color'])}, {round(m['amount'] * 100)}%"

    s["tint"] = table(
        ["Role", "Color and mix", d.name, l.name, "Use"],
        [[f"`{p.split('.')[1]}`", tint_mix(p), f"`{d.hex(p)}`", f"`{l.hex(p)}`", desc(p)] for p in paths("tint")],
    )

    for g in ("interface", "syntax", "markdown", "diff"):
        s[g] = table(["Role", "Color"], list(role_rows(roles[g])))
    s["diagnostics"] = table(["Severity", "Color", "Underline"], list(role_rows(roles["diagnostics"], True)))

    s["contrast"] = "\n".join(contrast_summary(v) for v in (d, l))
    return s


def contrast_summary(v: Variant) -> str:
    bg = v.hex("base.background")
    ansi = sorted((p for p, _ in v.tokens() if p.startswith("ansi.")), key=lambda p: v.ext(p)["slot"])
    fills = [plain("{%s}" % p) for p in ansi if v.ext(p).get("use") == "fill"]
    text = [p for p in ansi if v.ext(p).get("use") == "text"]

    def span(ps):
        rs = [float(ratio(v.hex(p), bg)) for p in ps]
        lo, hi = min(rs), max(rs)
        return f"{lo:.1f}:1" if lo == hi else f"{lo:.1f}–{hi:.1f}:1"

    normal = [p for p in text if 1 <= v.ext(p)["slot"] <= 7]
    bright = [p for p in text if 9 <= v.ext(p)["slot"] <= 15]
    out = f"- **{v.name}:** "
    out += f"normal colors are {span(normal)} and bright colors {span(bright)}. "
    out += f"Bright black, for comments, is {ratio(v.hex('ansi.bright-black'), bg)}:1. "
    if fills:
        out += f"Fills only, never text: {' and '.join(fills)}."
    return out


MARK = re.compile(r"(<!-- generated:(\w+) -->\n)(.*?)(<!-- /generated -->)", re.S)


def readme_palette(d: Variant, l: Variant) -> str:
    rows = [[label, f"`{d.hex(p)}`", f"`{l.hex(p)}`"] for label, p in
            [("Background", "base.background"), ("Foreground", "base.foreground"),
             ("Cursor", "base.cursor"), ("Selection", "base.selection")]]
    for name in ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]:
        n, b = f"ansi.{name}", f"ansi.bright-{name}"
        rows.append([f"{name.capitalize()} / bright", f"`{d.hex(n)}` / `{d.hex(b)}`", f"`{l.hex(n)}` / `{l.hex(b)}`"])
    return table(["", d.name, l.name], rows)


def fill_spec(text: str, sections: dict[str, str], file: str = "SPEC.md") -> str:
    seen = set()

    def sub(m):
        seen.add(m[2])
        if m[2] not in sections:
            problems.append(f"{file} has a marker for an unknown section {m[2]!r}")
            return m[0]
        return m[1] + sections[m[2]] + "\n" + m[4]

    text = MARK.sub(sub, text)
    for missing in sections.keys() - seen:
        problems.append(f"{file} is missing the marker <!-- generated:{missing} -->")
    return text


# ── palette.svg ───────────────────────────────────────────────────────────

def palette_svg(variants: list[Variant]) -> str:
    W, H, GAP, PAD, SW, SH = 880, 250, 16, 28, 92, 44
    step = (W - 2 * PAD - SW) / 7
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{len(variants) * (H + GAP) - GAP}" '
        f'viewBox="0 0 {W} {len(variants) * (H + GAP) - GAP}" '
        "font-family=\"ui-monospace, 'Cascadia Mono', 'SF Mono', Menlo, Consolas, monospace\">"
    ]
    for n, v in enumerate(variants):
        top = n * (H + GAP)
        bg, fg, muted = v.hex("base.background"), v.hex("base.foreground"), v.hex("ansi.bright-black")
        out += [
            f'<rect x="0" y="{top}" width="{W}" height="{H}" rx="14" fill="{bg}"/>',
            f'<rect x="0.5" y="{top + 0.5}" width="{W - 1}" height="{H - 1}" rx="13.5" fill="none" stroke="{muted}" stroke-opacity="0.35"/>',
            f'<text x="{PAD}" y="{top + 40}" font-size="18" font-weight="700" fill="{fg}">{v.name}</text>',
            f'<text x="{W - PAD}" y="{top + 40}" font-size="13" text-anchor="end" fill="{muted}">'
            f'bg {bg} · fg {fg} · cursor {v.hex("base.cursor")}</text>',
        ]
        ansi = sorted((p for p, _ in v.tokens() if p.startswith("ansi.")), key=lambda p: v.ext(p)["slot"])
        for p in ansi:
            slot = v.ext(p)["slot"]
            x, y = PAD + (slot % 8) * step, top + 64 + (slot // 8) * 86
            c = v.hex(p)
            # Outline swatches that would vanish into the card.
            edge = f' stroke="{muted}" stroke-opacity="0.5"' if slot == 0 or contrast(c, bg) < 1.5 else ""
            out += [
                f'<rect x="{x:.1f}" y="{y}" width="{SW}" height="{SH}" rx="6" fill="{c}"{edge}/>',
                f'<text x="{x:.1f}" y="{y + 60}" font-size="11.5" fill="{fg}">{c}</text>',
                f'<text x="{x:.1f}" y="{y + 74}" font-size="10.5" fill="{muted}">{slot} {plain("{%s}" % p)}</text>',
            ]
    out.append("</svg>")
    return "\n".join(out)


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="change nothing; fail if anything is out of date")
    args = ap.parse_args()

    variants = [Variant(f) for f in VARIANTS]
    for v in variants:
        v.resolve()
    roles = json.loads((TOKENS / "roles.tokens.json").read_text(encoding="utf-8"))

    for v in variants:
        check(v)
    check_pair(*variants)
    check_roles(roles, variants)

    outputs: dict[Path, str] = {}
    for v in variants:
        outputs[v.path] = v.serialize()
        outputs[ROOT / "src" / f"{v.file}.yml"] = yaml_for(v)
    spec = ROOT / "SPEC.md"
    outputs[spec] = fill_spec(spec.read_text(encoding="utf-8"), spec_sections(*variants, roles))
    readme = ROOT / "README.md"
    outputs[readme] = fill_spec(readme.read_text(encoding="utf-8"), {"palette": readme_palette(*variants)}, "README.md")
    outputs[ROOT / "palette.svg"] = palette_svg(variants)

    if problems:
        print("Problems:", *problems, sep="\n  ", file=sys.stderr)
        return 1

    stale = []
    for path, text in outputs.items():
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old == text:
            continue
        stale.append(path.relative_to(ROOT).as_posix())
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")

    if args.check and stale:
        print("Out of date (run python tools/build.py):", *stale, sep="\n  ", file=sys.stderr)
        return 1
    print("Wrote:", *stale, sep="\n  ") if stale else print("Everything is up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
