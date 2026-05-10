from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype

from app.utils.dispatcher import dispatcher
from app.utils.logger import logger


@dataclass(frozen=True)
class RuleError:
    """Structured validation error returned by the business rules validator."""

    rule: str
    column: str
    row: int | None
    message: str
    value: Any = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "column": self.column,
            "row": self.row,
            "message": self.message,
            "value": None if pd.isna(self.value) else self.value,
        }


MONEY_KEYWORDS = (
    "amount",
    "monto",
    "price",
    "precio",
    "revenue",
    "ingreso",
    "venta",
    "sales",
    "net_sales",
    "gross_sales",
    "subtotal",
    "total",
    "cost",
    "costo",
)

NON_NEGATIVE_NUMERIC_KEYWORDS = MONEY_KEYWORDS + (
    "quantity",
    "cantidad",
    "qty",
    "stock",
    "units",
    "unidades",
    "count",
    "conteo",
)

PERCENT_KEYWORDS = ("percent", "percentage", "pct", "rate", "ratio", "descuento_pct", "discount_pct")
DISCOUNT_KEYWORDS = ("discount", "descuento")
DATE_KEYWORDS = ("date", "fecha", "created_at", "updated_at", "timestamp", "day", "month", "year")

MIN_REASONABLE_DATE = pd.Timestamp("1900-01-01", tz="UTC")
MAX_FUTURE_SKEW = timedelta(days=1)


def _normalise_column_name(column: Any) -> str:
    return str(column).strip().lower()


def _column_matches(column: Any, keywords: Iterable[str]) -> bool:
    name = _normalise_column_name(column)
    return any(keyword in name for keyword in keywords)


def _to_numeric(series: pd.Series) -> pd.Series:
    """Parse numeric legacy values without raising on malformed rows."""
    if is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    cleaned = (
        series.astype("string")
        .str.strip()
        .str.replace(r"[^0-9,\.\-]", "", regex=True)
    )

    # Support both "1,234.56" and "1.234,56" style values.
    comma_decimal = cleaned.str.contains(r",\d{1,2}$", regex=True, na=False)
    cleaned = cleaned.mask(
        comma_decimal,
        cleaned.str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
    )
    cleaned = cleaned.mask(~comma_decimal, cleaned.str.replace(",", "", regex=False))

    return pd.to_numeric(cleaned, errors="coerce")


def _to_datetime(series: pd.Series) -> pd.Series:
    """Parse dates defensively, accepting mixed legacy formats."""
    if is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce", utc=True)
    return pd.to_datetime(series, errors="coerce", utc=True, format="mixed")


def _row_errors(
    *,
    df: pd.DataFrame,
    mask: pd.Series,
    rule: str,
    column: str,
    message: str,
    max_examples: int = 20,
) -> list[RuleError]:
    errors: list[RuleError] = []

    for row_index in df.index[mask.fillna(False)][:max_examples]:
        errors.append(
            RuleError(
                rule=rule,
                column=column,
                row=int(row_index) if isinstance(row_index, int) else None,
                message=message,
                value=df.at[row_index, column],
            )
        )

    if int(mask.fillna(False).sum()) > max_examples:
        errors.append(
            RuleError(
                rule=rule,
                column=column,
                row=None,
                message=f"{int(mask.sum()) - max_examples} additional rows failed this rule.",
            )
        )

    return errors


def _validate_non_negative(df: pd.DataFrame, column: str) -> list[RuleError]:
    numeric = _to_numeric(df[column])
    negative = numeric < 0
    parse_failed = df[column].notna() & numeric.isna() & df[column].astype("string").str.strip().ne("")

    errors = _row_errors(
        df=df,
        mask=negative,
        rule="non_negative_numeric",
        column=column,
        message="Business numeric fields such as amounts, prices, quantities and totals cannot be negative.",
    )

    errors.extend(
        _row_errors(
            df=df,
            mask=parse_failed,
            rule="numeric_parse",
            column=column,
            message="Could not parse numeric legacy value.",
        )
    )

    return errors


def _validate_percentage(df: pd.DataFrame, column: str) -> list[RuleError]:
    numeric = _to_numeric(df[column])
    invalid_range = df[column].notna() & ((numeric < 0) | (numeric > 100))
    parse_failed = df[column].notna() & numeric.isna() & df[column].astype("string").str.strip().ne("")

    errors = _row_errors(
        df=df,
        mask=invalid_range,
        rule="percentage_range",
        column=column,
        message="Percentage fields must be between 0 and 100.",
    )

    errors.extend(
        _row_errors(
            df=df,
            mask=parse_failed,
            rule="percentage_parse",
            column=column,
            message="Could not parse percentage legacy value.",
        )
    )

    return errors


