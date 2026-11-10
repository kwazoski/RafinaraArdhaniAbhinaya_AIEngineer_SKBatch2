# Architecture Note

## Prinsip desain

1. **LLM hanya mengekstrak.** Skor dan label dihitung kode deterministik sehingga bisa diaudit dan dites.
2. **Setiap fakta punya evidence** (kutipan persis dari CV) yang diverifikasi terhadap teks CV.
3. **Tidak ada keputusan otomatis.** Tidak ada label reject; `requires_human_review` selalu `true`.
4. **Minimisasi data.** PII dimasking sebelum masuk LLM; atribut yang dilindungi tidak ada di schema dan scoring.

## Komponen

| Tahap | Modul | Tujuan | Kegagalan ditangani dengan |
|---|---|---|---|
| Redaksi PII | `pipeline.redact_pii` | Email dan telepon tidak dikirim ke LLM | Regex ketat agar rentang tahun aman |
| Ekstraksi | `llm.py` | Teks CV menjadi JSON terstruktur | Prompt ketat, CV diperlakukan sebagai data |
| Validasi schema | `schema.py` | Menjamin bentuk output | Retry 1x, lalu `needs_human_review` |
| Grounding check | `pipeline.check_grounding` | Menangkap halusinasi | Caveat `high` -> `needs_human_review` |
| Scoring | `pipeline.score` | Skor transparan (60/25/15) | Bobot di `config.py`, perlu kalibrasi |
| Caveat engine | `pipeline.build_caveats` | Menyatakan ketidakpastian | Severity low/medium/high |
| Label | `pipeline.decide` | Rekomendasi awal | Label terendah tetap review manusia |

## Logika label

- `needs_human_review`: ada caveat `high` (halusinasi) atau output LLM tidak valid.
- `strong_match`: skor >= 0.75 dan tidak ada caveat `medium`.
- `possible_match`: skor >= 0.50.
- `low_match_needs_review`: sisanya. Tetap perlu dilihat manusia; bukan penolakan.

## Safety

- Prompt injection: skor dihitung kode, bukan LLM, sehingga instruksi tersembunyi di CV tidak bisa menaikkan skor.
- Fairness: nama, universitas, dan atribut sensitif tidak memengaruhi skor (tes kontrafaktual di `tests/`).
- Kegagalan aman: output rusak atau halusinasi selalu berujung ke manusia, bukan tebakan.

## Keterbatasan dan langkah berikutnya

- Substring grounding rapuh terhadap hasil parsing PDF yang berantakan; perlu fuzzy match.
- Sinonim skill (MS Excel vs Excel) perlu taksonomi skill.
- Bobot dan ambang adalah asumsi; kalibrasi dengan keputusan recruiter dan ukur agreement (Cohen's kappa).
- Golden set baru 5 CV; perluas ke 20 sampai 30 dengan variasi format (dua kolom, hasil OCR).
- Belum mencakup parsing PDF/OCR dan multi-job matching.
