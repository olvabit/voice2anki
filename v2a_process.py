"""Speech-to-text and translation for voice2anki.

  v2a_process.py capture JOB_DIR QUEUE   transcribe word.wav/sentence.wav, translate, append to queue
  v2a_process.py retranslate QUEUE       fill in translations that failed earlier (e.g. no internet)
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

TARGET_LANG = os.environ.get("TARGET_LANG", "Ukrainian")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "sonnet")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small.en")

# Whisper tends to "hear" these on silence or noise.
HALLUCINATIONS = {"", "you", "thank you", "thanks for watching", "thank you for watching", "bye"}

SYSTEM_PROMPT = f"""You are a dictionary for a {TARGET_LANG} speaker who learns English from video games.
You get an English word or expression (from speech recognition, it may be misheard),
optionally the sentence where it was seen, and the game.
1. Fix the word's spelling if speech recognition clearly misheard it (use the sentence), keep it otherwise.
   Put verbs in base form ("running out of" -> "run out of").
2. Translate ONLY the word or expression (not the sentence) into {TARGET_LANG}, in the sense it has
   in the sentence. Translate phrasal verbs and idioms as a whole. Use correct, natural, common
   {TARGET_LANG} words a native speaker would use (check spelling carefully). Never use Russian
   words, Russian spellings or calques (for Ukrainian: "теча", not "течь"). Give the single best
   translation of 1-4 words; add a second variant after a comma only if it is clearly useful.
Answer with exactly one line: <english word> | <translation>
No quotes, no explanations."""


def notify(title, body=""):
    subprocess.run(["notify-send", "-a", "voice2anki", "-t", "6000", title, body],
                   stderr=subprocess.DEVNULL, check=False)


def transcribe(model, path, prompt):
    if not path.exists() or path.stat().st_size < 16000:  # < ~0.5 s of 16 kHz audio
        return ""
    segments, _ = model.transcribe(str(path), language="en", beam_size=5,
                                   initial_prompt=prompt, condition_on_previous_text=False)
    text = " ".join(s.text.strip() for s in segments).strip()
    return "" if text.lower().strip(" .!?,") in HALLUCINATIONS else text


def translate(word, sentence, game):
    query = f"Game: {game or 'unknown'}\nWord: {word}\nSentence: {sentence or '-'}"
    try:
        out = subprocess.run(
            ["claude", "-p", "--model", CLAUDE_MODEL, "--tools", "", "--no-session-persistence",
             "--strict-mcp-config", "--setting-sources", "", "--system-prompt", SYSTEM_PROMPT, query],
            capture_output=True, text=True, timeout=90, cwd="/tmp")
    except (OSError, subprocess.TimeoutExpired):
        return word, ""
    line = out.stdout.strip().splitlines()[-1] if out.returncode == 0 and out.stdout.strip() else ""
    if "|" not in line:
        return word, line
    fixed, tr = (p.strip() for p in line.split("|", 1))
    return fixed or word, tr


def capture(job, queue):
    from faster_whisper import WhisperModel  # imported lazily: retranslate does not need it

    t0 = time.time()
    model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    word = transcribe(model, job / "word.wav", "A single English word or short phrase.")
    word = word.strip(" .!?,\"'").lower() if word else ""
    if not word:
        notify("voice2anki: no word heard", "Nothing was recognised, try again.")
        return 0
    sentence = transcribe(model, job / "sentence.wav", "")
    game = (job / "game").read_text().strip() if (job / "game").exists() else ""

    word, tr = translate(word, sentence, game)
    item = {"id": job.name, "word": word, "translation": tr, "sentence": sentence,
            "game": game, "created": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(queue, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"captured in {time.time() - t0:.1f}s: {item}", flush=True)
    notify(f"{word} → {tr or '(translation pending)'}", sentence)
    return 0


def retranslate(queue):
    if not queue.exists():
        return 0
    items = [json.loads(l) for l in queue.read_text(encoding="utf-8").splitlines() if l.strip()]
    changed = False
    for it in items:
        if not it.get("translation"):
            it["word"], it["translation"] = translate(it["word"], it.get("sentence", ""), it.get("game", ""))
            changed = changed or bool(it["translation"])
    if changed:
        queue.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items), encoding="utf-8")
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "capture":
        sys.exit(capture(Path(sys.argv[2]), Path(sys.argv[3])))
    if mode == "retranslate":
        sys.exit(retranslate(Path(sys.argv[2])))
    print(__doc__)
    sys.exit(1)
