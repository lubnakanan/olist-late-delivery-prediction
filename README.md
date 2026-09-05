# Olist Late Delivery Prediction

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

## Project Structure

```
olist_project/
├── docker-compose.yml # PostgreSQL setup
├── load_olist_data.py # Loads raw CSVs into PostgreSQL
├── notebooks/ # Step-by-step ML pipeline
│ ├── 01_read_join.ipynb
│ ├── 02_labels.ipynb
│ ├── 03_split.ipynb
│ ├── 04_eda.ipynb
│ ├── 05_feature_engineering.ipynb
│ └── 06_train_evaluate.ipynb
└── artifacts/ # Saved outputs (model, transformers, results)
```


Each notebook has a single responsibility: it reads the artifacts produced
by the previous step and writes its own artifacts for the next one. This
keeps the pipeline modular and reproducible, and makes it straightforward
to later convert into production scripts.

## Part 1 — Data Ingestion

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

### How to run the ingestion step

1. Download the 9 CSV files from the Kaggle link above and place them in a
   `data/` folder in this project.
2. Start PostgreSQL:

docker compose up -d
3. Install dependencies:
pip install pandas sqlalchemy psycopg2-binary
4. Load the data:
python load_olist_data.py
5. Connect and explore:

docker exec -it olist_postgres psql -U olist_user -d olist_db

### Verification

Confirmed the join between `orders` and `customers` works correctly:

```sql
SELECT o.order_id, o.order_status, c.customer_city, c.customer_state
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
LIMIT 10;
```

<img width="932" height="737" alt="image" src="https://github.com/user-attachments/assets/5588949b-a8c5-4d7e-a799-d9ad9c46b1b0" />

## Part 2 — ML Pipeline (Notebooks)

Six notebooks, run in order, each producing artifacts consumed by the next:

| # | Notebook | What it does | Key artifact |
|---|---|---|---|
| 1 | `01_read_join` | Reads all 9 tables, aggregates `order_items`/`order_payments` (many rows per order) to one row per order, merges into a single ML table | `01_ml_table.csv` |
| 2 | `02_labels` | Builds the `is_late` label from delivered vs. estimated delivery date; checks class balance | `02_labeled_table.csv` |
| 3 | `03_split` | Splits data into train/validation/test **by time** (not randomly), so the model is evaluated on future, unseen periods | `03_train/val/test.csv` |
| 4 | `04_eda` | Deep exploration of the training set only (data types, missing values, distributions, categorical cardinality, relationships with the label, dates, geography) | Charts + findings summary |
| 5 | `05_feature_engineering` | Builds final features, imputes missing values and one-hot encodes categories — fitted on train only, applied to val/test | Feature tables + fitted transformers |
| 6 | `06_train_evaluate` | Trains a baseline, tunes a Random Forest, evaluates on validation, then touches the test set once at the very end | Trained model + results summary |

### Key EDA Findings (Notebook 4)

- **Class imbalance:** only ~8% of delivered orders are late.
- **`customer_state` is a strong signal:** late rate ranges from ~3.8% (RO) to
  ~27.9% (AL) across states — a 7x difference.
- **Strong seasonality:** late rate spiked to 16–21% in Feb–Mar 2018, versus
  3–8% through most of 2017 — likely an operational disruption in that period.
- **Weak signals:** purchase weekday and the length of the estimated delivery
  window showed little relationship with lateness.

### Modeling Results

| Metric (class = late) | Baseline (always "not late") | Tuned model — validation | Tuned model — test |
|---|---|---|---|
| Recall | 0.00 | 0.13 | 0.01 |
| Precision | 0.00 | 0.07 | 0.02 |

**Key finding:** the tuned Random Forest improved recall over the baseline
on validation, but performance dropped sharply on the test set. This is
most likely because the model partly learned patterns specific to the
unusual Feb–Mar 2018 spike (the last months of the training period), which
did not repeat in the test period (Jun–Aug 2018). Using a **time-based
split** (rather than random) is what surfaced this generalization gap —
a random split would likely have hidden it.

**Conclusion:** the current feature set (order/payment aggregates, state,
month) gives only a weak and inconsistent signal for predicting late
deliveries. This is a legitimate first-iteration baseline result, and
points to concrete next steps rather than a finished model.

### How to run the pipeline

1. Make sure PostgreSQL is running (`docker compose up -d`) and populated
   (see Part 1).
2. Install the additional dependencies:

pip install jupyter matplotlib seaborn scikit-learn
3. Launch Jupyter and run the notebooks in `notebooks/` in order, 01 → 06:
jupyter notebook

## Key Lessons / Notes

- An order can have multiple items, so `order_items` and `order_payments`
  must be **aggregated to one row per order** before joining with `orders`,
  otherwise values get duplicated.
- Care must be taken to avoid **data leakage**: only information available
  at *purchase time* should be used as model input; delivery dates and
  reviews are only used to build the label, never as features.
- Fitted transformers (imputer, encoder) are trained on the training split
  only, then applied unchanged to validation/test — the same fitted objects
  must be reused in production rather than refit on new data.
- A time-based split is essential for this problem: it revealed a
  generalization gap between validation and test that a random split
  would not have exposed.

## Next Steps

- Investigate the Feb–Mar 2018 delay spike directly (external events,
  operational changes).
- Add richer features: seller-level delay history, shipping distance,
  carrier information.
- Test whether a simpler or differently regularized model generalizes
  more consistently across time periods.
- Convert the notebooks into production-ready Python scripts.
