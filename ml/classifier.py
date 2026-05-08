"""
Machine Learning Classifier.
Handles training, evaluation, and prediction using our ensemble model.
"""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.dataset import MODEL_FEATURE_NAMES

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODELS_DIR / "novashield_classifier.joblib"


@dataclass
class PredictionResult:
    label: str          # "malicious" | "benign"
    confidence: float   # 0.0 - 1.0
    risk_score: float   # 0.0 - 1.0 (probability of being malicious)
    features_used: int  # number of features
    trusted_bypass: bool = False  # True if from whitelist


class WebsiteClassifier:
    """Ensemble classifier for phishing/malicious website detection."""

    def __init__(self):
        self.feature_names = list(MODEL_FEATURE_NAMES)
        self._model: Optional[Pipeline] = None
        self._trained = False
        self._load_if_exists()

    def _build_pipeline(self) -> Pipeline:
        rf = RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
        gb = GradientBoostingClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.8,
            random_state=42,
        )
        lr = LogisticRegression(
            C=1.0,
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
        )
        ensemble = VotingClassifier(
            estimators=[("rf", rf), ("gb", gb), ("lr", lr)],
            voting="soft",
            weights=[2, 2, 1],
        )
        return Pipeline([
            ("scaler", StandardScaler()),
            ("clf", ensemble),
        ])

    def _load_if_exists(self):
        if MODEL_PATH.exists():
            try:
                self._model = joblib.load(MODEL_PATH)
                self._trained = True
                logger.info("Loaded classifier from %s", MODEL_PATH)
            except Exception as exc:
                logger.warning("Failed to load model: %s", exc)
                self._model = None
                self._trained = False

    def train(self, X_train, y_train):
        """Train the ensemble on feature matrix X_train and labels y_train."""
        self._model = self._build_pipeline()
        logger.info("Training ensemble on %d samples...", len(y_train))
        self._model.fit(X_train, y_train)
        self._trained = True
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._model, MODEL_PATH)
        logger.info("Model saved to %s", MODEL_PATH)

    def evaluate(self, X_test, y_test) -> dict:
        """Evaluate the classifier and return metrics dict."""
        if not self._trained:
            raise RuntimeError("Model not trained.")
        y_pred = self._model.predict(X_test)
        y_prob = self._model.predict_proba(X_test)[:, 1]
        metrics = {
            "accuracy": round(accuracy_score(y_test, y_pred), 4),
            "f1": round(f1_score(y_test, y_pred, average="weighted"), 4),
            "roc_auc": round(roc_auc_score(y_test, y_prob), 4),
            "report": classification_report(y_test, y_pred, target_names=["benign", "malicious"]),
        }
        return metrics

    def predict(self, features: list, trusted_bypass: bool = False) -> PredictionResult:
        """
        Predict whether a URL is malicious.
        features: list of selected runtime feature values using UCI-style -1/0/+1 encoding
        trusted_bypass: if True, override with benign result
        """
        if trusted_bypass:
            return PredictionResult(
                label="benign",
                confidence=0.98,
                risk_score=0.02,
                features_used=len(self.feature_names),
                trusted_bypass=True,
            )

        if not self._trained or self._model is None:
            raise RuntimeError("Model not trained. Run train_model.py first.")

        X = np.array(features, dtype=float).reshape(1, -1)
        if X.shape[1] != len(self.feature_names):
            raise ValueError(
                f"Expected {len(self.feature_names)} features, got {X.shape[1]}"
            )

        prob = self._model.predict_proba(X)[0]
        malicious_prob = float(prob[1])
        label = "malicious" if malicious_prob >= 0.5 else "benign"
        confidence = max(malicious_prob, 1.0 - malicious_prob)

        return PredictionResult(
            label=label,
            confidence=round(confidence, 4),
            risk_score=round(malicious_prob, 4),
            features_used=len(self.feature_names),
        )

    def is_ready(self) -> bool:
        return self._trained and self._model is not None


# Module-level singleton
_classifier = WebsiteClassifier()


def get_classifier() -> WebsiteClassifier:
    return _classifier
