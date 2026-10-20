# Lit Cell specification

This document defines what each Lit Cell color is *for*. It's the reference for anyone porting Lit Cell to a new app, so ports agree on meaning, not just hex values.

The hex values live in `src/`. If this document and `src/` ever disagree, `src/` wins and this document gets fixed. Keep in mind that these are guidelines. Legibility comes first, so when a case isn't covered or a rule makes text hard to read, use your judgement and note the choice in your port.

## Principles

1. **A phosphor screen, not a neon sign.** The ground is dark and quiet, with a faint green cast. Color is used for meaning, and most text stays in the foreground color.
2. **Green is the signature.** Phosphor green is the accent: the cursor, the active thing, success. Use it where attention belongs, not everywhere.
3. **Status colors mean one thing.** Red is errors and deletions, amber is warnings and changes, green is success and additions. Never use them as decoration.
4. **Never color alone.** Red and green are the hardest pair to tell apart for color-blind readers, so meaning is always carried by something else too: an underline shape, a symbol, or position. See [Diagnostics](#diagnostics) and [Diffs](#diffs).
5. **Readable first.** Text colors meet WCAG AA (4.5:1) against the background. Colors that don't are fills only (see [Contrast](#contrast)).
6. **No new hues.** A port that needs another shade derives it by mixing palette colors (see [Derived colors](#derived-colors)). It never introduces an outside color.

## Base colors

Contrast is the WCAG ratio against each variant's background.

| Role | Lit Cell | | Lit Cell Light | | Use |
|---|---|---|---|---|---|
| `background` | `#0C110E` | | `#F1F4EF` | | Main ground |
| `foreground` | `#CFDDD3` | 13.6 | `#1B2620` | 14.1 | Body text, identifiers |
| `cursor` | `#3DF2A0` | 13.1 | `#0B7A4B` | 4.9 | Text cursor; the one brightest thing on screen |
| `cursor-text` | `#0C110E` | | `#F1F4EF` | | Text under a block cursor |
| `selection` | `#1E4533` | | `#CBE6D6` | | Selection background |
| `selection-text` | `#EDEFEA` | 9.3* | `#0F1311` | 14.1* | Text inside a selection |

\* Against `selection`, not `background`.

## The sixteen ANSI colors

Normal colors are the workhorses. Bright colors are for emphasis and for the second level of a hierarchy (for example, a bold heading versus body text in the same hue).

| Slot | Name | Lit Cell | | Lit Cell Light | | Meaning |
|---|---|---|---|---|---|---|
| 0 | black | `#1C2420` | fill | `#1B2620` | 14.1 | Dark fills. In Light, also strong text. |
| 1 | red | `#FF6B6B` | 6.9 | `#AA2826` | 6.2 | Errors, failures, deletions |
| 2 | green | `#3DF2A0` | 13.1 | `#09663F` | 6.3 | Success, additions, the accent |
| 3 | yellow (amber) | `#FFB000` | 10.4 | `#834D00` | 6.3 | Warnings, modifications, attention |
| 4 | blue | `#6FB3F2` | 8.5 | `#225B9D` | 6.2 | Information, links, directories |
| 5 | magenta | `#C99AF2` | 8.5 | `#7E3E98` | 6.2 | Keywords, special values |
| 6 | cyan | `#48D6CF` | 10.7 | `#096561` | 6.2 | Types, hints, secondary information |
| 7 | white | `#B9C7BE` | 10.9 | `#A9B4AD` | fill | Light fills. In Lit Cell, also secondary text. |
| 8 | bright black | `#758679` | 4.9 | `#5F6E66` | 4.8 | Muted text: comments, metadata, line numbers |
| 9 | bright red | `#FF9494` | 9.0 | `#C9382F` | 4.6 | Emphasised errors |
| 10 | bright green | `#86FFC6` | 15.5 | `#0C7E4F` | 4.6 | Emphasised success, strong accent |
| 11 | bright yellow | `#FFCB5C` | 12.7 | `#9E5F00` | 4.6 | Emphasised warnings |
| 12 | bright blue | `#9CCBFF` | 11.3 | `#316FB7` | 4.6 | Emphasised information, visited links |
| 13 | bright magenta | `#DDBCFF` | 11.5 | `#9A4BB9` | 4.6 | Emphasised keywords |
| 14 | bright cyan | `#86ECE6` | 13.7 | `#0C7B75` | 4.6 | Emphasised types and hints |
| 15 | bright white | `#EDEFEA` | 16.5 | `#FFFFFF` | fill | Strongest text in Lit Cell; a fill in Light |

"Fill" means the color is below 4.5:1 and must not be used for text in that variant.

## Derived colors

Some apps need surfaces, borders and tints that a terminal palette doesn't define. Derive them by mixing one color into another by the given amount. Never pick a new hex value by eye.

### Surfaces and text levels

Made by mixing `foreground` into `background`.

| Role | Mix | Lit Cell | | Lit Cell Light | | Use |
|---|---|---|---|---|---|---|
| `surface` | 4% | `#141916` | | `#E8ECE7` | | Status bars, sidebars, gutters |
| `surface-raised` | 8% | `#1C211E` | | `#E0E4DE` | | Popups, menus, hover rows, the current line |
| `line` | 16% | `#2B322E` | | `#CFD3CE` | | Borders, dividers, indent guides |
| `subtext` | 75% | `#9EAAA2` | 7.9 | `#505A54` | 6.5 | Secondary text: labels, sub-headings, operators, status text |

The text hierarchy, from strongest to quietest, is `foreground`, `subtext`, then bright black. Bright black reaches 4.5:1 on `background` and `surface` only; on `surface-raised`, use `subtext` instead.

### Tints

Made by mixing a palette color into `background`. Text on any of these stays at least 4.5:1 in both variants.

| Role | Color and mix | Lit Cell | Lit Cell Light |
|---|---|---|---|
| `search-match` | yellow, 25% | `#49390A` | `#D6CAB3` |
| `search-active` | yellow, 45% | `#795908` | `#C0A983` |
| `diff-added-line` | green, 12% | `#122C20` | `#D5E3DA` |
| `diff-added-text` | green, 25% | `#184932` | `#B7D0C3` |
| `diff-removed-line` | red, 12% | `#291C19` | `#E8DCD7` |
| `diff-removed-text` | red, 25% | `#492825` | `#DFC1BD` |
| `diff-changed-line` | yellow, 12% | `#29240C` | `#E4E0D2` |
| `diff-changed-text` | yellow, 25% | `#49390A` | `#D6CAB3` |

## Interface roles

For terminals, editors and other apps with chrome around the content.

| Role | Color |
|---|---|
| Text on a green or accent fill | `background` ("on accent") |
| Line numbers | bright black |
| Active line number | `foreground` |
| Current line | `surface-raised` |
| Search match / active match | `search-match` / `search-active` background, text unchanged |
| Active border, focused pane | green |
| Inactive border | `line` |
| Bell, attention | yellow |
| Links | blue, underlined |
| Visited links | bright blue, underlined |
| Hovered links | bright blue, underlined |

## Syntax roles

For editors, pagers (bat, delta) and syntax highlighters. In code, colors are categories, so amber marks constants here rather than warnings.

| Role | Color |
|---|---|
| Plain code, variables, parameters | `foreground` |
| Operators, punctuation | `subtext` |
| Comments | bright black |
| Keywords, storage, control flow | magenta |
| Builtins (`self`, `this`, built-in functions) | bright magenta |
| Strings | green |
| Escape sequences, regex | bright yellow |
| Numbers, constants, booleans | yellow |
| Functions, methods | blue |
| Attributes, annotations, decorators | bright blue |
| Types, classes, interfaces | cyan |
| Properties, fields | bright cyan |
| Invalid code | red, wavy underline |

### Markdown

Headings: green, bold.
Links: blue, underlined.
Inline code and code blocks: cyan.
Quotes: bright black.

Emphasis stays in `foreground`, styled italic or bold.

## Diagnostics

Severity is shown by underline shape as well as color, so it reads without color.

| Severity | Color | Underline |
|---|---|---|
| Error | red | wavy |
| Warning | yellow | dashed |
| Info | blue | dotted |
| Hint | cyan | dotted |

## Diffs

Added lines are green, removed lines red, and changed lines yellow. Line and text backgrounds use the [tints](#tints) above. Diffs must keep their `+` and `−` markers or gutter symbols, so additions and deletions never rely on red versus green alone.

| Line | Color |
|---|---|
| File headers (`diff --git`, `---`, `+++`) | `foreground`, bold |
| Extended headers (`index`, `new file mode`, `rename from`, `similarity index` and similar) | bright black |
| Hunk headers (`@@ … @@`) | cyan |
| Context lines | `foreground` |

This stays close to git's defaults, which make every header bold. Lit Cell dims the extended headers, since they're metadata, so the file names stand out.

## Contrast

- **Lit Cell:** every color except black is at least 4.5:1. Bright black, for comments, is 4.9:1.
- **Lit Cell Light:** normal colors are about 6.2:1 and bright colors about 4.6:1. Bright black is 4.8:1. White and bright white are fills only: **never use slots 7 or 15 for text in Light.**
- In Light, prefer the normal color for text and the bright one for emphasis. In Lit Cell, either works.

## Porting

- Start from `src/` and map by role, using this document, rather than copying another port.
- If an app has a slot this document doesn't cover, pick the closest role and note your choice in the port's README.
- Ports in other repositories are welcome. Open an issue with a link and it will be listed in the main README.