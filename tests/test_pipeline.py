from fastapi.testclient import TestClient

from app.main import app
from src.predict import predict_order
from src.preprocessing import load_artifacts
from src.validation import validate_order, ValidationError


client = TestClient(app)


GOOD_ORDER = {
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


def test_prediction_pipeline():
    artifacts = load_artifacts()

    result = predict_order(GOOD_ORDER, artifacts)

    assert result["is_late"] in [0, 1]
    assert 0 <= result["probability_late"] <= 1
    assert result["model_version"] == "1.0.0"


def test_valid_order():
    validate_order(GOOD_ORDER)


def test_invalid_order_is_rejected():
    bad_order = GOOD_ORDER.copy()
    bad_order["customer_state"] = "XX"

    try:
        validate_order(bad_order)
        assert False, "Invalid order was accepted"
    except ValidationError:
        assert True


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_predict_endpoint():
    response = client.post("/predict", json=GOOD_ORDER)

    assert response.status_code == 200

    data = response.json()

    assert data["is_late"] in [0, 1]
    assert 0 <= data["probability_late"] <= 1
    assert data["model_version"] == "1.0.0"


def test_invalid_api_input():
    bad_order = GOOD_ORDER.copy()
    bad_order["customer_state"] = "XX"

    response = client.post("/predict", json=bad_order)

    assert response.status_code == 422