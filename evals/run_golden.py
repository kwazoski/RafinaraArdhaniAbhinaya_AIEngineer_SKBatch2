"""Evaluasi pada golden set. Jalankan dari root repo: python evals/run_golden.py

Metrik per CV : kecocokan label, precision/recall/F1 skill, kecocokan set caveat, grounding rate.
Ringkasan     : label accuracy, rata-rata F1 skill, caveat exact-match, deteksi halusinasi.
Exit code 1 jika ada label atau caveat yang tidak sesuai golden (berguna untuk CI).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

from cv_screening import MockLLM, run_pipeline  # noqa: E402
from cv_screening.pipeline import norm  # noqa: E402


def prf(pred, gold):
    pred, gold = {norm(x) for x in pred}, {norm(x) for x in gold}
    tp = len(pred & gold)
    p = tp / len(pred) if pred else 0
    r = tp / len(gold) if gold else 0
    f1 = 2 * p * r / (p + r) if p + r else 0
    return p, r, f1


def evaluate():
    golden = json.loads((ROOT / 'data' / 'golden.json').read_text(encoding='utf-8'))
    rows = []
    for case in golden['cases']:
        cid = case['id']
        cv = (ROOT / 'data' / 'cvs' / f'{cid}.txt').read_text(encoding='utf-8')
        llm = MockLLM(ROOT / 'data' / 'mock_llm_responses' / f'{cid}.json')
        out = run_pipeline(cv, llm=llm, as_of=golden['as_of'])
        rec = out['recommendation']
        pred_skills = [s['name'] for s in out['profile']['skills']]
        p, r, f1 = prf(pred_skills, case['expected_skills'])
        got_caveats = {c['code'] for c in rec['caveats']}
        rows.append({
            'id': cid,
            'label_expected': case['expected_label'],
            'label_got': rec['label'],
            'label_ok': rec['label'] == case['expected_label'],
            'precision': p, 'recall': r, 'f1': f1,
            'caveats_ok': got_caveats == set(case['expected_caveats']),
            'caveats_got': sorted(got_caveats),
            'grounding': rec['grounding_rate'],
            'score': rec['match_score'],
        })
    return rows


def render(rows):
    n = len(rows)
    lines = ['| CV | Label (expected -> got) | Score | Skill P / R / F1 | Caveat set | Grounding |',
             '|---|---|---|---|---|---|']
    for x in rows:
        lines.append(
            f"| {x['id']} | {x['label_expected']} -> {x['label_got']} {'OK' if x['label_ok'] else 'MISMATCH'} "
            f"| {x['score']} | {x['precision']:.2f} / {x['recall']:.2f} / {x['f1']:.2f} "
            f"| {'OK' if x['caveats_ok'] else 'MISMATCH'} | {x['grounding']} |")
    halluc = [x for x in rows if x['grounding'] < 1.0]
    flagged = [x for x in halluc if 'ungrounded_extraction' in x['caveats_got']]
    lines += [
        '',
        f"- Label accuracy: {sum(x['label_ok'] for x in rows)}/{n}",
        f"- Mean skill F1: {sum(x['f1'] for x in rows) / n:.2f} "
        '(sengaja tidak 1.0: CV 05 berisi skill yang dikarang extractor)',
        f"- Caveat exact-match: {sum(x['caveats_ok'] for x in rows)}/{n}",
        f"- Halusinasi terdeteksi: {len(flagged)}/{len(halluc)} CV dengan grounding < 1.0",
    ]
    return '\n'.join(lines)


if __name__ == '__main__':
    rows = evaluate()
    report = render(rows)
    print(report)
    (ROOT / 'evals' / 'latest_report.md').write_text(report + '\n', encoding='utf-8')
    sys.exit(0 if all(x['label_ok'] and x['caveats_ok'] for x in rows) else 1)
