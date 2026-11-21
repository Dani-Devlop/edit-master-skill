#!/usr/bin/env python3
"""Phase 8.0 step 3: per-category style sheets + depth anchors (16 reps).

Family:
  F1 TALKING-HEAD STACK - giant type BEHIND masked person (u2net matte)
  F2 HERO OBJECT        - giant type BEHIND masked salient object (u2net matte)
  F3 WORLD PAN          - footage-first, giant type under duotone scrim (honest:
                          no matte occlusion claim), elements in lower safe band
Palettes/sig kits come from docs/STYLES.md (Phase 5.0 sheets).
"""
import json, os

STYLES = {
    "talkinghead_1": dict(
        cat="TALKING-HEAD", family="F1",
        accent=(232, 120, 80), secondary=(255, 210, 180), ink=(24, 16, 12),
        type_fill="white", extrude="accent_dark", halftone="accent", sticker="accent",
        card_border=(232, 120, 80), pill_bg=(232, 120, 80),
        bg_tint=(255, 244, 228, 14),
        types=[("NOBODY", "FINISHES"), ("TALKS", "TOO SLOW"), ("CUT", "DEAD AIR"),
               ("KEEP THE", "LEAN-IN")],
        payoff=("REWIND", None),
        cards=[("the guest", 1.5), ("the cut", 7.0), ("the flow", 12.0)],
        labels=["my name is", "the socials", "step 01", "step 02"],
        sig_pill="SPEAKER TAKEOVER", stickers=["bolt", "play", "headphones", "clapper", "arrow", "star"],
        insert="surreal 3D dream world, astronaut sitting on a giant floating smartphone screen among soft clouds, terracotta and cream palette, halftone dot texture sky, volumetric light, vertical, cinematic render, no text, no watermark",
    ),
    "podcast_1": dict(
        cat="PODCAST", family="F1",
        accent=(255, 190, 70), secondary=(240, 240, 240), ink=(26, 20, 14),
        type_fill="white", extrude="accent_dark", halftone="accent", sticker="accent",
        card_border=(255, 190, 70), pill_bg=(255, 190, 70),
        bg_tint=(255, 236, 210, 14),
        types=[("RECORD", "LIKE THAT"), ("TWO", "MICS"), ("THE ROOM", "IS THE STUDIO"),
               ("SOUND", "EXPENSIVE")],
        payoff=("REWIND", None),
        cards=[("the setup", 1.2), ("the room", 6.0), ("the talk", 8.5)],
        labels=["on air", "two mics", "step 01", "step 02"],
        sig_pill="REC 00:26", stickers=["play", "headphones", "star", "bolt", "arrow", "clapper"],
        insert="surreal 3D dream world, giant condenser microphone growing out of a warm amber cloud island, recording cables as rivers of light, amber and cream palette, halftone dot sky, vertical, cinematic render, no text, no watermark",
    ),
    "education_1": dict(
        cat="EDUCATION", family="F1",
        accent=(28, 80, 160), secondary=(240, 246, 255), ink=(24, 42, 84),
        type_fill="ink", extrude="accent", halftone="accent", sticker="accent",
        card_border=(28, 80, 160), pill_bg=(28, 80, 160),
        bg_tint=(240, 246, 255, 16),
        types=[("THE", "MISTAKE"), ("LINE", "CONFIDENCE"), ("INK COMES", "LAST"),
               ("FIX THE", "MISTAKE")],
        payoff=("RUN IT", "BACK"),
        cards=[("the sketch", 1.4), ("the line", 5.5), ("the ink", 8.0)],
        labels=["step 01", "step 02", "sketch light", "ink last"],
        sig_pill="DAILY DRILL", stickers=["star", "arrow", "play", "bolt", "rocket", "clapper"],
        insert="surreal 3D dream world, open notebook floating in soft blue daylight with giant pencil towers and paper clouds, blue ink rivers, clean minimal palette, vertical, cinematic render, no text, no watermark",
    ),
    "fitness_1": dict(
        cat="FITNESS", family="F1",
        accent=(180, 255, 0), secondary=(255, 255, 255), ink=(10, 14, 6),
        type_fill="accent", extrude="accent_dark", halftone="accent", sticker="accent",
        card_border=(180, 255, 0), pill_bg=(180, 255, 0),
        bg_tint=(10, 14, 6, 18),
        types=[("DO NOT", "POST IT"), ("CUT ON", "THE EXHALE"), ("SWEAT IS", "THE AESTHETIC"),
               ("NOW", "POST IT")],
        payoff=("RUN IT", "BACK"),
        cards=[("the set", 2.0), ("the exhale", 8.0), ("the rep", 13.0)],
        labels=["rep 08/12", "beats under effort", "step 01", "step 02"],
        sig_pill="REP COUNTER 8/12", stickers=["bolt", "rocket", "play", "star", "arrow", "headphones"],
        insert="surreal 3D dream world, athlete silhouette holding a giant volt-green barbell made of light above clouds, dark gym sky, volt and white palette, halftone texture, vertical, cinematic render, no text, no watermark",
    ),
    "food_1": dict(
        cat="FOOD", family="F2",
        accent=(255, 107, 53), secondary=(255, 190, 120), ink=(30, 16, 8),
        type_fill="white", extrude="accent_dark", halftone="accent", sticker="accent",
        card_border=(255, 107, 53), pill_bg=(255, 107, 53),
        bg_tint=(255, 226, 200, 14),
        types=[("COSTS", "NOTHING"), ("SIDE LIGHT", "ONLY"), ("READS", "$4,000"),
               ("ONE WINDOW", "ZERO GEAR")],
        payoff=("ONE MORE", "TIME"),
        cards=[("window light", 1.5), ("the crop", 5.5), ("the glints", 9.0)],
        labels=["order up", "fresh", "step 01", "step 02"],
        sig_pill="READS $4,000", stickers=["star", "play", "arrow", "rocket", "bolt", "clapper"],
        insert="surreal 3D dream world, giant gourmet dish floating on a warm orange cloud with fruit towers and light glints, dark wood sky, orange and cream palette, halftone dots, vertical, cinematic render, no text, no watermark",
    ),
    "product_2": dict(
        cat="PRODUCT", family="F2",
        accent=(40, 120, 255), secondary=(245, 247, 250), ink=(16, 34, 66),
        type_fill="ink", extrude="accent", halftone="accent", sticker="accent",
        card_border=(40, 120, 255), pill_bg=(40, 120, 255),
        bg_tint=(240, 246, 255, 12),
        types=[("NO MORE", "WHITE"), ("HANDS ADD", "SCALE"), ("SCREEN GLOW", "SELLS"),
               ("YOUR PRODUCT", "ALIVE")],
        payoff=("ONE MORE", "TIME"),
        cards=[("the hands", 2.0), ("the glow", 6.5), ("in context", 11.0)],
        labels=["specs", "b-roll ready", "step 01", "step 02"],
        sig_pill="SPEC SHEET V2", stickers=["star", "arrow", "play", "bolt", "rocket", "headphones"],
        insert="surreal 3D dream world, smartphone product shot levitating over a clean white pedestal island with cobalt blue light beams and soft geometric clouds, studio palette, vertical, cinematic render, no text, no watermark",
    ),
    "branding_1": dict(
        cat="BRANDING", family="F2",
        accent=(212, 175, 55), secondary=(230, 230, 235), ink=(20, 18, 12),
        type_fill="accent", extrude="accent_dark", halftone="accent", sticker="accent",
        card_border=(212, 175, 55), pill_bg=(212, 175, 55),
        bg_tint=(255, 240, 200, 12),
        types=[("SKIP", "THIS SHOT"), ("SILHOUETTES", "SELL SCALE"), ("OWN THE", "SKYLINE"),
               ("SHOOT INTO", "THE SUN")],
        payoff=("ONE MORE", "TIME"),
        cards=[("the silhouette", 1.5), ("the sun", 5.5), ("the skyline", 10.0)],
        labels=["AURUM & CO", "backlight is free", "step 01", "step 02"],
        sig_pill="GOLD COUNTER x12", stickers=["star", "arrow", "rocket", "clapper", "play", "bolt"],
        insert="surreal 3D dream world, golden silhouette statue on a marble rooftop island above a charcoal city, warm gold backlight rays, gold and charcoal palette, halftone texture sky, vertical, cinematic render, no text, no watermark",
    ),
    "nature_1": dict(
        cat="NATURE", family="F3",
        accent=(224, 196, 120), secondary=(180, 220, 170), ink=(12, 24, 16),
        type_fill="white", extrude="accent_dark", halftone="accent", sticker="accent",
        card_border=(224, 196, 120), pill_bg=(224, 196, 120),
        bg_tint=(230, 240, 220, 12),
        types=[("WATCH", "WATER"), ("WAVES SET", "THE TEMPO"), ("END ON THE", "HORIZON"),
               ("BREATHE", "OUT")],
        payoff=("RUN IT", "BACK"),
        cards=[("the water", 1.5), ("the wave", 5.5), ("the horizon", 9.5)],
        labels=["tide +0.4m", "slow cuts only", "step 01", "step 02"],
        sig_pill="TIDE TABLE +0.4M", stickers=["star", "arrow", "play", "rocket", "bolt", "headphones"],
        insert="surreal 3D dream world, giant wave curling over a floating forest island with golden pollen light beams, misty green tones, deep green and sand palette, vertical, cinematic render, no text, no watermark",
    ),
    "cars_2": dict(
        cat="CARS", family="F3",
        accent=(0, 229, 255), secondary=(120, 190, 255), ink=(8, 12, 24),
        type_fill="accent", extrude="accent_dark", halftone="accent", sticker="accent",
        card_border=(0, 229, 255), pill_bg=(0, 229, 255),
        bg_tint=(200, 230, 255, 10),
        types=[("LUXURY", "SHOTS"), ("LOCK", "THE FRAME"), ("STATIC", "IS CINEMA"),
               ("LET IT", "BREATHE")],
        payoff=("REWIND", None),
        cards=[("the shot", 1.5), ("the frame", 5.5), ("the breath", 9.0)],
        labels=["0-60 3.1s", "warm light", "step 01", "step 02"],
        sig_pill="GEAR PILL N-60", stickers=["bolt", "arrow", "star", "play", "rocket", "clapper"],
        insert="surreal 3D dream world, midnight blue luxury sports car floating on a cyan light-line racetrack in the clouds, electric cyan rim light, halftone dot sky, vertical, cinematic render, no text, no watermark",
    ),
    "racing_1": dict(
        cat="RACING", family="F3",
        accent=(0, 229, 255), secondary=(255, 120, 60), ink=(8, 12, 24),
        type_fill="accent", extrude="accent_dark", halftone="accent", sticker="accent",
        card_border=(255, 120, 60), pill_bg=(255, 120, 60),
        bg_tint=(210, 225, 255, 10),
        types=[("PURE", "PACE"), ("CUT ON", "MOTION"), ("PACE IS", "THE HOOK"),
               ("NEVER", "SLOW")],
        payoff=("REWIND", None),
        cards=[("cold open", 1.5), ("the hit", 5.5), ("the drop", 9.5)],
        labels=["LAP 04 P1", "14.0s", "step 01", "step 02"],
        sig_pill="RPM 12,400", stickers=["bolt", "rocket", "arrow", "star", "play", "clapper"],
        insert="surreal 3D dream world, race car cornering on a floating cyan neon circuit ribbon above clouds, orange light streaks and motion blur, night palette, vertical, cinematic render, no text, no watermark",
    ),
    "city_1": dict(
        cat="CITY", family="F3",
        accent=(255, 45, 170), secondary=(0, 230, 200), ink=(14, 6, 18),
        type_fill="accent", extrude="accent_dark", halftone="accent", sticker="accent",
        card_border=(255, 45, 170), pill_bg=(255, 45, 170),
        bg_tint=(255, 220, 240, 10),
        types=[("UP", "HERE"), ("NIGHT", "CIRCUITS"), ("SHOOT", "THE GRID"),
               ("TRAFFIC", "RIVERS")],
        payoff=("RUN IT", "BACK"),
        cards=[("the view", 1.5), ("the circuits", 5.5), ("the grid", 9.0)],
        labels=["GRID 07", "teal and amber", "step 01", "step 02"],
        sig_pill="ROOFTOP 51F", stickers=["star", "arrow", "bolt", "play", "headphones", "rocket"],
        insert="surreal 3D dream world, magenta and teal neon city floating on clouds with circuit-board streets glowing below, wet reflections, night palette, vertical, cinematic render, no text, no watermark",
    ),
    "fashion_1": dict(
        cat="FASHION", family="F3",
        accent=(255, 190, 205), secondary=(240, 240, 245), ink=(26, 16, 18),
        type_fill="accent", extrude="accent_dark", halftone="accent", sticker="accent",
        card_border=(255, 190, 205), pill_bg=(240, 240, 245),
        bg_tint=(255, 230, 236, 12),
        types=[("TOO", "FAST"), ("LET FABRIC", "MOVE"), ("TEXTURE IS", "THE STORY"),
               ("HOLD THE", "FRAME")],
        payoff=("ONE MORE", "TIME"),
        cards=[("the fabric", 1.5), ("the rack", 4.5), ("the texture", 7.5)],
        labels=["FW DROP", "neutral grade", "step 01", "step 02"],
        sig_pill="LOOKBOOK 12", stickers=["star", "arrow", "play", "bolt", "rocket", "headphones"],
        insert="surreal 3D dream world, elegant blush fabric ribbon flowing over a noir floating island, pearl silk clouds, studio soft light, blush and noir palette, vertical, cinematic render, no text, no watermark",
    ),
    "mindset_1": dict(
        cat="MINDSET", family="F3",
        accent=(230, 180, 110), secondary=(210, 210, 205), ink=(20, 20, 18),
        type_fill="accent", extrude="accent_dark", halftone="accent", sticker="accent",
        card_border=(230, 180, 110), pill_bg=(230, 180, 110),
        bg_tint=(240, 230, 215, 12),
        types=[("SLOW", "DOWN"), ("INHALE", "4-4-6"), ("STILLNESS IS", "THE EDIT"),
               ("START", "NOW")],
        payoff=("RUN IT", "BACK"),
        cards=[("the coast", 1.5), ("the breath", 5.5), ("the still", 9.5)],
        labels=["4-4-6 breath", "no hard cuts", "step 01", "step 02"],
        sig_pill="BREATH 4-4-6", stickers=["star", "arrow", "play", "rocket", "headphones", "bolt"],
        insert="surreal 3D dream world, calm foggy coast floating as a soft island with candle-amber sunrise glow and giant breathing light orbs, film grain mood, amber palette, vertical, cinematic render, no text, no watermark",
    ),
    "music_1": dict(
        cat="MUSIC", family="F3",
        accent=(170, 90, 255), secondary=(255, 170, 60), ink=(16, 8, 26),
        type_fill="accent", extrude="accent_dark", halftone="accent", sticker="accent",
        card_border=(170, 90, 255), pill_bg=(170, 90, 255),
        bg_tint=(240, 225, 255, 10),
        types=[("STEAL", "THE RIG"), ("BACKLIGHT", "FIRST"), ("RIDE THE", "DROP"),
               ("CROWD CUTS", "FREE")],
        payoff=("REWIND", None),
        cards=[("the rig", 1.5), ("the beat", 5.5), ("the drop", 10.0)],
        labels=["128 BPM", "cut on the beat", "step 01", "step 02"],
        sig_pill="128 BPM LIVE", stickers=["play", "star", "arrow", "headphones", "bolt", "rocket"],
        insert="surreal 3D dream world, concert stage floating on a purple cloud with giant amber waveform ribbons and crowd silhouettes below, stage light beams, purple and amber palette, vertical, cinematic render, no text, no watermark",
    ),
    "tech_1": dict(
        cat="TECH", family="F3",
        accent=(0, 255, 130), secondary=(180, 190, 200), ink=(6, 14, 10),
        type_fill="accent", extrude="accent_dark", halftone="accent", sticker="accent",
        card_border=(0, 255, 130), pill_bg=(0, 255, 130),
        bg_tint=(220, 255, 235, 8),
        types=[("THE", "DATA MAP"), ("NODES ARE", "CITIES"), ("FOLLOW", "THE FLOW"),
               ("THE INTERNET", "HAS A SHAPE")],
        payoff=("REWIND", None),
        cards=[("the map", 1.5), ("the nodes", 5.5), ("the flow", 9.0)],
        labels=["> ping 12ms", "grade in neon", "step 01", "step 02"],
        sig_pill="UPLINK 12ms", stickers=["bolt", "arrow", "play", "star", "rocket", "clapper"],
        insert="surreal 3D dream world, giant glowing green data map of the world hovering above a dark terminal cloud island, neon phosphor rivers connecting cities, green and dark palette, vertical, cinematic render, no text, no watermark",
    ),
    "travel_1": dict(
        cat="TRAVEL", family="F3",
        accent=(255, 170, 80), secondary=(255, 236, 210), ink=(30, 18, 12),
        type_fill="accent", extrude="accent_dark", halftone="accent", sticker="accent",
        card_border=(255, 170, 80), pill_bg=(255, 170, 80),
        bg_tint=(255, 235, 210, 14),
        types=[("BEFORE THEY", "PAVE IT"), ("EMPTY", "ROAD"), ("GO", "NOW"),
               ("LAST RIDE", "RAW")],
        payoff=("RUN IT", "BACK"),
        cards=[("the road", 1.5), ("the turn", 5.0), ("the raw", 8.5)],
        labels=["passport stamp", "engine metronome", "step 01", "step 02"],
        sig_pill="ROUTE 1 OPEN", stickers=["rocket", "star", "arrow", "play", "bolt", "headphones"],
        insert="surreal 3D dream world, coastal road at sunset looping over a floating warm island with a vintage suitcase and orange sky clouds, sunset palette, vertical, cinematic render, no text, no watermark",
    ),
}


