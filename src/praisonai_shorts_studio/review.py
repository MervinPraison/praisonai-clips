"""Review visible edits against source references; preserve every review attempt."""
import math

from . import captions, media
from .models import Review
from .store import digest_file


def inspect_render(source, video, folder, edl, mapped, backend, cache, check):
    technical = media.technical_review(video, edl.duration, check)
    times = sorted({.2, edl.duration - .2,
                    *(float(t) for t in range(1, math.ceil(edl.duration), 2)),
                    *((w['start'] + w['end'])/2 for w in mapped[::8])})
    fingerprint = digest_file(video)
    frames = [(t, media.frame(video, folder/'review-v2-frames'/fingerprint[:16]/f'{t:.6f}.jpg', t, check),
               'RENDERED OUTPUT') for t in times]
    measured_groups = [{'start': g[0]['start'], 'end': g[-1]['end'],
                        'text': ' '.join(w['word'] for w in g)} for g in captions.groups(mapped)]
    results = []
    for offset in range(0, len(frames), 8):
        batch = frames[offset:offset + 8]
        references = []
        for t, _, _ in batch[::3]:
            mapping = next((m for m in edl.mappings if m.output_start <= t < m.output_end), edl.mappings[-1])
            source_t = mapping.source_start + max(0, t - mapping.output_start)
            references.append((source_t, media.frame(source, folder/'source-reference-frames'/f'{source_t:.6f}.jpg',
                                                    source_t, check), 'ORIGINAL SOURCE REFERENCE'))
        evidence = {'review_protocol': 2, 'edl': edl.model_dump(), 'words': mapped,
                    'caption_groups': measured_groups, 'technical_defects': technical,
                    'picture_policy': 'mode=fit retains the full original picture, letterboxed with black padding; no crop is applied',
                    'reference_policy': 'Source-reference frames show original design. Only identify defects introduced in output.',
                    'review_scope': 'Full decode and timestamps; sampled visual evidence; no auditory verification'}
        raw = cache(f'review-v2-{offset:03}', {'evidence': evidence, 'times': [t for t,_,_ in batch],
                    'video_sha256': fingerprint}, lambda: backend.review(batch + references, evidence))
        results.append(Review.model_validate(raw))
    accepted = not technical and all(r.accepted and r.confidence >= .85 and not r.defects for r in results)
    return {'accepted': accepted, 'protocol': 2, 'technical_defects': technical,
            'visual_reviews': [r.model_dump() for r in results],
            'review_scope': 'Full decode and timestamp checks; sampled visual review against original source; no auditory model review'}
