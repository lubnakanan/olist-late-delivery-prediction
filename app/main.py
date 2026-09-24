from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.preprocessing import load_artifacts
from src.predict import predict_order, PredictionError
from src.validation import validate_order, ValidationError
from src.monitoring import record_prediction, record_error, get_metrics


app = FastAPI(
    title="Olist Late Delivery Prediction API",
    description="Inference API for predicting late e-commerce deliveries.",
    version="1.0.0",
)


artifacts = load_artifacts()


class OrderRequest(BaseModel):
    n_items: int
    total_price: float
    total_freight: float
    avg_price: float
    n_unique_sellers: int
    n_unique_products: int
    total_payment_value: float
    n_payment_installments: int
    n_payment_methods: int
    customer_state: str
    purchase_month: int


class PredictionResponse(BaseModel):
    is_late: int
    probability_late: float
    model_version: str


class BatchPredictionRequest(BaseModel):
    orders: List[OrderRequest]


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_version": artifacts["config"]["model"]["version"],
    }


@app.get("/model")
def model_info():
    model = artifacts["model"]

    return {
        "model_type": type(model).__name__,
        "model_version": artifacts["config"]["model"]["version"],
        "features": artifacts["feature_list"],
    }


@app.get("/metrics")
def metrics():
    return JSONResponse(content=get_metrics())


@app.post("/predict", response_model=PredictionResponse)
def predict(order: OrderRequest):
    order_dict = order.model_dump()

    try:
        validate_order(order_dict)

        result = predict_order(order_dict, artifacts)

        record_prediction(
            input_data=order_dict,
            result=result,
            latency_ms=0.0,
        )

        return result

    except ValidationError as error:
        record_error()
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )

    except PredictionError as error:
        record_error()
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@app.post("/predict/batch", response_model=BatchPredictionResponse)
def predict_batch(request: BatchPredictionRequest):
    predictions = []

    for order in request.orders:
        order_dict = order.model_dump()

        try:
            validate_order(order_dict)

            result = predict_order(order_dict, artifacts)

            record_prediction(
                input_data=order_dict,
                result=result,
                latency_ms=0.0,
            )

            predictions.append(result)

        except ValidationError as error:
            record_error()
            raise HTTPException(
                status_code=422,
                detail=str(error),
            )

        except PredictionError as error:
            record_error()
            raise HTTPException(
                status_code=400,
                detail=str(error),
            )

    return {
        "predictions": predictions
    }