"""
Dataset Manager.
Downloads and formats the UCI Machine Learning Phishing Websites dataset.
"""

import logging
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

# UCI ML Repository — Phishing Websites dataset
UCI_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00327/Training%20Dataset.arff"
DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH = DATA_DIR / "phishing_dataset.csv"

# The 30 feature names from the original UCI ARFF (in order)
UCI_FEATURE_NAMES = [
    "having_IP_Address", "URL_Length", "Shortining_Service", "having_At_Symbol",
    "double_slash_redirecting", "Prefix_Suffix", "having_Sub_Domain", "SSLfinal_State",
    "Domain_registeration_length", "Favicon", "port", "HTTPS_token",
    "Request_URL", "URL_of_Anchor", "Links_in_tags", "SFH",
    "Submitting_to_email", "Abnormal_URL", "Redirect", "on_mouseover",
    "RightClick", "popUpWidnow", "Iframe", "age_of_domain",
    "DNSRecord", "web_traffic", "Page_Rank", "Google_Index",
    "Links_pointing_to_page", "Statistical_report",
]
TARGET_COL = "Result"

# Runtime model feature subset.
# We intentionally drop legacy WHOIS / traffic / blacklist-style fields and
# low-signal browser-era features that are either unavailable during live scans
# or were contributing noise with modern sites.
MODEL_FEATURE_NAMES = [
    "having_IP_Address",
    "URL_Length",
    "Shortining_Service",
    "having_At_Symbol",
    "Prefix_Suffix",
    "having_Sub_Domain",
    "SSLfinal_State",
    "Favicon",
    "port",
    "HTTPS_token",
    "Request_URL",
    "URL_of_Anchor",
    "Links_in_tags",
    "SFH",
    "Submitting_to_email",
    "on_mouseover",
    "popUpWidnow",
]

DROPPED_FEATURE_NAMES = [
    name for name in UCI_FEATURE_NAMES
    if name not in MODEL_FEATURE_NAMES
]


def _download_and_convert() -> pd.DataFrame:
    """Download UCI ARFF and convert to DataFrame."""
    logger.info("Downloading UCI Phishing dataset from %s", UCI_URL)
    with urllib.request.urlopen(UCI_URL, timeout=30) as resp:
        raw = resp.read().decode("utf-8", errors="replace")

    # Parse ARFF: skip header, find @data section
    lines = raw.splitlines()
    data_start = next(i for i, l in enumerate(lines) if l.strip().lower() == "@data") + 1
    data_lines = [l.strip() for l in lines[data_start:] if l.strip() and not l.startswith("%")]

    rows = [list(map(int, l.split(","))) for l in data_lines]
    cols = UCI_FEATURE_NAMES + [TARGET_COL]
    df = pd.DataFrame(rows, columns=cols)

    # Dataset inspection shows rows with heavily suspicious signals map to Result=-1,
    # so we treat -1 as malicious and +1 as benign.
    df["label"] = (df[TARGET_COL] == -1).astype(int)
    return df


def _make_synthetic() -> pd.DataFrame:
    """Create a balanced synthetic dataset that respects UCI encoding."""
    rng = np.random.default_rng(42)
    n = 2000

    # Phishing samples: features biased toward -1
    phish = rng.choice([-1, 0, 1], size=(n // 2, 30), p=[0.6, 0.25, 0.15])
    phish_df = pd.DataFrame(phish, columns=UCI_FEATURE_NAMES)
    phish_df["label"] = 1

    # Benign samples: features biased toward +1
    benign = rng.choice([-1, 0, 1], size=(n // 2, 30), p=[0.05, 0.15, 0.80])
    benign_df = pd.DataFrame(benign, columns=UCI_FEATURE_NAMES)
    benign_df["label"] = 0

    df = pd.concat([phish_df, benign_df], ignore_index=True)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    logger.warning("Using synthetic dataset (%d samples). Real dataset preferred.", n)
    return df


def load_dataset(force_download: bool = False) -> pd.DataFrame:
    """Load the phishing dataset. Downloads if not cached."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not force_download and CSV_PATH.exists():
        logger.info("Loading cached dataset from %s", CSV_PATH)
        df = pd.read_csv(CSV_PATH)
        if TARGET_COL in df.columns:
            df["label"] = (df[TARGET_COL] == -1).astype(int)
        return df

    try:
        df = _download_and_convert()
        df.to_csv(CSV_PATH, index=False)
        logger.info("Dataset saved to %s (%d samples)", CSV_PATH, len(df))
        return df
    except Exception as exc:
        logger.error("Download failed: %s — falling back to synthetic dataset", exc)
        df = _make_synthetic()
        df.to_csv(CSV_PATH, index=False)
        return df


def get_train_test_split(
    test_size: float = 0.2,
    random_state: int = 42,
    feature_names: list[str] | None = None,
):
    """Return (X_train, X_test, y_train, y_test) for the selected runtime feature set."""
    df = load_dataset()
    selected = feature_names or MODEL_FEATURE_NAMES
    X = df[selected].values
    y = df["label"].values
    return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
