"""Conservative quiet-pause detection and frame-aligned source mappings."""
import math
import re
import subprocess

from .models import Mapping


def remove_quiet_pauses(source, cut, words, check, *, threshold_db=-35, min_silence=0.6, padding=0.15):
    """Return kept ranges; never cut inside a measured word or its safety margin."""
    check()
    duration = cut.source_end - cut.source_start
    result = subprocess.run(['ffmpeg', '-hide_banner', '-nostdin', '-ss', str(cut.source_start),
        '-t', str(duration), '-i', str(source), '-af',
        f'silencedetect=noise={threshold_db}dB:d={min_silence}', '-vn', '-f', 'null', '-'],
        capture_output=True, text=True, timeout=120)
    check()
    if result.returncode:
        raise RuntimeError('Could not analyse quiet pauses: ' + result.stderr[-1000:])
    starts = [float(x) for x in re.findall(r'silence_start: ([0-9.]+)', result.stderr)]
    ends = [float(x) for x in re.findall(r'silence_end: ([0-9.]+)', result.stderr)]
    if len(starts) > len(ends):
        ends.append(duration)
    removals = []
    for start, end in zip(starts, ends):
        intervals = [(cut.source_start + start + padding, cut.source_start + end - padding)]
        for word in words:
            protected_start, protected_end = word.start - padding, word.end + padding
            next_intervals = []
            for a, b in intervals:
                if protected_end <= a or protected_start >= b:
                    next_intervals.append((a, b))
                else:
                    next_intervals.extend([(a, min(b, protected_start)), (max(a, protected_end), b)])
            intervals = [(a, b) for a, b in next_intervals if b > a]
        for a, b in intervals:
            a, b = math.ceil(a * 30) / 30, math.floor(b * 30) / 30
            if b - a >= 0.2 and a > cut.source_start and b < cut.source_end:
                removals.append((a, b))
    cursor, output, mappings = cut.source_start, 0.0, []
    for a, b in sorted(removals):
        if a <= cursor:
            continue
        mappings.append(Mapping(source_start=cursor, source_end=a, output_start=output))
        output += a - cursor
        cursor = b
    mappings.append(Mapping(source_start=cursor, source_end=cut.source_end, output_start=output))
    return mappings
