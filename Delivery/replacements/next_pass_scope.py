"""
Next pass scope for SteamFall intro polish.

Target areas:
- scenes/marked_prologue.py
- scenes/fleshforged_prologue.py
- systems/dialogue.py
- core/game.py

Goals:
1. convert per-frame fades and timing to dt-based behavior
2. explicitly save intro completion and selected faction state
3. preserve state when the player skips an intro
4. improve dialogue pacing and readability during emotional beats
5. prepare a follow-up gameplay feel pass after tutorial-facing is fixed

Recommended implementation order:

A. Prologue timing
- replace fixed fade decrements with dt-scaled values
- replace fixed background lerp values with dt-scaled interpolation
- keep transition speed visually similar at 60 FPS

B. Story state
- on completion of Marked intro, persist:
  selected_faction = 'marked'
  marked_intro_complete = True
- on completion of Fleshforged intro, persist:
  selected_faction = 'fleshforged'
  fleshforged_intro_complete = True
- on skip, persist the same required values before scene transition

C. Dialogue pacing
- allow a slightly longer beat after emotionally heavy lines
- keep control hints visible but secondary to the line delivery
- avoid making every line require the same cadence of user advancement

D. Save hardening
- ensure save writes are resilient if optional fields are absent
- keep intro completion flags in the same state object used for continue/load

Suggested test checklist:
- start Marked intro and complete normally
- start Marked intro and skip
- start Fleshforged intro and complete normally
- start Fleshforged intro and skip
- confirm continue/load preserves the chosen faction and intro completion
- confirm fades and transitions feel stable at different frame rates
"""
