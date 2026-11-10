"""Job requirement mock yang dipakai untuk scoring. Ganti sesuai lowongan."""

JOB = {
    'title': 'Junior Data Analyst (MOCK)',
    'must_have': ['python', 'sql', 'excel'],
    'nice_to_have': ['tableau', 'power bi'],
    'min_months': 12,
}

# Bobot scoring (asumsi; perlu dikalibrasi dengan keputusan recruiter)
WEIGHTS = {'must_have': 0.60, 'experience': 0.25, 'nice_to_have': 0.15}

# Ambang label
STRONG_THRESHOLD = 0.75
POSSIBLE_THRESHOLD = 0.50
