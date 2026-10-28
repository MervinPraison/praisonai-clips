import pytest

from praisonai_shorts_studio.kdenlive import frame_mappings, seconds_to_frame
from praisonai_shorts_studio.models import EDL, Mapping


def test_frame_rounding_policy_and_nonadjacent_cuts():
    assert seconds_to_frame(.05)==2  # explicit half-up policy, not binary float tie behavior
    edit=EDL(title='Cuts',rationale='Test',mappings=[
        Mapping(source_start=.012,source_end=5.012,output_start=0),
        Mapping(source_start=10.012,source_end=15.012,output_start=5)])
    frames=frame_mappings(edit)
    assert [(m['source_in'],m['source_out'],m['output_start']) for m in frames]==[(0,150,0),(300,450,150)]
    assert all(abs(m['rounding_start_seconds'])<=1/60 for m in frames)
    assert all(abs(m['rounding_end_seconds'])<=1/60 for m in frames)


def test_subframe_cut_cannot_be_exported_as_empty_clip():
    edit=EDL(title='Tiny',rationale='Test',mappings=[Mapping(source_start=.001,source_end=.002,output_start=0)])
    with pytest.raises(ValueError,match='one project frame'):
        frame_mappings(edit)
