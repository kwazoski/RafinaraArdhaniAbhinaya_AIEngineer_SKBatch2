"""Menghasilkan output asli pipeline untuk setiap CV di golden set ke folder examples/.
Jalankan dari root repo: python evals/generate_sample_output.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

from cv_screening import MockLLM, run_pipeline  # noqa: E402

golden = json.loads((ROOT / 'data' / 'golden.json').read_text(encoding='utf-8'))
out_dir = ROOT / 'examples'
out_dir.mkdir(exist_ok=True)

for case in golden['cases']:
    cid = case['id']
    cv = (ROOT / 'data' / 'cvs' / f'{cid}.txt').read_text(encoding='utf-8')
    llm = MockLLM(ROOT / 'data' / 'mock_llm_responses' / f'{cid}.json')
    result = run_pipeline(cv, llm=llm, as_of=golden['as_of'])
    (out_dir / f'{cid}.output.json').write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('ditulis:', out_dir / f'{cid}.output.json')
