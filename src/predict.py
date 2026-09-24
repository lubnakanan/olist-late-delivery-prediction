import time

from src.logger import get_logger
from src.preprocessing import load_artifacts, preprocess

logger = get_logger(__name__)


class PredictionError(Exception):
    """Raised when an order cannot be processed or predicted."""
    pass


def predict_order(order: dict, artifacts: dict) -> dict:
    """Predict whether a single order will be late.

    Parameters
    ----------
    order : dict
        Raw order fields (numeric + categorical features, unprocessed).
    artifacts : dict
        Output of load_artifacts() — model, encoder, imputer, feature list.

    Returns
    -------
    dict with keys: is_late (0/1), probability_late (float), model_version (str)
    """
    start_time = time.time()

    # Validate required fields are present before touching the model
    required_fields = (
        artifacts["config"]["features"]["numeric_features"]
        + artifacts["config"]["features"]["categorical_features"]
    )
    missing_fields = [f for f in required_fields if f not in order]

    if missing_fields:
        logger.warning(f"Rejected order — missing fields: {missing_fields}")
        raise PredictionError(f"Missing required fields: {missing_fields}")

    try:
        features_df = preprocess(order, artifacts)

        model = artifacts["model"]
        prediction = int(model.predict(features_df)[0])
        probability = float(model.predict_proba(features_df)[0][1])

        result = {
            "is_late": prediction,
            "probability_late": round(probability, 4),
            "model_version": artifacts["config"]["model"]["version"],
        }

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"Prediction made | input={order} | output={result} | "
            f"latency_ms={elapsed_ms} | model_version={result['model_version']}"
        )

        return result

    except PredictionError:
        raise
    except Exception as e:
        logger.error(f"Prediction failed for input={order} | error={e}")
        raise PredictionError(f"Failed to generate prediction: {e}")


if __name__ == "__main__":
    # Quick manual test when running this file directly
    artifacts = load_artifacts()

    sample_order = {
        "n_items": 1,
        "total_price": 100.0,
        "total_freight": 20.0,
        "avg_price": 100.0,
        "n_unique_sellers": 1,
        "n_unique_products": 1,
        "total_payment_value": 120.0,
        "n_payment_installments": 2,
        "n_payment_methods": 1,
        "customer_state": "SP",
        "purchase_month": 3,
    }

    result = predict_order(sample_order, artifacts)
    print(result)