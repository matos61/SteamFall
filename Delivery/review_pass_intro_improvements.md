# Intro Review Pass — Findings and Improvements

This review pass is based on a code-level walkthrough of the current playable branch.

## Strongest current elements
- Faction identity is much clearer than earlier builds.
- The prologues teach controls through story beats instead of detached menus.
- The Marked path, especially Kael's sacrifice sequence, lands emotionally.
- The Fleshforged path establishes economic brutality and personal stakes quickly.

## Highest-priority issues to fix next

### 1. Prologue skip path loses narrative state
Both `scenes/marked_prologue.py` and `scenes/fleshforged_prologue.py` currently send the player directly to gameplay when ESC is pressed.

That means a skipped intro may fail to preserve:
- selected faction
- faction-specific intro completion
- any future branching or unlock state tied to the intro

Recommended fix:
- before skip transition, persist `selected_faction`
- persist `marked_intro_complete` or `fleshforged_intro_complete`
- write save data before changing scene

### 2. Prologue timing is frame-dependent
Both prologue scenes use fixed per-frame values for:
- fade alpha decrement
- background color interpolation

This makes pacing inconsistent across hardware.

Recommended fix:
- scale fade speed and interpolation with `dt`
- keep 60 FPS visual timing roughly the same

### 3. Dialogue pacing is still too uniform
The dialogue system is visually cleaner, but emotional lines advance with a very even cadence.

Recommended fix:
- allow an optional per-line linger or beat value
- use that for narrator-heavy or emotionally weighted lines
- keep control hints visible but secondary

### 4. Tutorial feedback should teach consequence, not just input
The current tutorial beats are functional but still binary.

Recommended fix:
- add a small pressure element to at least one tutorial per faction
- examples:
  - Marked move tutorial: detection or pursuit pressure
  - Fleshforged jump tutorial: collapsing-shaft urgency indicator

### 5. Continue/load should align with intro completion
`core/game.py` save behavior is straightforward, but intro-specific state should be treated as first-class save data.

Recommended fix:
- keep selected faction in save data
- keep intro completion flags in save data
- allow main menu continue flow to react accordingly later

## Suggested file targets
- `scenes/marked_prologue.py`
- `scenes/fleshforged_prologue.py`
- `systems/dialogue.py`
- `core/game.py`

## Recommended implementation order
1. tutorial attack-facing fix
2. prologue skip-state persistence
3. dt-based timing cleanup
4. dialogue linger support
5. tutorial pressure/readability pass

## Manual test pass after changes
- complete Marked intro normally
- skip Marked intro with ESC
- complete Fleshforged intro normally
- skip Fleshforged intro with ESC
- confirm faction and intro flags are preserved
- verify fade speed feels similar at different frame rates
- verify dialogue still reads cleanly with any added linger behavior
