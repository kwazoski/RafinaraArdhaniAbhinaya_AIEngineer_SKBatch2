import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def cv_text():
    return (ROOT / 'data' / 'cvs' / 'cv_01_rina_partial_dates.txt').read_text(encoding='utf-8')


@pytest.fixture
def base_response():
    path = ROOT / 'data' / 'mock_llm_responses' / 'cv_01_rina_partial_dates.json'
    return json.loads(path.read_text(encoding='utf-8'))
