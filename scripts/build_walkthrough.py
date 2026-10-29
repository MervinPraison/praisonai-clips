"""Assemble a captioned walkthrough from a real browser recording and public screenshots.

Capture an empty local app with Playwright (1440x1000); play the public example,
download its bundle, and expand the comparison. No personal media or API calls.
Run: python scripts/build_walkthrough.py /path/to/recording.webm
Requires FFmpeg with drawtext and H.264 support. Output contains no audio.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'docs/assets/challenge'


def main():
    recording = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix='clips-walkthrough-') as temporary:
        work = Path(temporary)
        segments = [
            ('card', 7, 'PRAISONAI CLIPS', 'One recording. A useful moment to share.', 'Built entirely using OpenAI Codex / under Mervin Praison\'s direction'),
            ('before-onboarding.png', 8, '01 / THE EVERYDAY TASK', 'Turn recordings into captioned clips you can review.', 'Before: an explanation-first screen, with the upload in a sidebar.'),
            ('recording', 31, '02 / THE IMPROVEMENT', 'See an output before configuring API access.', 'Actual app recording / generated example / scripted captions / no AI analysis'),
            ('card', 12, '03 / THE CHECK', '44 tests passed. 4 optional runtime tests skipped.', 'macOS check: rendering, repair, resume, SDK guards and onboarding.\nBrowser check: sample playback and ZIP download. No paid API calls.'),
            ('card', 8, 'A SMALL WIN YOU CAN INSPECT', 'See it. Check it. Choose what to share.', 'clips.praison.ai / built-with-codex\nLocal app / source timings / accepted clips and uncertain drafts'),
        ]
        outputs = []
        for index, (source, duration, heading, title, footer) in enumerate(segments):
            labels = []
            for name, value in [('heading', heading), ('title', title), ('footer', footer)]:
                file = work / f'{index}-{name}.txt'
                file.write_text(value)
                labels.append(file)
            if source == 'card':
                inputs = ['-f', 'lavfi', '-i', f'color=c=0xf5f2e9:s=1440x1160:r=25:d={duration}']
                layout = 'null'
                positions = [(26, 130), (42, 360), (25, 610)]
            else:
                inputs = (['-ss', '1', '-i', str(recording)] if source == 'recording' else ['-loop', '1', '-i', str(DEST / source)])
                layout = 'scale=1440:1000:force_original_aspect_ratio=decrease,pad=1440:1000:(ow-iw)/2:(oh-ih)/2:color=0xf5f2e9,pad=1440:1160:0:160:color=0xf5f2e9'
                positions = [(20, 16), (30, 48), (18, 102)]
            filters = [layout]
            for file, (size, y) in zip(labels, positions):
                filters.append(f"drawtext=textfile='{file}':font='DejaVu Sans':fontsize={size}:fontcolor=0x20211e:x=(w-text_w)/2:y={y}:line_spacing=16")
            output = work / f'{index}.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-t', str(duration), '-vf', ','.join(filters), '-an', '-r', '25', '-c:v', 'libx264', '-threads', '2', '-preset', 'fast', '-crf', '21', '-pix_fmt', 'yuv420p', str(output)], check=True)
            outputs.append(output)
        listing = work / 'segments.txt'
        listing.write_text(''.join(f"file '{file}'\n" for file in outputs))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(listing), '-c', 'copy', '-movflags', '+faststart', str(DEST / 'walkthrough.mp4')], check=True)


if __name__ == '__main__':
    main()
