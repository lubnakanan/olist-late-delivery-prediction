import json
import time
from pathlib import Path

from src.config import PROJECT_ROOT
from src.logger import get_logger

logger = get_logger(__name__)

METRICS_FILE = PROJECT_ROOT / "logs" / "metrics.json"
PREDICTIONS_FILE = PROJECT_ROOT / "logs" / "predictions.jsonl"


def _load_metrics():
    if not METRICS_FILE.exists():
        return {
            "request_count": 0,
            "error_count": 0,
            "total_latency_ms": 0.0,
            "late_predictions": 0,
            "on_time_predictions": 0,
        }

    with open(METRICS_FILE, "r") as file:
        return json.load(file)


def record_prediction(
    input_data: dict,
    result: dict,
    latency_ms: float,
):
    metrics = _load_metrics()

    metrics["request_count"] += 1
    metrics["total_latency_ms"] += latency_ms

    if result["is_late"] == 1:
        metrics["late_predictions"] += 1
    else:
        metrics["on_time_predictions"] += 1

    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(METRICS_FILE, "w") as file:
        json.dump(metrics, file, indent=2)

    prediction_record = {
        "timestamp": time.time(),
        "input": input_data,
        "prediction": result,
        "latency_ms": latency_ms,
    }

    with open(PREDICTIONS_FILE, "a") as file:
        file.write(json.dumps(prediction_record) + "\n")


def record_error():
    metrics = _load_metrics()
    metrics["request_count"] += 1
    metrics["error_count"] += 1

    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(METRICS_FILE, "w") as file:
        json.dump(metrics, file, indent=2)


def get_metrics():
    metrics = _load_metrics()

    if metrics["request_count"] > 0:
        avg_latency = (
            metrics["total_latency_ms"] / metrics["request_count"]
        )
        error_rate = (
            metrics["error_count"] / metrics["request_count"]
        )
    else:
        avg_latency = 0.0
        error_rate = 0.0

    prediction_total = (
        metrics["late_predictions"]
        + metrics["on_time_predictions"]
    )

    late_rate = (
        metrics["late_predictions"] / prediction_total
        if prediction_total > 0
        else 0.0
    )

    return {
        **metrics,
        "average_latency_ms": round(avg_latency, 2),
        "error_rate": round(error_rate, 4),
        "late_prediction_rate": round(late_rate, 4),
    }