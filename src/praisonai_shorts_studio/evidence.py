"""Source-time audio and analysis evidence for the local review interface."""
from __future__ import annotations

from array import array
import math
import subprocess
import sys
from pathlib import Path


def waveform(path: Path, start: float, end: float, *, sample_rate: int = 8000):
    """Return 20 ms peak envelopes from a bounded source interval, in linear amplitude."""
    if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end and end - start <= 30):
        raise ValueError("Choose a source interval of at most 30 seconds")
    proc = subprocess.run([
        'ffmpeg', '-v', 'error', '-nostdin', '-ss', str(start), '-i', str(path),
        '-t', str(end-start), '-map', '0:a:0', '-ac', '1', '-ar', str(sample_rate),
        '-f', 's16le', 'pipe:1',
    ], capture_output=True, timeout=60)
    if proc.returncode:
        raise RuntimeError('Could not read audio: ' + proc.stderr.decode(errors='replace')[-500:])
    samples = array('h')
    samples.frombytes(proc.stdout[:len(proc.stdout) // 2 * 2])
    if sys.byteorder != 'little':
        samples.byteswap()
    if not samples:
        raise ValueError('No audio samples found in this interval')
    bin_size = sample_rate // 50
    return [{'Source time (s)': round(start + i / sample_rate, 3),
             'Peak amplitude': max(abs(x) for x in samples[i:i+bin_size]) / 32768}
            for i in range(0, len(samples), bin_size)]


def in_window(words, scenes, start, end):
    """Keep words intersecting the interval and point observations within it."""
    return ([w for w in words if w['end'] >= start and w['start'] < end],
            [s for s in scenes if start <= s['time'] < end])
