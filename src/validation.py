import great_expectations as gx
import pandas as pd

from src.logger import get_logger


logger = get_logger(__name__)


class ValidationError(Exception):
    """Raised when an incoming order fails data validation."""

    pass


def validate_order(order: dict) -> None:
    """
    Validate a single incoming order.

    Validation rules:
    - Required numeric fields must be present and not null.
    - Numeric fields must be non-negative.
    - customer_state must be a valid Brazilian state abbreviation.
    - purchase_month must be between 1 and 12.

    Raises:
        ValidationError: If the order fails one or more expectations.
    """

    df = pd.DataFrame([order])

    # Use an ephemeral Great Expectations context.
    context = gx.get_context(mode="ephemeral")

    # Create a batch from the incoming DataFrame.
    batch = context.data_sources.pandas_default.read_dataframe(
        df,
        asset_name="incoming_order",
    )

    # ---------------------------------------------------------
    # Define expectations
    # ---------------------------------------------------------

    expectations = []

    numeric_fields = [
        "n_items",
        "total_price",
        "total_freight",
        "avg_price",
        "n_unique_sellers",
        "n_unique_products",
        "total_payment_value",
        "n_payment_installments",
        "n_payment_methods",
    ]

    for field in numeric_fields:

        expectations.append(
            gx.expectations.ExpectColumnValuesToNotBeNull(
                column=field
            )
        )

        expectations.append(
            gx.expectations.ExpectColumnValuesToBeBetween(
                column=field,
                min_value=0,
                max_value=None,
            )
        )

    # ---------------------------------------------------------
    # Customer state
    # ---------------------------------------------------------

    valid_states = [
        "AC",
        "AL",
        "AP",
        "AM",
        "BA",
        "CE",
        "DF",
        "ES",
        "GO",
        "MA",
        "MT",
        "MS",
        "MG",
        "PA",
        "PB",
        "PR",
        "PE",
        "PI",
        "RJ",
        "RN",
        "RS",
        "RO",
        "RR",
        "SC",
        "SP",
        "SE",
        "TO",
    ]

    expectations.append(
        gx.expectations.ExpectColumnValuesToNotBeNull(
            column="customer_state"
        )
    )

    expectations.append(
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="customer_state",
            value_set=valid_states,
        )
    )

    # ---------------------------------------------------------
    # Purchase month
    # ---------------------------------------------------------

    expectations.append(
        gx.expectations.ExpectColumnValuesToNotBeNull(
            column="purchase_month"
        )
    )

    expectations.append(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="purchase_month",
            min_value=1,
            max_value=12,
        )
    )

    # ---------------------------------------------------------
    # Run validation
    # ---------------------------------------------------------

    failed = []

    for expectation in expectations:

        result = batch.validate(expectation)

        if not result.success:

            failed.append(
                {
                    "column": getattr(
                        expectation,
                        "column",
                        None,
                    ),
                    "expectation": expectation.__class__.__name__,
                }
            )

    # ---------------------------------------------------------
    # Handle validation failure
    # ---------------------------------------------------------

    if failed:

        logger.warning(
            "Validation failed | order=%s | failures=%s",
            order,
            failed,
        )

        raise ValidationError(
            f"Order failed validation: {failed}"
        )

    # ---------------------------------------------------------
    # Successful validation
    # ---------------------------------------------------------

    logger.info(
        "Order passed validation | order=%s",
        order,
    )


# =============================================================
# Manual test
# =============================================================

if __name__ == "__main__":

    # ---------------------------------------------------------
    # Valid order
    # ---------------------------------------------------------

    good_order = {
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

    try:
        validate_order(good_order)
        print("Good order passed.")

    except ValidationError as error:
        print(f"Good order failed: {error}")

    # ---------------------------------------------------------
    # Invalid order
    # ---------------------------------------------------------

    bad_order = dict(good_order)

    bad_order["customer_state"] = "XX"
    bad_order["total_price"] = -50

    try:
        validate_order(bad_order)
        print("ERROR: Bad order unexpectedly passed.")

    except ValidationError as error:
        print(f"Bad order correctly rejected: {error}")