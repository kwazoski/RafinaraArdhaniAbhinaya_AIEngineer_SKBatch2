# CV Screening Assistant

Mini assignment AI Engineer (Sekolah Karir Batch 2): flow LLM kecil yang mengekstrak informasi kandidat
dari CV ke schema terstruktur, lalu memberi **rekomendasi awal dengan caveat**, bukan keputusan final.

> Semua data adalah mock. Tidak ada data pribadi nyata dan tidak ada API berbayar.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python evals/run_golden.py      # evaluasi golden set (5 CV), menulis evals/latest_report.md
pytest                          # 12 tes: golden regression, safety, fairness, PII
```

## Struktur repo

```
src/cv_screening/
  schema.py     # CandidateProfile: output schema ekstraksi (tanpa atribut sensitif)
  config.py     # job requirement mock, bobot skor, ambang label
  llm.py        # system prompt + MockLLM (ganti dengan LLM sungguhan)
  pipeline.py   # redaksi PII -> ekstraksi -> validasi -> grounding -> scoring -> caveat -> label
data/
  cvs/                   # 5 CV mock (satu per edge case)
  mock_llm_responses/    # respons LLM mock untuk tiap CV
  golden.json            # label manual: skill, label, set caveat
evals/run_golden.py      # metrik per CV dan ringkasan; exit 1 jika ada regresi
tests/                   # pytest
docs/ARCHITECTURE.md     # architecture note, keputusan desain, safety
```

## Flow singkat

```
CV text -> [PII redaction] -> [LLM extraction] -> [schema validation + retry]
        -> [grounding check: evidence harus ada di CV] -> [rule-based scoring]
        -> [caveat engine + label] -> human review (keputusan final di manusia)
```

## Golden set (edge case)

| CV | Edge case | Label yang diharapkan |
|---|---|---|
| cv_01 | Freelance hanya bertahun, durasi di bawah minimum | possible_match |
| cv_02 | Kandidat lengkap dan kuat | strong_match |
| cv_03 | Bahasa Indonesia, tanpa tanggal, career changer | low_match_needs_review |
| cv_04 | Prompt injection di summary | low_match_needs_review (skor tidak terpengaruh) |
| cv_05 | Extractor mengarang skill dan pengalaman | needs_human_review (tertangkap grounding check) |

## Memakai LLM sungguhan

Buat fungsi `llm(system, user) -> str` yang mengembalikan JSON sesuai `CandidateProfile`
(gunakan JSON mode / structured output jika tersedia), lalu:

```python
from cv_screening import run_pipeline
result = run_pipeline(cv_text, llm=my_llm)
```

Bagian lain pipeline tidak perlu diubah. Gunakan hanya data mock atau data yang sudah dianonimkan.

## Catatan penggunaan AI

Claude (Anthropic) membantu menyusun struktur repo, draft kode, dan CV mock. Kode dijalankan dan diuji,
dan satu bug (regex masking telepon yang menghapus rentang tahun) ditemukan dan diperbaiki lewat pengujian.
[Sesuaikan catatan ini dengan penggunaan Anda yang sebenarnya.]
