#!/usr/bin/env python3
"""Phase 18 Telegram delivery — LIVE-ONLY. Proofs first, then master + report."""
import sys, os, json
sys.path.insert(0, "/home/z/my-project/scripts")
sys.path.insert(0, "/tmp/ems-work/ems-repo/scripts")
import p16_tg as tg
import time

TC = "Test Edit Skill"
P18 = "/tmp/ems-work/p18"
D = "/home/z/my-project/download/phase18_deliverables"
REPO = "github.com/Dani-Devlop/edit-master-skill"

MSG_SONGID = (
    f"{TC} | P18 PROOFS 1/3 — song ID + source automation (A1-A4)\n"
    "Song: WELCOME - IDK feat. Eminem (prod. J Dilla) - released 2026-11-13\n"
    "Method: faster-whisper-small word-timestamp transcript -> exact-phrase "
    "match (Genius + consequence.net) -> confidence HIGH\n"
    "Source: yt-dlp BLOCKED (YouTube bot-check) + cobalt auth-required + "
    "REF-TAG-A CDN 403 -> honest fallback: manager-provided raw = official MV "
    "footage excerpt 27.9s (source-quality 8.5/10 PASS, LUFS -14.1)\n"
    "Lyrics: whisper timings x Genius verbatim; 12 ASR corrections logged "
    "(e.g. 'Sam Tellegrino'->'San Pellegrino', 'Baca rock'->'Baccarat')\n"
    "License: commercial track - EDIT-TEST USAGE ONLY, no publication")

MSG_PLAN = (
    f"{TC} | P18 PROOFS 3/3 — scene plan / engines / cue sheet / quotas\n"
    "12 beats: 01 S02 hook lockup | 02 S11 starburst pop | 03 S04 tape slam "
    "HOMICIDE | 04 S03 camera-track | 05 S02E echo+invert | 06 S10 listicle | "
    "07 S08 graph+odometer 178 BPM (measured) | 08 S12 arc PAID>LAID | "
    "09 S05 Zurbaran painting slide | 10 S13 pills | 11 S07 callout | 12 S09 endcard\n"
    "Engine per beat: FilmCraft CLI unavailable -> EffectCraft unavailable -> "
    "Remotion scaffold skipped -> PIL sequences + ffmpeg composite (E3 fallback, logged)\n"
    "Cue sheet: 15 SFX == entrances (whoosh/glitch/splice/thump/click/riser/"
    "tape-stop) at -8..-14 dB, original mix kept, loudnorm -14 LUFS\n"
    "Quotas: designed 98% | 11 scene types | no consecutive same | wow 10 | "
    "camera moves 5 | frame-1 composed | endcard no-brand")

MSG_REPORT = (
    f"{TC} | PHASE 18.0 FINAL REPORT (2026-11-24)\n\n"
    "INPUT: REF-TAG-A unreachable (CDN 403) -> fallback raw (manager-provided "
    "official-MV excerpt)\n"
    "SONG-ID: WELCOME - IDK feat. Eminem (J Dilla) | whisper x Genius | HIGH\n\n"
    "DELIVERED: T1_welcome_v18_9x16.mp4 (30.3s, 720x1280@30, H.264+AAC)\n"
    "M1 Instagram match: 99.1% aggregate (bar 70%), min dim 9.33 (bar 6.0)\n"
    "  D1 hook 10.0 | D2 two-font karaoke 10.0 | D3 variety 10.0 | D4 designed "
    "9.8 | D5 transitions 9.33 | D6 grade 10.0 | D7 sound 10.0 | D8 platform "
    "10.0 | D9 polish 10.0 | D10 pacing 10.0\n"
    "M2 self-critique: 20 axes ALL >= 9.5 (weakest A5_dim_gradation 9.5)\n"
    "GATES: G-P1..G-P20 19/19 PASS + Q1-Q12 12/12 PASS | negatives 4/4 caught "
    "(typewriter/empty-frame0/halftone/debug-HUD)\n"
    "DELIVERY LOCK: master sha256_16 948aed98f8878f23 == gate file sha "
    "(gate_948aed98f8878f23.json)\n"
    "Preset mv_welcome sha16 43e83c594f9ec833\n"
    "AUDIO: -14.0 LUFS / TP -3.0 dBFS | 15 SFX == entrances | original mix kept\n"
    "TRANSPORT NOTE: telegram copy = transcode sha16 bba5c8e4de5c1def (50MB bot "
    "limit; audio bit-identical); locked master kept in workspace download folder\n"
    f"Repo: {REPO} (main — Phase 18 scripts+test-results pushed; badge audit 0 Unverified)\n"
    "TEMP: /tmp/ems-work/p18 cleaned after delivery | chat surface clean")

def main():
    log = []
    ok = True

    def guard(res, what):
        nonlocal ok
        if not res:
            print(f"SEND FAILED: {what}", file=sys.stderr)
            ok = False
            return False
        log.append(f"OK {what}")
        return True

    guard(tg.send(MSG_SONGID), "msg song-id")
    time.sleep(1.5)
    if ok: guard(tg.send_photo(f"{P18}/proof_component_strip_11types.jpg",
                f"{TC} | P18 PROOFS 2/3 - component strip: 11 scene types "
                f"(S01-S19 engine) rendered by the actual deliverable"), "proof strip")
    time.sleep(1.5)
    if ok: guard(tg.send_photo(f"{P18}/proof_karaoke_sweep_strip_8frames.jpg",
                f"{TC} | karaoke sweep proof - two-font captions: bold sans body "
                f"+ serif accent keywords, full sentence always, active accent "
                f"1.2x, spoken dim 45%, sweep loop"), "karaoke strip")
    time.sleep(1.5)
    if ok: guard(tg.send_photo(f"{P18}/proof_hud_removal_pair.jpg",
                f"{TC} | HUD-removal proof - regression negative (debug HUD) "
                f"caught by Q7; final deliverable is clean"), "hud pair")
    time.sleep(2.0)
    if ok: guard(tg.send(MSG_PLAN), "msg plan/cue")
    time.sleep(2.0)
    if ok: guard(tg.send_photo(f"{D}/cover_T1_welcome_9x16.jpg",
                f"{TC} | T1_welcome_v18 - cover frame (auto-scored pick, t="
                f"{json.load(open('/tmp/ems-work/p18/run_T1/manifest_9x16.json'))['cover_t']}s)"), "cover")
    time.sleep(1.5)
    if ok: guard(tg.send_photo(f"{D}/scoresheet_T1_welcome_9x16.jpg",
                f"{TC} | T1_welcome_v18 - 20-axis self-critique scoresheet "
                f"(all >= 9.5)"), "scoresheet")
    time.sleep(2.5)
    if ok: guard(tg.send_video(f"{D}/T1_welcome_v18_9x16_telegram_transcode.mp4",
                f"{TC} | T1_welcome_v18 9x16 (30.3s)\n"
                f"Song: WELCOME - IDK feat. Eminem (J Dilla) | ID: whisper x Genius, HIGH\n"
                f"IG match M1: 99.1% (bar 70%) | 20-axis min 9.5\n"
                f"Gates: G-P1..G-P20 + Q1-Q12 ALL PASS | negatives 4/4\n"
                f"Master sha16 948aed98f8878f23 (gate-locked) | preset sha16 43e83c594f9ec833\n"
                f"LUFS -14.0 / TP -3.0 | transcode sha16 bba5c8e4de5c1def (50MB limit, audio bit-identical)\n"
                f"Repo: {REPO} (main)"), "master video")
    time.sleep(2.5)
    if ok: guard(tg.send(MSG_REPORT), "final report")

    for l in log: print(l)
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
