import joblib
import pandas as pd

from src.config import PROJECT_ROOT, load_config


def load_artifacts():
    """Load the trained model and fitted transformers from disk (once)."""
    config = load_config()

    model_path = PROJECT_ROOT / config["model"]["path"]
    encoder_path = PROJECT_ROOT / config["transformers"]["encoder_path"]
    imputer_path = PROJECT_ROOT / config["transformers"]["imputer_path"]
    feature_list_path = PROJECT_ROOT / config["features"]["feature_list_path"]

    model = joblib.load(model_path)
    encoder = joblib.load(encoder_path)
    imputer = joblib.load(imputer_path)

    with open(feature_list_path, "r") as f:
        feature_list = f.read().splitlines()

    return {
        "model": model,
        "encoder": encoder,
        "imputer": imputer,
        "feature_list": feature_list,
        "config": config,
    }


def preprocess(order: dict, artifacts: dict) -> pd.DataFrame:
    """Turn a single raw order (dict) into a feature row ready for the model.

    This mirrors Notebook 5 exactly, but only transforms (never fits).
    """
    config = artifacts["config"]
    numeric_features = config["features"]["numeric_features"]
    categorical_features = config["features"]["categorical_features"]

    df = pd.DataFrame([order])

    # Impute numeric features using the already-fitted imputer
    df[numeric_features] = artifacts["imputer"].transform(df[numeric_features])

    # Encode categorical features using the already-fitted encoder
    encoded = artifacts["encoder"].transform(df[categorical_features])
    encoded_cols = artifacts["encoder"].get_feature_names_out(categorical_features)
    encoded_df = pd.DataFrame(encoded, columns=encoded_cols, index=df.index)

    final_df = pd.concat([df[numeric_features], encoded_df], axis=1)

    # Make sure columns are in the exact order the model expects
    final_df = final_df.reindex(columns=artifacts["feature_list"], fill_value=0)

    return final_df