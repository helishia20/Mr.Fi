"""
save.py: Persistence — load / write JSON save files.
"""
import json
import time
import os
from config import SAVE_FILE, DEFAULT_STATE


def load_save() -> dict:
    """Return saved state, back-filling any keys that are new since last save."""
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE) as f:
                data = json.load(f)
            for k, v in DEFAULT_STATE.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return dict(DEFAULT_STATE)


def write_save(state: dict) -> bool:
    """Serialise state to disk; return True on success."""
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        return True
    except Exception as e:
        print("save error:", e)
        return False
