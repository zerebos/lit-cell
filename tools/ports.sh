#!/usr/bin/env bash
# Generate every terminal port from src/*.yml with iTerm2-Color-Schemes' own
# generator, so Lit Cell's ports match the ones that project publishes.
#
# Usage: tools/ports.sh
#
# Uses the clone in $ITERM2_SCHEMES, or clones it into .cache/ at the commit
# below. Its generator needs Python 3.11+ and its requirements:
#   pip install -r .cache/iTerm2-Color-Schemes/requirements.txt
set -euo pipefail

COMMIT=c02052159ff9a1c438ff419b7451cd33f9ab4934
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ITS="${ITERM2_SCHEMES:-$ROOT/.cache/iTerm2-Color-Schemes}"
PYTHON="${PYTHON:-python3}"

if [ ! -d "$ITS/.git" ]; then
  git clone --quiet --filter=blob:none https://github.com/mbadolato/iTerm2-Color-Schemes.git "$ITS"
  git -C "$ITS" checkout --quiet "$COMMIT"
fi

# Their output folder and file extension -> ours.
PORTS=(
  "ghostty::ghostty:"
  "windowsterminal:.json:windows-terminal:.json"
  "alacritty:.toml:alacritty:.toml"
  "kitty:.conf:kitty:.conf"
  "wezterm:.toml:wezterm:.toml"
  "schemes:.itermcolors:iterm2:.itermcolors"
  "foot:.ini:foot:.ini"
  "konsole:.colorscheme:konsole:.colorscheme"
  "vscode:.json:vscode:.json"
)
SCHEMES=("Lit Cell:lit-cell" "Lit Cell Light:lit-cell-light")

cleanup() { git -C "$ITS" clean -fq -- ':(glob)**/Lit Cell*' ':(glob)**/Lit-Cell*'; }
trap cleanup EXIT

for s in "${SCHEMES[@]}"; do
  cp "$ROOT/src/${s#*:}.yml" "$ITS/yaml/${s%%:*}.yml"
done

(cd "$ITS" && "$PYTHON" tools/gen.py -s "Lit Cell" "Lit Cell Light" > /dev/null)

for p in "${PORTS[@]}"; do
  IFS=: read -r from from_ext to to_ext <<< "$p"
  mkdir -p "$ROOT/$to"
  for s in "${SCHEMES[@]}"; do
    cp "$ITS/$from/${s%%:*}$from_ext" "$ROOT/$to/${s#*:}$to_ext"
  done
done

echo "Ports written from src/*.yml."