def _validate_dates(df: pd.DataFrame, column: str) -> list[RuleError]:
    parsed = _to_datetime(df[column])
    now = pd.Timestamp(datetime.now(timezone.utc) + MAX_FUTURE_SKEW)
    source = df[column].astype("string").str.strip()

    parse_failed = df[column].notna() & source.ne("") & parsed.isna()
    out_of_range = parsed.notna() & ((parsed < MIN_REASONABLE_DATE) | (parsed > now))

    errors = _row_errors(
        df=df,
        mask=parse_failed,
        rule="date_parse",
        column=column,
        message="Could not parse date legacy value.",
    )

    errors.extend(
        _row_errors(
            df=df,
            mask=out_of_range,
            rule="date_reasonable_range",
            column=column,
            message="Date is outside the reasonable dashboard range.",
        )
    )

    return errors


def _validate_discount_consistency(df: pd.DataFrame) -> list[RuleError]:
    errors: list[RuleError] = []
    discount_columns = [c for c in df.columns if _column_matches(c, DISCOUNT_KEYWORDS)]

    base_columns = [
        c
        for c in df.columns
        if _column_matches(c, ("subtotal", "gross", "price", "precio", "amount", "monto", "total"))
        and not _column_matches(c, DISCOUNT_KEYWORDS)
    ]

    for discount_column in discount_columns:
        discount_values = _to_numeric(df[discount_column])
        negative = discount_values < 0

        errors.extend(
            _row_errors(
                df=df,
                mask=negative,
                rule="discount_non_negative",
                column=discount_column,
                message="Discount values cannot be negative.",
            )
        )

        if _column_matches(discount_column, PERCENT_KEYWORDS):
            errors.extend(_validate_percentage(df, discount_column))
            continue

        for base_column in base_columns:
            if base_column == discount_column:
                continue

            base_values = _to_numeric(df[base_column])
            too_large = discount_values.notna() & base_values.notna() & (discount_values > base_values)

            errors.extend(
                _row_errors(
                    df=df,
                    mask=too_large,
                    rule="discount_not_greater_than_base",
                    column=discount_column,
                    message=f"Discount cannot be greater than related base column '{base_column}'.",
                )
            )

    return errors


@dispatcher.register_validator(name="business_rules_validator")
async def validate_business_rules(df: pd.DataFrame) -> dict[str, Any]:
    """
    Validate QueryAgent results before they reach the UI.

    Fallback policy: this first iteration is deterministic and does not call an
    LLM, which keeps latency bounded and avoids network timeouts. If a future
    rule delegates to an LLM, it must use an explicit timeout and return a
    partial/suspicious validation result rather than raising through the request.
    """
    if df is None:
        return {
            "valid": False,
            "errors": [
                RuleError(
                    rule="dataset_required",
                    column="*",
                    row=None,
                    message="Validator expected a pandas DataFrame but received None.",
                ).as_dict()
            ],
        }

    if not isinstance(df, pd.DataFrame):
        return {
            "valid": False,
            "errors": [
                RuleError(
                    rule="dataset_type",
                    column="*",
                    row=None,
                    message=f"Validator expected a pandas DataFrame but received {type(df).__name__}.",
                ).as_dict()
            ],
        }

    if df.empty:
        return {"valid": True, "errors": []}

    errors: list[RuleError] = []

    try:
        for column in df.columns:
            if _column_matches(column, DATE_KEYWORDS):
                errors.extend(_validate_dates(df, column))

            if _column_matches(column, NON_NEGATIVE_NUMERIC_KEYWORDS):
                errors.extend(_validate_non_negative(df, column))

            if _column_matches(column, PERCENT_KEYWORDS):
                errors.extend(_validate_percentage(df, column))

        errors.extend(_validate_discount_consistency(df))

    except Exception as exc:
        logger.exception("Business rules validator failed unexpectedly")
        errors.append(
            RuleError(
                rule="validator_runtime_error",
                column="*",
                row=None,
                message=f"Validator failed defensively: {exc}",
            )
        )

    serialised_errors = [error.as_dict() for error in errors]

    return {
        "valid": len(serialised_errors) == 0,
        "errors": serialised_errors,
    }