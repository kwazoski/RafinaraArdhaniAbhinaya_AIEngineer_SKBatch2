"""Pipeline: redaksi PII -> ekstraksi LLM -> validasi schema -> grounding -> scoring -> caveat -> label."""
import re

from pydantic import ValidationError

from .config import JOB, POSSIBLE_THRESHOLD, STRONG_THRESHOLD, WEIGHTS
from .llm import SYSTEM
from .schema import CandidateProfile


# ---------- Preprocessing ----------
def redact_pii(text):
    text = re.sub(r'[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+[.][A-Za-z0-9.]+', '[EMAIL]', text)
    # hanya nomor berawalan 0 atau +62 yang tidak menempel pada angka lain,
    # agar rentang tahun (2019 - 2023) tidak ikut termasking
    return re.sub(r'(?<![0-9])(?:[+]62[ -]?|0)[0-9][0-9 -]{7,}[0-9]', '[PHONE]', text)


def norm(s):
    return ' '.join(s.lower().split())


# ---------- Validasi hasil ekstraksi ----------
def check_grounding(p, cv):
    """Setiap evidence harus muncul di teks CV. Return (item_bermasalah, grounding_rate)."""
    cv_n = norm(cv)
    items = ([('experience', e.evidence) for e in p.experience]
             + [('education', e.evidence) for e in p.education]
             + [('skill', s.evidence) for s in p.skills])
    bad = [(k, ev) for k, ev in items if norm(ev) not in cv_n]
    return bad, 1 - len(bad) / max(len(items), 1)


def is_month(x):
    return x is not None and len(x) == 7 and x[4] == '-'


def months(a, b, as_of):
    b = as_of if b == 'present' else b
    (y1, m1), (y2, m2) = [list(map(int, x.split('-'))) for x in (a, b)]
    return (y2 - y1) * 12 + (m2 - m1) + 1


def conservative_months(p, as_of):
    """Hanya menghitung entri dengan tanggal bulan-tahun lengkap; sisanya ditandai vague."""
    total, vague = 0, []
    for e in p.experience:
        if is_month(e.start) and (is_month(e.end) or e.end == 'present'):
            total += months(e.start, e.end, as_of)
        else:
            vague.append(e.title)
    return total, vague


# ---------- Scoring deterministik ----------
def score(p, job, total_months):
    have = {norm(s.name) for s in p.skills}
    must = [k for k in job['must_have'] if k in have]
    missing = [k for k in job['must_have'] if k not in have]
    nice = [k for k in job['nice_to_have'] if k in have]
    s = (WEIGHTS['must_have'] * len(must) / len(job['must_have'])
         + WEIGHTS['experience'] * min(total_months / job['min_months'], 1)
         + WEIGHTS['nice_to_have'] * len(nice) / len(job['nice_to_have']))
    return round(s, 2), must, missing, nice


# ---------- Caveat & label ----------
def build_caveats(p, job, total_months, vague, bad):
    c = []

    def add(code, sev, msg):
        c.append({'code': code, 'severity': sev, 'message': msg})

    if bad:
        add('ungrounded_extraction', 'high',
            f'{len(bad)} item tidak ditemukan di CV; kemungkinan halusinasi')
    if not p.experience:
        add('no_experience_found', 'medium', 'Tidak ada pengalaman terdeteksi; cek format CV')
    if vague:
        add('vague_dates', 'medium', 'Tanggal tidak lengkap, tidak dihitung: ' + ', '.join(vague))
    if total_months < job['min_months']:
        add('experience_below_min', 'medium',
            f'Pengalaman terverifikasi {total_months} bulan, minimal {job["min_months"]}')
    if p.extraction_notes:
        add('extractor_notes', 'low', '; '.join(p.extraction_notes))
    add('self_reported', 'low', 'Skill dan pencapaian adalah klaim di CV, belum diverifikasi')
    return c


def decide(s, caveats):
    sev = {c['severity'] for c in caveats}
    if 'high' in sev:
        return 'needs_human_review'
    if s >= STRONG_THRESHOLD and 'medium' not in sev:
        return 'strong_match'
    if s >= POSSIBLE_THRESHOLD:
        return 'possible_match'
    return 'low_match_needs_review'   # sengaja tidak ada label reject


# ---------- Pipeline ----------
def run_pipeline(cv_text, llm, job=JOB, as_of='2026-11'):
    clean = redact_pii(cv_text)
    profile = None
    for _ in range(2):   # retry 1x jika output tidak valid
        try:
            profile = CandidateProfile.model_validate_json(llm(SYSTEM, clean))
            break
        except ValidationError:
            continue
    if profile is None:
        return {
            'recommendation': {'label': 'needs_human_review', 'reason': 'schema_validation_failed'},
            'requires_human_review': True,
        }
    bad, grounding = check_grounding(profile, clean)
    total, vague = conservative_months(profile, as_of)
    s, must, missing, nice = score(profile, job, total)
    caveats = build_caveats(profile, job, total, vague, bad)
    return {
        'profile': profile.model_dump(),
        'recommendation': {
            'label': decide(s, caveats),
            'match_score': s,
            'matched_must_have': must,
            'missing_must_have': missing,
            'matched_nice_to_have': nice,
            'conservative_months': total,
            'grounding_rate': round(grounding, 2),
            'caveats': caveats,
            'questions_for_reviewer': ['Konfirmasi durasi dan scope: ' + t for t in vague],
        },
        'requires_human_review': True,
        'disclaimer': 'Rekomendasi awal otomatis. Keputusan final ada pada reviewer manusia.',
    }
