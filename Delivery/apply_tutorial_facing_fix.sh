#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT_DIR/Delivery/replacements/tutorial_minigame.py"
DST="$ROOT_DIR/systems/tutorial_minigame.py"

if [[ ! -f "$SRC" ]]; then
  echo "Replacement source not found: $SRC"
  exit 1
fi

cp "$SRC" "$DST"
echo "Applied tutorial facing fix:"
echo "  $SRC -> $DST"
echo
echo "Next steps:"
echo "  git add systems/tutorial_minigame.py"
echo "  git commit -m \"Apply tutorial attack facing fix\""
echo "  git push origin feature/intro-playable-review"
