# Apply the real code fix locally

This branch gives you a one-command way to apply the live tutorial fix into the real source file.

## Steps

1. Pull the latest review branch:

```bash
git checkout feature/intro-playable-review
git pull origin feature/intro-playable-review
```

2. Make sure the replacement file exists:

```bash
ls Delivery/replacements/tutorial_minigame.py
```

3. Run the helper script:

```bash
bash Delivery/apply_tutorial_facing_fix.sh
```

4. Commit the actual source-file change:

```bash
git add systems/tutorial_minigame.py
git commit -m "Apply tutorial attack facing fix"
git push origin feature/intro-playable-review
```

5. Test it:

```bash
python3 main.py --auto-start
```

## What this changes
- `systems/tutorial_minigame.py` becomes the reviewed replacement version from `Delivery/replacements/tutorial_minigame.py`
- left-facing attacks hit correctly
- right-facing attacks stay correct
- attack arc visual renders on the correct side
