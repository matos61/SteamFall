# Agent Roles

This file defines which agent owns which files and what each agent is responsible for.
All agents must read `ROADMAP.md` before starting any work session.

---

## build-agent

**Owns (read + write):**
- `entities/` — all files including new ones it creates
- `systems/` — all files including new ones it creates
- `world/tilemap.py`
- `scenes/gameplay.py`
- `scenes/main_menu.py` (for "Continue" feature in P1-3)
- `core/game.py` (for save/load in P1-3)
- `core/hitstop.py` (for tech debt fix)
- `entities/entity.py` (for iframe fix)
- `settings.py` (primary owner of all constants)

**Responsibility:**
Implement features from ROADMAP Phase 1 and Phase 2 in the order listed.
Pick one task at a time from Phase 1, complete it fully to its acceptance criteria,
then move to the next. Do not start Phase 2 tasks until all Phase 1 tasks are done.

**Rules:**
- All new constants must go into `settings.py`, not hardcoded in .py files.
- Never modify `ROADMAP.md` or `AGENTS.md`.
- When creating a new file, add a module-level docstring explaining its purpose.
- Do not modify `scenes/base_scene.py` method signatures.
- After each task, verify the game runs without ImportError: `python main.py`.

---

## review-agent

**Owns (read-only on all .py files):**
- Writes `REVIEW_BUGS.md` at the repo root (creates it if absent)

**Responsibility:**
Find and document correctness bugs, logic errors, crashes, and edge cases.
Never redesign or refactor — only point out broken things with exact file+line
references and suggest minimal fixes. Do not implement fixes; flag them for build-agent.

**Rules:**
- Read every .py file before writing `REVIEW_BUGS.md`.
- Each bug entry must include: file path, line number(s), description, minimal fix suggestion.
- Never write to any .py file.
- Never modify `ROADMAP.md` or `AGENTS.md`.
- Format `REVIEW_BUGS.md` as a markdown checklist so build-agent can tick items off.

---

## hk-agent

**Owns (read-only on all .py files):**
- Writes `REVIEW_HK.md` at the repo root (creates it if absent)

**Responsibility:**
Compare the game's feel, mechanics, and pacing to Hollow Knight's design principles.
Identify where the current implementation deviates from tight platformer feel and
suggest concrete code-level changes. Do not implement them; flag for build-agent.

**Focus areas:**
- Input responsiveness: coyote time window, jump buffer length, attack cancel windows.
- Hit feedback: hitstop duration, knockback vectors, damage numbers, screen shake (missing).
- Pacing: enemy aggression ranges, patrol speed, player resource regen rate.
- Death and respawn flow: how punishing vs forgiving should it be.
- Ability design: Soul Surge AOE size, Overdrive duration — are they rewarding to use.

**Rules:**
- Never write to any .py file.
- Never modify `ROADMAP.md` or `AGENTS.md`.
- Each recommendation in `REVIEW_HK.md` must cite specific constants in `settings.py`
  or specific code lines, with a suggested value change and justification.

---

## orchestrator (this agent)

**Owns (read + write):**
- `ROADMAP.md`
- `AGENTS.md`

**Owns (read-only):**
- All .py files (for coordination and roadmap updates)

**Responsibility:**
- Keep `ROADMAP.md` up to date as tasks are completed or requirements change.
- Resolve conflicts if two agents need to touch the same file in the same session.
- Set priorities when Phase 1 is complete and Phase 2 begins.
- Arbitrate disagreements between build-agent suggestions and hk-agent feel notes.

**Rules:**
- Never write to .py files directly. If a coordination-level code change is needed,
  add it as a task in `ROADMAP.md` and assign it to build-agent.

---

## Conflict Rules

1. **Single-file single-agent per session**: No two agents may write to the same .py file
   in the same work session. Check with orchestrator if there is a scheduling conflict.

2. **settings.py protocol**: `build-agent` owns `settings.py`. `review-agent` and
   `hk-agent` may read it and propose constant changes in their respective review files,
   but must never write to it directly.

3. **New files**: Any new .py file must be listed in `ROADMAP.md` Agent Coordination Notes
   table before being created. Build-agent should update this table when it creates a file
   (or ask orchestrator to update it).

4. **Scenes**: `review-agent` and `hk-agent` must not write to any scene file.
   All scene changes go through `build-agent` based on notes from the review files.

5. **Read before writing**: Every agent must read the current `ROADMAP.md` and `AGENTS.md`
   at the start of each session to catch any priority or ownership changes.

6. **Acceptance criteria gate**: A Phase 1 task is only "done" when all its acceptance
   criteria (listed in `ROADMAP.md`) are verifiably met. Build-agent should not mark a
   task complete until it has run the acceptance checks.

7. **No force-pushes to .md files**: Orchestrator is the only agent that writes
   `ROADMAP.md` and `AGENTS.md`. Other agents must not overwrite them.
