"""Push queued voice2anki cards into a running Anki through the AnkiConnect add-on.

Exits with code 1 if AnkiConnect is not reachable, so the caller keeps the cards queued.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

URL = os.environ.get("ANKICONNECT_URL", "http://127.0.0.1:8765")


def call(action, **params):
    req = json.dumps({"action": action, "version": 6, "params": params}).encode()
    with urllib.request.urlopen(urllib.request.Request(URL, req), timeout=5) as r:
        res = json.load(r)
    if res.get("error"):
        raise RuntimeError(res["error"])
    return res["result"]


def main(queue):
    try:
        call("version")
    except OSError:
        return 1
    env = os.environ.get
    lines = [l for l in queue.read_text(encoding="utf-8").splitlines() if l.strip()]
    call("createDeck", deck=env("DECK", "English"))
    done = set()
    for line in lines:
        it = json.loads(line)
        if not it.get("translation"):
            continue
        note = {
            "deckName": env("DECK", "English"),
            "modelName": env("NOTE_TYPE", "voice2anki"),
            "fields": {env("FIELD_WORD", "Word"): it["word"],
                       env("FIELD_TRANSLATION", "Translation"): it["translation"],
                       env("FIELD_SENTENCE", "Sentence"): it.get("sentence", ""),
                       env("FIELD_GAME", "Game"): it.get("game", "")},
            "tags": [env("TAG", "voice2anki")],
        }
        try:
            call("addNote", note=note)
            print(f"added via AnkiConnect: {it['word']}")
            done.add(it["id"])
        except RuntimeError as e:
            if "duplicate" in str(e):
                done.add(it["id"])
            print(f"AnkiConnect: {it['word']}: {e}")
    rest = [l for l in lines if json.loads(l)["id"] not in done]
    queue.write_text("".join(l + "\n" for l in rest), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
