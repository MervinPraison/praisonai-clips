import json

import pytest

from praisonai_shorts_studio.captions import ass_escape, clock, export, map_words
from praisonai_shorts_studio.models import Candidate, EDL, Mapping, Word
from praisonai_shorts_studio.pipeline import candidate_edl, default_config
from praisonai_shorts_studio.store import Cancelled, Store


def test_mapping_across_nonadjacent_cuts():
    words = [Word(word="First.", start=11, end=12), Word(word="Removed.", start=20, end=21),
             Word(word="Second.", start=31, end=32)]
    edl = EDL(title="Two cuts", rationale="Test", mappings=[
        Mapping(source_start=10, source_end=15, output_start=0),
        Mapping(source_start=30, source_end=35, output_start=5)])
    mapped = map_words(words, edl)
    assert [(w['word'], w['start'], w['end'], w['source_start']) for w in mapped] == [
        ('First.', 1, 2, 11), ('Second.', 6, 7, 31)]


def test_partial_word_not_invented():
    edl = EDL(title="T", rationale="R", mappings=[Mapping(source_start=1, source_end=3, output_start=0)])
    assert map_words([Word(word="cut", start=.9, end=1.1)], edl) == []


def test_output_timeline_must_be_contiguous():
    with pytest.raises(ValueError, match="contiguous"):
        EDL(title="T", rationale="R", mappings=[Mapping(source_start=1, source_end=3, output_start=2)])


def test_invalid_or_fabricated_duration_rejected():
    with pytest.raises(ValueError):
        Word(word="hello", start=2, end=1)
    with pytest.raises(ValueError):
        Word(word="hello", start=float('nan'), end=3)


def test_sentence_and_duration_validation():
    words = [Word(word="Hello", start=1, end=2), Word(word="world.", start=2.1, end=3),
             Word(word="Next.", start=4, end=5)]
    config = default_config(min_duration=1, max_duration=10)
    c = Candidate(start_word=1, end_word=2, title="T", rationale="R", score=.9)
    with pytest.raises(ValueError, match="inside a sentence"):
        candidate_edl(c, words, config, 10)
    c.start_word, c.end_word = 0, 0
    with pytest.raises(ValueError, match="inside a sentence"):
        candidate_edl(c, words, config, 10)
    c.end_word = 1
    edl = candidate_edl(c, words, config, 10)
    assert edl.mappings[0].source_start == pytest.approx(.88)
    assert edl.mappings[0].source_end == pytest.approx(3.15)


def test_caption_clocks_carry_rounding():
    assert clock(59.9996) == '00:01:00,000'
    assert clock(3599.999, ass=True) == '1:00:00.00'
    assert ass_escape(r'{\pos(0,0)}') == '｛＼pos(0,0)｝'


def test_exports_retain_exact_word_timings(tmp_path):
    words = [Word(word='Hello', start=10.123, end=10.456), Word(word='world.', start=10.9, end=11.25)]
    edl = EDL(title='T', rationale='R', mappings=[Mapping(source_start=10, source_end=12, output_start=0)])
    mapped = export(tmp_path, words, edl)
    assert mapped[0]['start'] == pytest.approx(.123)
    assert mapped[0]['end'] == pytest.approx(.456)
    assert '00:00:00,123 --> 00:00:01,250' in (tmp_path/'captions.srt').read_text()
    assert '{\\c&H0000FFFF&}' in (tmp_path/'captions.ass').read_text()
    assert json.loads((tmp_path/'words.json').read_text())[1]['source_start'] == 10.9


def test_cancel_and_resume_reuse_completed_api_cache(tmp_path):
    store = Store(tmp_path/'data')
    source = tmp_path/'source'
    source.write_bytes(b'video fixture')
    job = store.create(source, {})
    calls = []
    assert store.cache(job, 'test', {'v':1}, lambda: calls.append(1) or {'words':[1]}) == {'words':[1]}
    store.update(job, cancel=1)
    with pytest.raises(Cancelled):
        store.cache(job, 'test', {'v':1}, lambda: calls.append(2))
    store.update(job, cancel=0)
    assert store.cache(job, 'test', {'v':1}, lambda: calls.append(3)) == {'words':[1]}
    assert calls == [1]
    store.cache(job, 'test', {'v':2}, lambda: calls.append(4) or {})
    assert calls == [1,4]


def test_zero_duration_provider_word_disqualifies_candidate():
    words=[Word(word='Measured',start=1,end=2),Word(word='point.',start=2,end=2)]
    with pytest.raises(ValueError,match='positive duration'):
        candidate_edl(Candidate(start_word=0,end_word=1,title='T',rationale='R',score=1),
                      words,default_config(min_duration=1),10)


def test_punctuation_restoration_never_changes_measured_times():
    from praisonai_shorts_studio.alignment import punctuate
    words=[{'word':'Hello','start':1.234,'end':1.5},{'word':'world','start':1.6,'end':2.1}]
    result=punctuate(words,'Hello, world.')
    assert [w['word'] for w in result]==['Hello,','world.']
    assert [(w['start'],w['end']) for w in result]==[(1.234,1.5),(1.6,2.1)]
    assert words[1]['word']=='world'
