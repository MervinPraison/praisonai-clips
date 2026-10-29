"""Compatibility import for the packaged native Kdenlive client."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from praisonai_shorts_studio.live.kdenlive import LiveClient

__all__ = ['LiveClient']
