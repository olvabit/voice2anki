# voice2anki config (sourced by bash). Copy to ~/.config/voice2anki/config.sh

# Python that has faster-whisper installed (e.g. a venv: ~/.venvs/whisper/bin/python)
WHISPER_PYTHON="python3"
# Speech model, runs on CPU so it does not take VRAM from the game: tiny.en, base.en, small.en
WHISPER_MODEL="small.en"

# Translation via Claude Code CLI (`claude -p`)
CLAUDE_MODEL="sonnet"
TARGET_LANG="Ukrainian"

# Anki. ANKI_COLLECTION is used to add cards while Anki is closed.
ANKI_FLATPAK="net.ankiweb.Anki"   # set to "" for a non-Flatpak Anki
ANKI_COLLECTION="$HOME/.var/app/net.ankiweb.Anki/data/Anki2/User 1/collection.anki2"
NOTE_TYPE="voice2anki"            # created automatically if missing
DECK="English"
FIELD_WORD="Word"
FIELD_TRANSLATION="Translation"
FIELD_SENTENCE="Sentence"
FIELD_GAME="Game"
TAG="voice2anki"

# Safety limit for one recording, seconds
MAX_SECONDS=30
