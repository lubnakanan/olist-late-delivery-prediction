# Olist Late Delivery Prediction — Task 1: Data Ingestion

## Business Problem

Olist is a Brazilian e-commerce marketplace that connects small sellers to larger
sales channels. After a customer places an order, Olist gives them an estimated
delivery date. When orders arrive later than that estimate, it hurts customer
satisfaction (low review scores, complaints) and increases support costs.

**Goal:** Build a model that predicts, at purchase time, whether an order is
likely to be delivered late — so the business can warn customers early, set
more realistic delivery promises, and prioritize support before a bad review
happens.

## Dataset

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
— ~100k orders placed between 2016-2018, split across 9 related CSV files
(orders, customers, order items, payments, reviews, products, sellers,
geolocation, category translation).

The data is relational, not a single ready-made ML table — it needs to be
loaded into a proper database and joined/aggregated before it can be used
for modeling.

## What I Did (Task 1)

1. **Set up PostgreSQL locally using Docker** (`docker-compose.yml`) instead
   of a native install, to keep the environment isolated and reproducible.
2. **Loaded all 9 Olist CSV files into PostgreSQL** using a Python script
   (`load_olist_data.py`) built with `pandas` + `SQLAlchemy` — each CSV
   becomes its own table.
3. **Verified the data** by listing all tables (`\dt`), checking row counts
   (e.g. `orders` = 99,441 rows, matching the known dataset size), and
   running a `JOIN` between `orders` and `customers` on `customer_id` to
   confirm the relational structure works correctly.
4. **Understood the table relationships**:
   - `orders` ⇄ `customers` via `customer_id`
   - `orders` ⇄ `order_items` via `order_id`
   - `order_items` ⇄ `products` via `product_id`
   - `order_items` ⇄ `sellers` via `seller_id`
   - `orders` ⇄ `order_payments` / `order_reviews` via `order_id`

## Key Lessons / Notes

- An order can have multiple items, so `order_items` and `order_payments`
  must be **aggregated to one row per order** before joining with `orders`,
  otherwise values get duplicated.
- Care must be taken to avoid **data leakage**: only information available
  at *purchase time* should be used as model input. Delivery dates and
  reviews are useful for building the label, not as features.

## How to Run This Locally

1. Download the 9 CSV files from the Kaggle link above and place them in a
   `data/` folder in this project.
2. Start PostgreSQL:
   ```
   docker compose up -d
   ```
3. Install dependencies:
   ```
   pip install pandas sqlalchemy psycopg2-binary
   ```
4. Load the data:
   ```
   python load_olist_data.py
   ```
5. Connect and explore:
   ```
   docker exec -it olist_postgres psql -U olist_user -d olist_db
   ```

## Next Steps (future tasks)

- Exploratory Data Analysis (EDA)
- Feature engineering (aggregating items/payments per order, avoiding leakage)
- Framing as a binary classification problem: late vs. on-time delivery
