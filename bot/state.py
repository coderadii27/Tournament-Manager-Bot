"""Persistent JSON state for tournaments and giveaways."""

import json
import os
import threading
from typing import Any

_LOCK = threading.Lock()
_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(_DATA_DIR, exist_ok=True)
_FILE = os.path.join(_DATA_DIR, "state.json")

_DEFAULT: dict[str, Any] = {
    "guilds": {},
    "giveaways": {},
}


def _load() -> dict:
    if not os.path.exists(_FILE):
        return json.loads(json.dumps(_DEFAULT))
    try:
        with open(_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in _DEFAULT.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return json.loads(json.dumps(_DEFAULT))


def _save(data: dict) -> None:
    tmp = _FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(tmp, _FILE)


def get_guild(guild_id: int) -> dict:
    with _LOCK:
        data = _load()
        g = data["guilds"].setdefault(
            str(guild_id),
            {
                "tournament_name": "EliteQ-tourny",
                "team_size": 5,
                "max_slots": 16,
                "running": False,
                "paused": False,
                "registration_channel_id": None,
                "confirm_channel_id": None,
                "slot_manager_channel_id": None,
                "teams": [],
                "groups": {},
            },
        )
        _save(data)
        return g


def update_guild(guild_id: int, patch: dict) -> dict:
    with _LOCK:
        data = _load()
        g = data["guilds"].setdefault(str(guild_id), {})
        g.update(patch)
        _save(data)
        return g


def save_guild(guild_id: int, g: dict) -> None:
    with _LOCK:
        data = _load()
        data["guilds"][str(guild_id)] = g
        _save(data)


def get_all_giveaways() -> dict:
    with _LOCK:
        return _load().get("giveaways", {})


def set_giveaway(message_id: int, payload: dict) -> None:
    with _LOCK:
        data = _load()
        data["giveaways"][str(message_id)] = payload
        _save(data)


def remove_giveaway(message_id: int) -> None:
    with _LOCK:
        data = _load()
        data["giveaways"].pop(str(message_id), None)
        _save(data)
