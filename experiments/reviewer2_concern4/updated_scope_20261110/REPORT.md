# Auditoría de truncamiento y longitudes actualizada

162 configuraciones; 20.142 salidas. Sin nuevas generaciones.

[
  {
    "model": "llama",
    "dataset": "all",
    "runs": 81,
    "n": 10071,
    "capped": 56,
    "percent": 0.5560520305828617,
    "prompt_max": 6559,
    "min_headroom_after_512": 1121
  },
  {
    "model": "llama",
    "dataset": "cochrane",
    "runs": 27,
    "n": 3375,
    "capped": 31,
    "percent": 0.9185185185185185,
    "prompt_max": 6559,
    "min_headroom_after_512": 1121
  },
  {
    "model": "llama",
    "dataset": "plaba",
    "runs": 27,
    "n": 3996,
    "capped": 25,
    "percent": 0.6256256256256256,
    "prompt_max": 6439,
    "min_headroom_after_512": 1241
  },
  {
    "model": "llama",
    "dataset": "tsar2025",
    "runs": 27,
    "n": 2700,
    "capped": 0,
    "percent": 0.0,
    "prompt_max": 4097,
    "min_headroom_after_512": 3583
  },
  {
    "model": "mixtral",
    "dataset": "all",
    "runs": 81,
    "n": 10071,
    "capped": 259,
    "percent": 2.5717406414457353,
    "prompt_max": 7615,
    "min_headroom_after_512": 65
  },
  {
    "model": "mixtral",
    "dataset": "cochrane",
    "runs": 27,
    "n": 3375,
    "capped": 180,
    "percent": 5.333333333333333,
    "prompt_max": 7615,
    "min_headroom_after_512": 65
  },
  {
    "model": "mixtral",
    "dataset": "plaba",
    "runs": 27,
    "n": 3996,
    "capped": 79,
    "percent": 1.976976976976977,
    "prompt_max": 7592,
    "min_headroom_after_512": 88
  },
  {
    "model": "mixtral",
    "dataset": "tsar2025",
    "runs": 27,
    "n": 2700,
    "capped": 0,
    "percent": 0.0,
    "prompt_max": 4806,
    "min_headroom_after_512": 2874
  }
]

Los totales son descriptivos de ejecuciones guardadas, no tasas independientes por texto. Los diagnósticos de penalización y ablación quedan separados.
