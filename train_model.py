"""
Model Training Script.
Entry point to download data, train the ensemble, and save the artifact.
"""
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 60)
    logger.info("  NovaShield — Model Training")
    logger.info("=" * 60)

    # Import here so path is set up
    from ml.dataset import MODEL_FEATURE_NAMES, get_train_test_split
    from ml.classifier import WebsiteClassifier

    logger.info("Loading dataset...")
    X_train, X_test, y_train, y_test = get_train_test_split()
    logger.info(
        "Dataset: %d train / %d test | Features: %d | Classes: benign=%d malicious=%d",
        len(y_train), len(y_test), len(MODEL_FEATURE_NAMES),
        (y_test == 0).sum(), (y_test == 1).sum(),
    )

    clf = WebsiteClassifier()
    clf.train(X_train, y_train)

    logger.info("Evaluating...")
    metrics = clf.evaluate(X_test, y_test)

    logger.info("\n%s", "=" * 60)
    logger.info("  EVALUATION RESULTS")
    logger.info("  Accuracy : %.2f%%", metrics["accuracy"] * 100)
    logger.info("  F1-Score : %.2f%%", metrics["f1"] * 100)
    logger.info("  ROC-AUC  : %.2f%%", metrics["roc_auc"] * 100)
    logger.info("  %s", "=" * 60)
    logger.info("\nClassification Report:\n%s", metrics["report"])

    # Save metrics report
    report_path = Path("ml/models/evaluation_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(
            {k: v for k, v in metrics.items() if k != "report"},
            f, indent=2,
        )
    logger.info("Evaluation report saved to %s", report_path)
    logger.info("\n[OK] Model is ready. You can now run the project in Direct or Distributed mode.")


if __name__ == "__main__":
    main()
