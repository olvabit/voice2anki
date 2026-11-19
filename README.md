# voice2anki

![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Platform: Linux](https://img.shields.io/badge/platform-Linux-blue)
![Anki](https://img.shields.io/badge/Anki-FSRS-informational)
![Speech: faster-whisper](https://img.shields.io/badge/speech-faster--whisper-orange)
![Translation: Claude](https://img.shields.io/badge/translation-Claude-blueviolet)

**Learn English from video games without pausing them.** Capture new words **by voice** with one hotkey and turn them into [Anki](https://apps.ankiweb.net/) flashcards with a translation that fits the context.

Built for language learners who play games in English (and streamers who translate games live for their audience): you hear or read an unknown word or phrasal verb, press a key, say it, and keep playing. Spaced repetition does the rest.

## Features

- **One hotkey, no alt-tab**: word, sentence, done. Sound cues and a desktop notification with the result.
- **Context-aware translation**: the sentence and the game decide the meaning, phrasal verbs and idioms are translated as a whole, misheard words are corrected.
- **Any target language**: Ukrainian by default, set `TARGET_LANG` to yours.
- **Game-friendly**: speech recognition runs on the CPU, so the game keeps its VRAM.
- **Works offline-first**: no internet or Anki closed? Cards wait in a queue and are added later automatically.
- **Anki-native**: two cards per word (both directions), FSRS scheduling, syncs to AnkiDroid / AnkiMobile as usual.
- **Tiny**: a bash script and three small Python files, no daemon, no GUI.

Press a hotkey, say the word, press again, say the sentence where you saw it, press again. That's it. The game keeps running.

```
[Super+Z] beep → "leak"                                  word
[Super+Z] beep → "There's a leak in the engine room"     sentence (optional, press twice to skip)
[Super+Z] done → notification:  leak → теча, протікання
```

The card lands in Anki with the word, translation, sentence and game name, as two cards (English → native, native → English), scheduled by Anki's FSRS.

## How it works

1. **Recording**: `pw-record` (PipeWire) from the default microphone, 30 s safety limit.
2. **Speech to text**: [faster-whisper](https://github.com/SYSTRAN/faster-whisper) `small.en` **on the CPU**, so it does not take VRAM from the game. About 5–8 s per card on a 4-core CPU.
3. **Translation**: [Claude Code](https://docs.claude.com/en/docs/claude-code) in print mode (`claude -p`, no tools, no session). It sees the sentence and the game, so it picks the right meaning (*leak* → "теча" in a submarine game, not "data leak"), translates phrasal verbs as a whole (*get away with*) and fixes misheard words from the sentence (*"well"* → *weld* in "weld that breach").
4. **Into Anki**:
   - Anki **closed** (usual while gaming): cards are written straight into the collection with Anki's own Python.
   - Anki **open** with [AnkiConnect](https://ankiweb.net/shared/info/2055492159): added immediately.
   - Otherwise cards wait in a queue. A systemd user timer retries every 2 minutes, and also retries translations that failed (no internet).

Duplicates (same word already in the note type) are skipped.

## Requirements

- Linux with PipeWire (`pw-record`), `notify-send`, `canberra-gtk-play`
- Python with `faster-whisper`
- [Claude Code](https://docs.claude.com/en/docs/claude-code) CLI, logged in
- Anki 23.10+ (Flatpak `net.ankiweb.Anki` or a regular install)
- GNOME for the built-in hotkey setup (any desktop works if you bind `voice2anki toggle` yourself)

## Install

```bash
git clone https://github.com/olvabit/voice2anki.git ~/Projects/voice2anki
cd ~/Projects/voice2anki

python3 -m venv ~/.venvs/whisper && ~/.venvs/whisper/bin/pip install faster-whisper
./install.sh --hotkey '<Super>z'
```

Then edit `~/.config/voice2anki/config.sh` (see [config.example.sh](config.example.sh)): the whisper Python, your Anki profile path, deck, note type and field names, and your language.

If the note type does not exist, it is created on the first import with the fields Word / Translation / Sentence / Game.

## Usage

```bash
voice2anki game "Barotrauma"   # game name for the next cards
voice2anki toggle              # what the hotkey runs
voice2anki status              # state and queued cards
voice2anki flush               # push the queue into Anki now
voice2anki cancel              # abort a recording
```

Logs: `~/.local/share/voice2anki/voice2anki.log`.

### Tips

- Single words are harder for speech recognition than sentences. Say the sentence too: it gives Claude the context to fix the word.
- Some games grab the keyboard in fullscreen and block desktop shortcuts. Use borderless windowed mode then.

## License

MIT
