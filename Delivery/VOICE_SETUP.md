# AI voice setup for current prologue lines

The repository already contains `scripts/gen_voices.py`, which can generate temporary voice lines for the prologues using ElevenLabs.

## 1. Activate your venv

```bash
cd ~/claude_workspace/steamfall
source .venv/bin/activate
```

## 2. Install the voice dependency

```bash
pip install elevenlabs
```

## 3. Set your API key

```bash
export ELEVENLABS_API_KEY="sk_your_key_here"
```

## 4. Preview available voices

```bash
python scripts/gen_voices.py --list-voices
```

## 5. Generate the voice files

```bash
python scripts/gen_voices.py
```

This writes files like:
- `assets/audio/voice/marked_000.mp3`
- `assets/audio/voice/fleshforged_000.mp3`

## 6. Re-generate after you replace story text

```bash
python scripts/gen_voices.py --force
```

## Suggested casting for the current tone
- Narrator: low, intimate, tired, grave
- Kael: young, loyal, soft but sure
- Sera: warm, stubborn, fierce, intimate
- Elder: calm, ceremonial, cold
- Dr. Orven: detached, clinical, almost bored
- Recruiter: clipped, military, transactional

## Important workflow note
If you apply the rewritten Fleshforged replacement file from this helper PR, run generation again with `--force` so the new Sera and Dr. Orven lines match the updated tragedy arc.
