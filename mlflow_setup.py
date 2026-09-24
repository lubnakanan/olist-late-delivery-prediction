import joblib
import mlflow
import mlflow.sklearn

from src.config import PROJECT_ROOT, load_config


# MLflow tracking database
mlflow.set_tracking_uri(
    f"sqlite:///{PROJECT_ROOT / 'mlflow.db'}"
)

# Experiment
mlflow.set_experiment("olist-late-delivery")

# Load configuration
config = load_config()

# Load the already-trained model
# No training or fitting happens here.
model_path = PROJECT_ROOT / config["model"]["path"]
model = joblib.load(model_path)


# Start an MLflow run
with mlflow.start_run(run_name="olist-late-delivery-model") as run:

    # Log model information
    mlflow.log_param(
        "model_type",
        type(model).__name__
    )

    mlflow.log_param(
        "model_version",
        config["model"]["version"]
    )

    # Log the existing trained model to MLflow
    mlflow.sklearn.log_model(
        sk_model=model,
        name="late_delivery_model",
        skops_trusted_types=[
            "sklearn.tree._tree.Tree"
        ],
    )

    print(f"Run ID: {run.info.run_id}")
    print("Model logged successfully.")