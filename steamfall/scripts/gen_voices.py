#!/usr/bin/env python3
"""
scripts/gen_voices.py — Generate AI voice lines for every prologue beat.

SETUP
-----
1. Sign up at https://elevenlabs.io  (free tier: 10k chars/month)
2. Install the SDK:
       pip install elevenlabs
3. Set your key:
       export ELEVENLABS_API_KEY="sk_..."
4. (Optional) Preview available voices, then update VOICE_MAP below:
       python scripts/gen_voices.py --list-voices

RUN
---
    python scripts/gen_voices.py          # generate all missing files
    python scripts/gen_voices.py --force  # re-generate everything

OUTPUT
------
    assets/audio/voice/marked_000.mp3
    assets/audio/voice/marked_001.mp3
    ...
    assets/audio/voice/fleshforged_000.mp3
    ...

Tutorial beats (__tutorial__) are skipped — they have no dialogue.
Already-existing files are skipped unless --force is passed.

CHARACTER EMOTION SETTINGS
---------------------------
ElevenLabs voice settings per character (tuned for emotional range):

  stability:       0.0–1.0. Low = more expressive/variable, High = consistent/flat.
  similarity_boost: 0.0–1.0. How closely to match the target voice.
  style:           0.0–1.0. Low = neutral, High = exaggerated emotion.
  use_speaker_boost: True for maximum clarity (slight quality cost).

We tune these per role:
  Narrator       — low stability, high style: raw, dramatic storytelling
  Kael / Sera    — medium stability, medium-high style: emotional, human
  Elder          — high stability, low style: cold, flat authority
  Dr. Orven      — very high stability, minimal style: clinical detachment
  Recruiter      — high stability, minimal style: military indifference
"""

import os
import re
import sys
import time
import argparse

# ---------------------------------------------------------------------------
# Voice configuration
#
# How to find voice IDs:
#   python scripts/gen_voices.py --list-voices
#
# These defaults use ElevenLabs pre-made voices. Swap any ID for a custom
# clone or a different preset that fits your vision better.
#
# Recommended voices for this game's tone:
#   Narrator  — "Adam"    (deep, intimate baritone)  or  "Daniel" (measured)
#   Kael      — "Callum"  (young, earnest)
#   Elder     — "Arnold"  (deep gravitas)             or  "George"
#   Sera      — "Charlotte" (warm, expressive)        or  "Elli"
#   Dr. Orven — "Antoni"  (smooth, detached)
#   Recruiter — "Daniel"  (flat, authoritative)
# ---------------------------------------------------------------------------

VOICE_MAP = {
    # speaker name (or "" for narrator)  →  (voice_id, stability, similarity, style)
    "":          ("pNInz6obpgDQGcFmaJgB", 0.32, 0.78, 0.72),  # Adam — raw narrator
    "Kael":      ("N2lVS1w4EtoT3dr4eOWO", 0.50, 0.80, 0.55),  # Callum — earnest, quiet
    "Elder":     ("VR6AewLTigWG4xSOukaG", 0.78, 0.75, 0.22),  # Arnold — cold authority
    "Sera":      ("XB0fDUnXU5powFXDhCwa", 0.42, 0.82, 0.68),  # Charlotte — fierce warmth
    "Dr. Orven": ("ErXwobaYiN019PkySvjV", 0.88, 0.78, 0.08),  # Antoni — clinical
    "Recruiter": ("onwK4e9ZLuTAKqWW03F9", 0.82, 0.76, 0.10),  # Daniel — flat authority
}

# ElevenLabs model — turbo is cheapest + fastest; swap for eleven_multilingual_v2
# for richer emotion on non-English text if you localize later.
MODEL_ID = "eleven_turbo_v2_5"

# Output path (relative to repo root)
OUT_DIR  = os.path.join(os.path.dirname(__file__), "..", "assets", "audio", "voice")

# ---------------------------------------------------------------------------
# Beat data — imported from the game modules
# ---------------------------------------------------------------------------

def _get_beats():
    # Walk up to repo root so game imports resolve
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if repo not in sys.path:
        sys.path.insert(0, repo)

    from scenes.marked_prologue     import MARKED_BEATS
    from scenes.fleshforged_prologue import FLESHFORGED_BEATS
    return {
        "marked":      MARKED_BEATS,
        "fleshforged": FLESHFORGED_BEATS,
    }

# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def clean_for_tts(text: str) -> str:
    """Strip markdown emphasis markers and tidy punctuation for TTS."""
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # *word* → word
    text = text.replace("—", ", ")              # em-dash → slight pause
    text = text.replace("...", "… ")            # ellipsis spacing
    return text.strip()

# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate(force: bool = False) -> None:
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY environment variable not set.")
        print("  export ELEVENLABS_API_KEY='sk_...'")
        sys.exit(1)

    try:
        from elevenlabs import ElevenLabs, VoiceSettings
    except ImportError:
        print("ERROR: elevenlabs package not installed.  pip install elevenlabs")
        sys.exit(1)

    client    = ElevenLabs(api_key=api_key)
    beats_map = _get_beats()

    os.makedirs(OUT_DIR, exist_ok=True)

    total_chars   = 0
    generated     = 0
    skipped       = 0
    errors        = 0

    for faction, beats in beats_map.items():
        print(f"\n── {faction.upper()} ({len(beats)} beats) ──")
        for idx, beat in enumerate(beats):
            _, speaker, data = beat

            # Skip tutorial beats
            if speaker == "__tutorial__":
                print(f"  [{idx:03d}] skip (tutorial)")
                continue

            out_path = os.path.join(OUT_DIR, f"{faction}_{idx:03d}.mp3")

            if os.path.exists(out_path) and not force:
                print(f"  [{idx:03d}] already exists — skip  (use --force to overwrite)")
                skipped += 1
                continue

            text = clean_for_tts(data)
            if not text:
                print(f"  [{idx:03d}] empty text — skip")
                continue

            # Look up voice config; fall back to narrator settings
            cfg     = VOICE_MAP.get(speaker, VOICE_MAP[""])
            v_id, stability, similarity, style = cfg

            label = f'"{speaker}"' if speaker else "(narrator)"
            print(f"  [{idx:03d}] {label}: {text[:60]}{'…' if len(text)>60 else ''}")

            try:
                audio_bytes = _call_api(
                    client, text, v_id, stability, similarity, style)
                with open(out_path, "wb") as f:
                    f.write(audio_bytes)
                total_chars += len(text)
                generated   += 1
            except Exception as e:
                print(f"         ERROR: {e}")
                errors += 1

            # Brief pause to respect rate limits (free tier: ~2 req/s)
            time.sleep(0.55)

    print(f"\n── DONE ──")
    print(f"  Generated : {generated}")
    print(f"  Skipped   : {skipped}")
    print(f"  Errors    : {errors}")
    print(f"  Chars used: ~{total_chars:,}  (free tier: 10,000/month)")
    print(f"  Output dir: {os.path.abspath(OUT_DIR)}")


def _call_api(client, text: str, voice_id: str,
              stability: float, similarity: float, style: float) -> bytes:
    from elevenlabs import VoiceSettings
    chunks = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=MODEL_ID,
        output_format="mp3_44100_128",
        voice_settings=VoiceSettings(
            stability=stability,
            similarity_boost=similarity,
            style=style,
            use_speaker_boost=True,
        ),
    )
    # SDK returns a generator of bytes chunks
    return b"".join(chunks)


# ---------------------------------------------------------------------------
# Voice browser
# ---------------------------------------------------------------------------

def list_voices() -> None:
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not set.")
        sys.exit(1)

    try:
        from elevenlabs import ElevenLabs
    except ImportError:
        print("ERROR: pip install elevenlabs")
        sys.exit(1)

    client = ElevenLabs(api_key=api_key)
    voices = client.voices.get_all()
    print(f"\n{'NAME':<28} {'VOICE ID':<26} CATEGORY")
    print("─" * 68)
    for v in sorted(voices.voices, key=lambda x: x.name):
        cat = getattr(v, "category", "")
        print(f"{v.name:<28} {v.voice_id:<26} {cat}")
    print(f"\n{len(voices.voices)} voices available.")
    print("\nCopy voice IDs into VOICE_MAP at the top of this script.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate AI voice lines for Steamfall prologues via ElevenLabs.")
    parser.add_argument("--force",       action="store_true",
                        help="Re-generate files that already exist.")
    parser.add_argument("--list-voices", action="store_true",
                        help="Print available voices and their IDs, then exit.")
    args = parser.parse_args()

    if args.list_voices:
        list_voices()
    else:
        generate(force=args.force)
