# Olist Late Delivery Prediction — MLOps Task 3

Production-style inference pipeline for predicting whether an Olist e-commerce order will be delivered late.

## Project Objective

The project converts the trained notebook workflow into a reproducible inference service.

The model receives a new order and returns:
- Late/on-time prediction
- Probability of late delivery
- Model version

Training remains in notebooks; the production pipeline performs inference only.

## Project Structure

```text
olist_project/
├── app/
│   └── main.py
├── config/
│   └── config.yaml
├── data/
├── models/
├── notebooks/
├── src/
│   ├── config.py
│   ├── preprocessing.py
│   ├── predict.py
│   ├── validation.py
│   ├── monitoring.py
│   └── logger.py
├── tests/
├── artifacts/
├── logs/
├── mlruns/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── mlflow_setup.py
```

## Main Components

### Data and Validation

- DVC is used for data/artifact versioning.
- Great Expectations validates incoming orders.
- Invalid values and invalid categorical states are rejected.

### MLflow

MLflow is used for experiment tracking and model artifact logging.

The model is logged with:
- Model type
- Model version
- MLflow run ID
- Model artifact

### API

The service is implemented with FastAPI.

Available endpoints:

```text
GET  /health
GET  /model
GET  /metrics
POST /predict
POST /predict/batch
```

Interactive API documentation is available through FastAPI's automatic documentation.

## Running Locally

Activate the virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API documentation:

```text
http://localhost:8000/docs
```

## Running with Docker Compose

Build the API image:

```bash
docker build -t olist-late-delivery-api .
```

Start the services:

```bash
docker compose up -d
```

Check service status:

```bash
docker compose ps
```

The API is available at:

```text
http://localhost:8000
```

## Example Prediction

Example request:

```json
{
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
  "purchase_month": 3
}
```

Example response:

```json
{
  "is_late": 1,
  "probability_late": 0.536,
  "model_version": "1.0.0"
}
```

## Testing

Run the complete test suite:

```bash
pytest -q
```

The tests cover:
- Prediction pipeline
- Data validation
- Invalid input rejection
- Health endpoint
- Prediction endpoint
- API validation errors

## Monitoring

Prediction monitoring stores:
- Request count
- Error count
- Average latency
- Error rate
- Late prediction rate
- Prediction records

Monitoring data is stored under:

```text
logs/
```

## CI/CD

GitHub Actions runs on pushes and pull requests to `main`.

The pipeline:
1. Installs Python dependencies
2. Runs pytest
3. Builds the Docker image

## Configuration

Runtime configuration is maintained in:

```text
config/config.yaml
```

Paths and model settings are configuration-driven rather than hardcoded in the inference logic.
