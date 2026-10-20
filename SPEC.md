# Lit Cell specification

This document defines what each Lit Cell colour is *for*. It's the reference for anyone porting Lit Cell to a new app, so ports agree on meaning, not just hex values.

The hex values live in `src/`. If this document and `src/` ever disagree, `src/` wins and this document gets fixed.

## Principles

1. **A phosphor screen, not a neon sign.** The ground is dark and quiet, with a faint green cast. Colour is used for meaning, and most text stays in the foreground colour.
2. **Green is the signature.** Phosphor green is the accent: the cursor, the active thing, success. Use it where attention belongs, not everywhere.
3. **Status colours mean one thing.** Red is errors and deletions, amber is warnings and changes, green is success and additions. Never use them as decoration.
4. **Readable first.** Text colours meet WCAG AA (4.5:1) against the background. Colours that don't are reserved for backgrounds and fills (see [Contrast](#contrast)).
5. **No new hues.** A port that needs another shade derives it from the palette by mixing (see [Derived colours](#derived-colours)). It never introduces an outside colour.

## Base colours

| Role | Lit Cell | Lit Cell Light | Use |
|---|---|---|---|
| `background` | `#0C110E` | `#F1F4EF` | Main ground |
| `foreground` | `#CFDDD3` | `#1B2620` | Body text, identifiers, punctuation |
| `cursor` | `#3DF2A0` | `#0B7A4B` | Text cursor; the one brightest thing on screen |
| `cursor-text` | `#0C110E` | `#F1F4EF` | Text under a block cursor |
| `selection` | `#1E4533` | `#CBE6D6` | Selection, search highlight background |
| `selection-text` | `#EDEFEA` | `#0F1311` | Text inside a selection |

## The sixteen ANSI colours

Normal colours are the workhorses. Bright colours are for emphasis and for the second level of a hierarchy (for example, a bold heading versus body text in the same hue).

| Slot | Name | Lit Cell | Lit Cell Light | Meaning |
|---|---|---|---|---|
| 0 | black | `#1C2420` | `#1B2620` | Dark fills. In Light, also strong text. |
| 1 | red | `#FF6B6B` | `#AA2826` | Errors, failures, deletions |
| 2 | green | `#3DF2A0` | `#09663F` | Success, additions, the accent |
| 3 | yellow (amber) | `#FFB000` | `#834D00` | Warnings, modifications, attention |
| 4 | blue | `#6FB3F2` | `#225B9D` | Information, links, directories |
| 5 | magenta | `#C99AF2` | `#7E3E98` | Keywords, special values |
| 6 | cyan | `#48D6CF` | `#096561` | Types, hints, secondary information |
| 7 | white | `#B9C7BE` | `#A9B4AD` | Light fills. In Lit Cell, also secondary text. |
| 8 | bright black | `#758679` | `#5F6E66` | Muted text: comments, metadata, line numbers |
| 9 | bright red | `#FF9494` | `#C9382F` | Emphasised errors |
| 10 | bright green | `#86FFC6` | `#0C7E4F` | Emphasised success, strong accent |
| 11 | bright yellow | `#FFCB5C` | `#9E5F00` | Emphasised warnings |
| 12 | bright blue | `#9CCBFF` | `#316FB7` | Emphasised information, visited links |
| 13 | bright magenta | `#DDBCFF` | `#9A4BB9` | Emphasised keywords |
| 14 | bright cyan | `#86ECE6` | `#0C7B75` | Emphasised types and hints |
| 15 | bright white | `#EDEFEA` | `#FFFFFF` | Strongest text in Lit Cell; a fill in Light |

## Derived colours

Some apps need surfaces and borders that a terminal palette doesn't define. Derive them by mixing `foreground` into `background` by the given amount.

| Role | Mix | Lit Cell | Lit Cell Light | Use |
|---|---|---|---|---|
| `surface` | 4% | `#141916` | `#E8ECE7` | Status bars, sidebars, gutters |
| `surface-raised` | 8% | `#1C211E` | `#E0E4DE` | Popups, menus, hover rows, the current line |
| `line` | 16% | `#2B322E` | `#CFD3CE` | Borders, dividers, indent guides |

Muted text (bright black) reaches 4.5:1 on `background` and `surface` only. On `surface-raised`, use `foreground`.

For other tints, such as a translucent highlight, mix a palette colour into `background` the same way rather than adding a new hex value.

## Syntax roles

For editors, pagers (bat, delta) and syntax highlighters. In code, colours are categories, so amber marks constants here rather than warnings.

| Role | Colour |
|---|---|
| Plain code, variables, punctuation | `foreground` |
| Comments | bright black |
| Keywords, storage, control flow | magenta |
| Strings | green |
| Numbers, constants, booleans | yellow |
| Functions, methods | blue |
| Types, classes, interfaces | cyan |
| Properties, fields | bright cyan |
| Escape sequences, regex | bright magenta |
| Invalid code | red, underlined |

**Diagnostics and diffs:** error = red, warning = yellow, info = blue, hint = cyan. Added = green, removed = red, changed = yellow.

**Markdown:** headings = green, bold. Links = blue, underlined. Inline code and code blocks = cyan. Quotes = bright black. Emphasis stays in `foreground`, styled italic or bold.

## Contrast

Measured as WCAG contrast against each variant's background.

- **Lit Cell:** every colour except black is at least 4.5:1. Bright black, for comments, is 4.9:1.
- **Lit Cell Light:** normal colours are about 6.2:1 and bright colours about 4.6:1. Bright black is 4.8:1. White (1.9:1) and bright white are fills only: **never use slots 7 or 15 for text in Light.**
- In Light, prefer the normal colour for text and the bright one for emphasis. In Lit Cell, either works.

## Porting

- Start from `src/` and map by role, using this document, rather than copying another port.
- If an app has a slot this document doesn't cover, pick the closest role and note your choice in the port's README.
- Ports in other repositories are welcome. Open an issue with a link and it will be listed in the main README.
