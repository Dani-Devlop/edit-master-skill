#!/usr/bin/env python3
"""Phase 19 font resolver (CV1/CV3): IG-native tight bold sans.
Primary: Montserrat variable -> ExtraBold instance. Secondary: Inter Bold.
Fallback: DejaVuSans-Bold (honest log). NO serif anywhere in captions/lockups.
"""
import os
from PIL import ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONT = os.path.join(REPO, "assets", "fonts", "Montserrat[wght].ttf")
INTER = os.path.join(REPO, "assets", "fonts", "Inter[opsz,wght].ttf")
DEJAVU_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

_family_used = None
_cache = {}


def _load(path, px, variation):
    f = ImageFont.truetype(path, px)
    try:
        f.set_variation_by_name(variation)
    except Exception:
        pass
    return f


def family_used():
    return _family_used


def sans_bold(px):
    """Caption BODY + lockups: one tight bold sans family (CV1)."""
    global _family_used
    if os.path.exists(MONT):
        _family_used = "Montserrat (variable) ExtraBold"
        key = ("mont", px)
        if key not in _cache:
            _cache[key] = _load(MONT, px, "ExtraBold")
        return _cache[key]
    if os.path.exists(INTER):
        _family_used = "Inter (variable) Bold"
        key = ("inter", px)
        if key not in _cache:
            _cache[key] = _load(INTER, px, "Bold")
        return _cache[key]
    _family_used = "DejaVuSans-Bold (fallback; IG-native font download unavailable)"
    key = ("dj", px)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(DEJAVU_B, px)
    return _cache[key]


def sans_medium(px):
    """Small labels/continuations inside lockups (same family, lighter)."""
    if os.path.exists(MONT):
        key = ("mont_m", px)
        if key not in _cache:
            _cache[key] = _load(MONT, px, "SemiBold")
        return _cache[key]
    return sans_bold(px)
