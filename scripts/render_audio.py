#!/usr/bin/env python3
"""Render deterministic, iPhone-friendly MP3 examples for released Niblet lessons."""
from __future__ import annotations

import math
import random
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

RATE = 44_100
BPM = 100
BEAT = 60 / BPM
ROOT = Path(__file__).parents[1] / "content" / "lessons"
random.seed(17)


def render(path: Path, duration: float, events: list[tuple[str, float, float, float]]) -> None:
    samples = [0.0] * int((duration + 0.15) * RATE)

    def add_tone(start: float, freq: float, length: float, amp: float, kind: str = "tone") -> None:
        begin = int(start * RATE)
        end = min(len(samples), begin + int(length * RATE))
        phase = 0.0
        for i in range(begin, end):
            x = (i - begin) / RATE
            if kind == "kick":
                f = max(42.0, freq * math.exp(-x * 16))
                phase += 2 * math.pi * f / RATE
                env = math.exp(-x * 13)
                value = math.sin(phase) * env
            elif kind == "snare":
                env = math.exp(-x * 17)
                value = (random.random() * 2 - 1) * env * 0.78 + math.sin(2 * math.pi * 180 * x) * env * 0.22
            elif kind == "hat":
                env = math.exp(-x * 55)
                value = (random.random() * 2 - 1) * env
            elif kind == "click":
                env = math.exp(-x * 45)
                value = math.sin(2 * math.pi * freq * x) * env
            elif kind == "held":
                attack = min(1.0, x / 0.035)
                release = min(1.0, max(0.0, (length - x) / 0.09))
                env = attack * release * 0.75
                value = (math.sin(2 * math.pi * freq * x) + 0.28 * math.sin(2 * math.pi * freq * 2 * x)) * env
            else:
                env = math.exp(-x * 5.2)
                value = (math.sin(2 * math.pi * freq * x) + 0.32 * math.sin(2 * math.pi * freq * 2 * x)) * env
            samples[i] += amp * value

    for kind, start, value, amp in events:
        lengths = {"kick": 0.22, "snare": 0.18, "hat": 0.075, "click": 0.12, "tone": 0.32}
        if kind == "held":
            add_tone(start, value, amp, 0.28, "held")
        else:
            add_tone(start, value, lengths.get(kind, 0.3), amp, kind)

    peak = max(max(samples), -min(samples), 0.001)
    gain = 0.88 / peak
    pcm = b"".join(struct.pack("<h", max(-32767, min(32767, int(s * gain * 32767)))) for s in samples)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav_path = Path(tmp) / "render.wav"
        with wave.open(str(wav_path), "wb") as out:
            out.setnchannels(1)
            out.setsampwidth(2)
            out.setframerate(RATE)
            out.writeframes(pcm)
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav_path), "-codec:a", "libmp3lame", "-q:a", "4", str(path)],
            check=True,
        )


def pulse_track(beats: int, meter: int, subdivision: int = 1) -> list[tuple[str, float, float, float]]:
    events = []
    for i in range(beats * subdivision):
        t = i * BEAT / subdivision
        if i % subdivision == 0:
            beat_index = i // subdivision
            if beat_index % meter == 0:
                events += [("kick", t, 125, 0.68), ("click", t, 1100, 0.32)]
            else:
                events.append(("click", t, 820, 0.24))
        else:
            events.append(("hat", t, 0, 0.12))
    return events


def groove(bars: int = 2) -> list[tuple[str, float, float, float]]:
    events = pulse_track(4 * bars, 4, 2)
    for beat in range(4 * bars):
        t = beat * BEAT
        if beat % 4 in (0, 2): events.append(("kick", t, 115, 0.66))
        if beat % 4 in (1, 3): events.append(("snare", t, 0, 0.48))
    return events


def main() -> None:
    jobs: list[tuple[Path, float, list[tuple[str, float, float, float]]]] = []
    # Meter
    jobs.append((ROOT/"001-beat-meter/assets/meter-4-4.mp3", 8*BEAT, pulse_track(8,4)))
    jobs.append((ROOT/"001-beat-meter/assets/meter-3-4.mp3", 6*BEAT, pulse_track(6,3)))
    # Duration
    base=pulse_track(4,4)
    jobs.append((ROOT/"002-duration/assets/duration-held.mp3",4*BEAT,base+[("held",0,220,4*BEAT-.05)]))
    jobs.append((ROOT/"002-duration/assets/duration-attacks.mp3",4*BEAT,base+[("tone",i*BEAT,220,0.45) for i in range(4)]))
    # On/off beats
    for name,offset in (("onbeats",0),("offbeats",BEAT/2)):
        events=pulse_track(8,4,2)+[("tone",i*BEAT+offset,330,0.42) for i in range(8) if i*BEAT+offset<8*BEAT]
        jobs.append((ROOT/f"003-onbeats-offbeats/assets/{name}.mp3",8*BEAT,events))
    # Sixteenth hook
    pattern=[0,3,5,8,10,13]
    events=pulse_track(8,4,4)
    for bar in range(2):
        events += [("tone",(bar*16+p)*BEAT/4,[294,330,392,440][p%4],0.4) for p in pattern]
    jobs.append((ROOT/"004-sixteenth-grid/assets/sixteenth-hook.mp3",8*BEAT,events))
    # Syncopation A/B
    straight=groove()+[("tone",i*BEAT,392 if i%2==0 else 330,0.43) for i in range(8)]
    sync=groove()+[("tone",(i+.5)*BEAT,392 if i%2==0 else 330,0.43) for i in range(8)]
    jobs.append((ROOT/"005-syncopation/assets/straight.mp3",8*BEAT,straight))
    jobs.append((ROOT/"005-syncopation/assets/syncopated.mp3",8*BEAT,sync))
    # Backbeat
    jobs.append((ROOT/"006-backbeat/assets/backbeat.mp3",8*BEAT,groove()+[("tone",(1.5+b*4)*BEAT,294,0.38) for b in range(2)]))
    # Eighths/triplets
    eighth_events=pulse_track(8,4)+[("tone",i*BEAT/2,370,0.34) for i in range(16)]
    triplet_events=pulse_track(8,4)+[("tone",i*BEAT/3,370,0.31) for i in range(24)]
    jobs.append((ROOT/"007-triplets/assets/eighths.mp3",8*BEAT,eighth_events))
    jobs.append((ROOT/"007-triplets/assets/triplets.mp3",8*BEAT,triplet_events))
    # Swing
    straight_events=pulse_track(8,4)+[("tone",(beat+off)*BEAT,330 if off==0 else 440,0.36) for beat in range(8) for off in (0,.5)]
    swing_events=pulse_track(8,4)+[("tone",(beat+off)*BEAT,330 if off==0 else 440,0.36) for beat in range(8) for off in (0,2/3)]
    jobs.append((ROOT/"008-swing/assets/straight-eighths.mp3",8*BEAT,straight_events))
    jobs.append((ROOT/"008-swing/assets/swung-eighths.mp3",8*BEAT,swing_events))

    for path,duration,events in jobs:
        render(path,duration,events)
        print(path.relative_to(ROOT), path.stat().st_size)


if __name__ == "__main__":
    main()
