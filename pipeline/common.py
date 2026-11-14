# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.
"""Shared paths and Earth Engine setup."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA, RAW = ROOT / 'data', ROOT / 'raw'
SITE_DATA, SITE_IMG = ROOT / 'docs' / 'data', ROOT / 'docs' / 'assets' / 'img'
EE_PROJECT = 'linear-stock-448205-t1'
YEARS = (2015, 2024)   # climate averaging period for MODIS / GPM


def ee_init():
    import ee
    ee.Initialize(project=EE_PROJECT)
    return ee
