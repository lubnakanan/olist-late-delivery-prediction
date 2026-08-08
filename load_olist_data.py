"""
Load all Olist CSV files into a PostgreSQL database.

Before running:
1. Make sure the postgres container is up (docker compose up -d)
2. pip install pandas sqlalchemy psycopg2-binary
3. Put all Olist CSV files inside a folder called "data" next to this script
"""

import pandas as pd
from sqlalchemy import create_engine
import os

# --- 1) Connection settings (must match docker-compose.yml) ---
DB_USER = "olist_user"
DB_PASS = "olist_pass"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "olist_db"

engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# --- 2) Map each CSV file to the table name we want in the database ---
DATA_FOLDER = "data"

FILES_TO_TABLES = {
    "olist_orders_dataset.csv": "orders",
    "olist_customers_dataset.csv": "customers",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "olist_geolocation_dataset.csv": "geolocation",
    "product_category_name_translation.csv": "category_translation",
}

# --- 3) Load each CSV into its table ---
for filename, table_name in FILES_TO_TABLES.items():
    file_path = os.path.join(DATA_FOLDER, filename)

    if not os.path.exists(file_path):
        print(f"Skipping {filename} - file not found in '{DATA_FOLDER}/' folder")
        continue

    print(f"Loading {filename} -> table '{table_name}' ...")
    df = pd.read_csv(file_path)

    # if_exists="replace" means: drop the table if it already exists and recreate it
    # this makes the script safe to re-run
    df.to_sql(table_name, engine, if_exists="replace", index=False)

    print(f"  Done. {len(df)} rows loaded into '{table_name}'.")

print("\nAll available files have been loaded into the database.")
