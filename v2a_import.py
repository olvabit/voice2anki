"""Add queued voice2anki cards straight into an Anki collection (Anki must be closed).

Run with Anki's own Python so the `anki` module matches the collection version:
  flatpak run --command=python3 net.ankiweb.Anki -I v2a_import.py COLLECTION QUEUE
"""
import json
import os
import sys
from pathlib import Path

from anki.collection import Collection

NOTE_TYPE = os.environ.get("NOTE_TYPE", "voice2anki")
DECK = os.environ.get("DECK", "English")
TAG = os.environ.get("TAG", "voice2anki")
F_WORD = os.environ.get("FIELD_WORD", "Word")
F_TR = os.environ.get("FIELD_TRANSLATION", "Translation")
F_SENT = os.environ.get("FIELD_SENTENCE", "Sentence")
F_GAME = os.environ.get("FIELD_GAME", "Game")
CONTEXT = f"<br><br><i>{{{{{F_SENT}}}}}</i><br><small>{{{{{F_GAME}}}}}</small>"


def ensure_note_type(col):
    mm = col.models
    m = mm.by_name(NOTE_TYPE)
    if m:
        return m
    m = mm.new(NOTE_TYPE)
    for f in (F_WORD, F_TR, F_SENT, F_GAME):
        mm.add_field(m, mm.new_field(f))
    for name, q, a in (("English → native", F_WORD, F_TR), ("Native → English", F_TR, F_WORD)):
        t = mm.new_template(name)
        t["qfmt"] = f"{{{{{q}}}}}"
        t["afmt"] = f"{{{{FrontSide}}}}<hr id=answer>{{{{{a}}}}}" + CONTEXT
        mm.add_template(m, t)
    m["css"] = ".card { font-family: sans-serif; font-size: 26px; text-align: center; }\n"
    mm.add(m)
    return mm.by_name(NOTE_TYPE)


def main(collection, queue):
    lines = [l for l in queue.read_text(encoding="utf-8").splitlines() if l.strip()]
    ready = [json.loads(l) for l in lines if json.loads(l).get("translation")]
    if not ready:
        return 0
    col = Collection(collection)
    try:
        m = ensure_note_type(col)
        did = col.decks.id(DECK)
        nids = col.find_notes(f'"note:{NOTE_TYPE}"')
        known = {col.get_note(n)[F_WORD].strip().lower() for n in nids}
        done = set()
        for it in ready:
            if it["word"].strip().lower() not in known:
                n = col.new_note(m)
                n[F_WORD], n[F_TR] = it["word"], it["translation"]
                n[F_SENT], n[F_GAME] = it.get("sentence", ""), it.get("game", "")
                n.tags = [TAG]
                col.add_note(n, did)
                known.add(it["word"].strip().lower())
                print(f"added: {it['word']} -> {it['translation']}")
            else:
                print(f"skipped (already in Anki): {it['word']}")
            done.add(it["id"])
    finally:
        col.close()
    rest = [l for l in lines if json.loads(l)["id"] not in done]
    queue.write_text("".join(l + "\n" for l in rest), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], Path(sys.argv[2])))
