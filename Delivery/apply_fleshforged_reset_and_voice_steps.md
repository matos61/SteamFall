# Apply steps for Fleshforged rewrite, tutorial auto-reset, and temporary AI voices

## 1. Pull the review branch

```bash
git checkout feature/intro-playable-review
git pull origin feature/intro-playable-review
```

## 2. Apply the rewritten Fleshforged intro

Copy:
- `Delivery/replacements/fleshforged_prologue.py`

Over:
- `scenes/fleshforged_prologue.py`

Example:

```bash
cp Delivery/replacements/fleshforged_prologue.py scenes/fleshforged_prologue.py
```

## 3. Apply tutorial auto-reset

Copy:
- `Delivery/replacements/tutorial_minigame_autoreset.py`

Over:
- `systems/tutorial_minigame.py`

Example:

```bash
cp Delivery/replacements/tutorial_minigame_autoreset.py systems/tutorial_minigame.py
```

## 4. Commit and push the real source changes

```bash
git add scenes/fleshforged_prologue.py systems/tutorial_minigame.py
git commit -m "Rewrite Fleshforged intro and add tutorial auto-reset"
git push origin feature/intro-playable-review
```

## 5. Test

```bash
python3 main.py --auto-start
```

Check:
- Fleshforged intro now makes Sera's sacrifice the only survival path
- jump tutorial resets if you fall
- long tutorial stalls auto-reset
- attack tutorial still works left and right

## 6. Generate temporary AI voices

```bash
source .venv/bin/activate
pip install elevenlabs
export ELEVENLABS_API_KEY="sk_your_key_here"
python scripts/gen_voices.py --force
```

## 7. Output location

Generated files land in:
- `assets/audio/voice/`
