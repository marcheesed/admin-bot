# modfunctions.py
import json
import os
from dotenv import load_dotenv

load_dotenv()

BANNED_JSON = "banned.json"


def load_banned_words():
    try:
        with open(BANNED_JSON, "r") as f:
            data = json.load(f)
        return [entry["word"].lower() for entry in data]
    except Exception:
        return []


def add_banned_word(new_word: str):
    try:
        with open(BANNED_JSON, "r") as f:
            data = json.load(f)
    except Exception:
        data = []

    data.append({"word": new_word})

    with open(BANNED_JSON, "w") as f:
        json.dump(data, f, indent=4)
