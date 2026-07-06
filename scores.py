"""
scores.py — Persistencia del leaderboard (top 5 por modo) en JSON.
"""
import json
import os

from config import SCORES_FILE, MODE_NORMAL, MODE_TIME

_DEFAULT = {MODE_NORMAL: [], MODE_TIME: []}


def load_scores() -> dict:
    if not os.path.exists(SCORES_FILE):
        return dict(_DEFAULT)
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for mode in _DEFAULT:
            data.setdefault(mode, [])
        return data
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT)


def save_score(mode: str, score: int) -> dict:
    """Agrega un puntaje, conserva el top 5 y guarda a disco."""
    data = load_scores()
    data[mode].append(int(score))
    data[mode] = sorted(data[mode], reverse=True)[:5]
    try:
        with open(SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass
    return data


def best_score(mode: str) -> int:
    data = load_scores()
    return data[mode][0] if data[mode] else 0