def anchor_map():
    probe = json.load(open("/home/z/my-project/p8work/anchor_probe.json"))
    out = {}
    for vid, s in STYLES.items():
        m = probe.get(vid, {})
        if s["family"] in ("F1", "F2"):
            out[vid] = {
                "family": s["family"], "anchor": "masked-subject" if s["family"] == "F1" else "masked-object",
                "probe": {k: m.get(k) for k in ("fg_frac", "iou", "bw", "bh")},
                "matte": True, "matte_fps": 30,
            }
        else:
            out[vid] = {
                "family": s["family"], "anchor": "insert-world-scrim",
                "probe": {k: m.get(k) for k in ("fg_frac", "iou")},
                "matte": False, "matte_fps": None,
            }
    # podcast_1 override: probe borderline (bw 0.28) but stable speaker silhouette
    if probe.get("podcast_1", {}).get("iou", 0) >= 0.5:
        out["podcast_1"]["probe"]["override"] = "bw 0.28<0.30 accepted: stable speaker silhouette"
    return out


if __name__ == "__main__":
    out = "/home/z/my-project/p8work/style16.json"
    json.dump({v: {k: w for k, w in s.items() if k != "insert"}
               for v, s in STYLES.items()}, open(out, "w"), indent=1)
    am = anchor_map()
    for v, a in am.items():
        print(v, a["family"], a["anchor"], a["probe"])
    print("styles ->", out)
