from typing import Dict

# TfL API configuration
TFL_API_BASE: str = "https://api.tfl.gov.uk"
# Optional API key for higher rate limits (replace with env var in production)
TFL_APP_KEY: str = "ac9b195ad9ed475289a2c67aac5a50e2"

# Sensory weighting factors
WEIGHTS: Dict[str, float] = {
    "platform_wait": 1.0,
    "train_travel": 0.6,
    "walking": 0.3,
    "interchange": 0.8,
}

DELAY_PENALTY: int = 50
