from __future__ import annotations

import json
import re
from datetime import date
from math import exp, log
from pathlib import Path

from .io_utils import read_csv_rows, write_csv_rows, write_json


LISTINGS_FIELDS = [
    "sku_id",
    "platform",
    "brand",
    "list_price",
    "monthly_sales_estimate",
    "rating",
    "review_count",
]

TRANSACTIONS_FIELDS = [
    "sku_id",
    "platform",
    "date",
    "list_price",
    "actual_price",
    "units",
]

CHANNEL_FIELDS = [
    "channel",
    "visits",
    "orders",
    "revenue",
    "ad_spend",
]

PART2_LISTING_SNAPSHOT_FIELDS = [
    "platform",
    "listing_id",
    "canonical_sku",
    "brand",
    "seller_id",
    "captured_at",
    "list_price",
    "sale_price",
    "currency",
    "shipping_fee",
    "rating_avg",
    "review_count",
    "sold_count_window",
    "sales_rank",
    "active_flag",
    "seller_type",
    "fulfillment_type",
]

PART2_SOLD_TRANSACTION_FIELDS = [
    "platform",
    "sold_id",
    "listing_id",
    "canonical_sku",
    "sold_at",
    "transaction_price",
    "shipping_fee",
    "units",
    "seller_type",
]

PART2_PRODUCT_CATALOG_FIELDS = [
    "canonical_sku",
    "brand",
    "category_path",
    "title",
    "attribute_tokens",
    "first_available_date",
]

PART2_REVIEW_FIELDS = [
    "platform",
    "canonical_sku",
    "review_id",
    "review_date",
    "rating",
    "review_text",
]

PART3_SUPPLIER_FIELDS = [
    "supplier_id",
    "supplier_name",
    "supplier_type",
    "region",
    "factory_flag",
    "oem_flag",
    "odm_flag",
    "main_category",
    "moq",
    "sample_days",
    "production_days",
    "capacity_score",
    "compliance_support_score",
]

PART3_RFQ_FIELDS = [
    "supplier_id",
    "sku_version",
    "incoterm",
    "moq_tier",
    "unit_price",
    "sample_fee",
    "tooling_fee",
    "packaging_cost",
    "customization_cost",
    "currency",
    "quote_date",
    "quote_id",
    "product_spec_key",
    "price_breaks_json",
    "lead_time_days",
    "payment_terms",
    "certifications_list",
    "quote_valid_until",
    "source_confidence",
    "captured_at",
    "included_items",
]

PART3_COMPLIANCE_FIELDS = [
    "market",
    "category",
    "requirement_type",
    "requirement_name",
    "mandatory_flag",
    "estimated_cost",
    "estimated_days",
    "risk_level",
    "notes",
]

PART3_LOGISTICS_FIELDS = [
    "route_id",
    "origin",
    "destination",
    "shipping_mode",
    "incoterm",
    "quote_basis",
    "cost_value",
    "currency",
    "lead_time_days",
    "volatility_score",
    "quote_date",
]

PART3_TARIFF_FIELDS = [
    "market",
    "hs_code",
    "base_duty_rate",
    "additional_duty_rate",
    "brokerage_fee",
    "port_fee",
    "effective_date",
]

PART3_SHIPMENT_FIELDS = [
    "shipment_id",
    "supplier_id",
    "shipping_mode",
    "etd",
    "eta",
    "customs_release_date",
    "warehouse_received_date",
    "sellable_date",
    "delay_days",
    "issue_type",
    "node",
    "delay_reason",
    "cost_component",
]

ATTRIBUTE_KEYWORDS = {
    "dual fuel": "dual_fuel",
    "inverter": "inverter",
    "quiet": "quiet",
    "electric start": "electric_start",
    "remote start": "remote_start",
    "co sensor": "co_sensor",
    "co-sensor": "co_sensor",
    "co safe": "co_sensor",
    "parallel": "parallel_ready",
    "wheel kit": "wheel_kit",
    "portable": "portable",
    "compact": "compact",
    "manual start": "manual_start",
    "budget": "budget",
    "waterproof": "waterproof",
    "led": "led",
    "steel": "steel",
    "leather": "leather",
    "quick release": "quick_release",
    "fitment": "fitment",
}


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    return read_csv_rows(path)


def _write_csv(path: str | Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    write_csv_rows(path, fieldnames, rows)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _lookup(row: dict[str, str], aliases: tuple[str, ...]) -> str:
    normalized = {_slug(key): value for key, value in row.items()}
    for alias in aliases:
        value = normalized.get(_slug(alias), "")
        if value not in ("", None):
            return str(value).strip()
    return ""


def _clean_currency(value: str) -> str:
    cleaned = re.sub(r"[^0-9.\-]+", "", value or "")
    return cleaned or "0"


def _clean_int(value: str) -> str:
    cleaned = re.sub(r"[^0-9\-]+", "", value or "")
    return cleaned or "0"


def _clean_float(value: str) -> str:
    cleaned = re.sub(r"[^0-9.\-]+", "", value or "")
    return cleaned or "0"


def _clean_percent(value: str) -> float:
    cleaned = re.sub(r"[^0-9.\-]+", "", value or "")
    if not cleaned:
        return 0.0
    return float(cleaned) / 100


def _clean_confidence_score(value: str, default: float = 0.72) -> str:
    cleaned = re.sub(r"[^0-9.\-]+", "", value or "")
    if not cleaned:
        return f"{default:.2f}"
    numeric = float(cleaned)
    if numeric > 1:
        numeric /= 100
    numeric = max(0.0, min(1.0, numeric))
    return f"{numeric:.2f}"


def _bool_flag(value: str, default: str = "true") -> str:
    normalized = str(value or default).strip().lower()
    return "true" if normalized in {"1", "true", "yes", "y", "active", "in stock"} else "false"


def _default_capture_date(value: str | None) -> str:
    return value or date.today().isoformat()


def _supplier_id_from_row(row: dict[str, str]) -> str:
    supplier_id = _lookup(row, ("supplier id", "vendor id", "id", "factory id"))
    if supplier_id:
        return supplier_id
    supplier_name = _lookup(row, ("supplier name", "vendor name", "supplier", "vendor"))
    if supplier_name:
        return f"S-{_slug(supplier_name)[:12]}"
    return ""


def _normalize_supplier_type(value: str, factory_flag: str = "") -> str:
    normalized = _slug(value)
    if normalized in {"factory", "manufacturer", "oem", "odm"}:
        return "factory"
    if normalized in {"trader", "tradingcompany", "trading", "exportcompany"}:
        return "trader"
    if normalized in {"wholesaler", "wholesale", "stockist", "distributor"}:
        return "wholesaler"
    if _bool_flag(factory_flag) == "true":
        return "factory"
    return "unknown"


def _normalize_incoterm(value: str) -> str:
    normalized = str(value or "").strip().upper()
    if normalized in {"EXW", "FOB", "CIF", "DDP"}:
        return normalized
    return normalized or "EXW"


def _normalize_risk_level(value: str) -> str:
    normalized = _slug(value)
    if normalized in {"high", "critical", "severe"}:
        return "high"
    if normalized in {"medium", "moderate", "mid"}:
        return "medium"
    if normalized in {"low", "minor"}:
        return "low"
    return "medium"


def _normalize_shipping_mode(value: str) -> str:
    normalized = _slug(value)
    if "seafcl" in normalized or normalized in {"fcl", "oceanfcl"}:
        return "sea_fcl"
    if "sealcl" in normalized or normalized in {"lcl", "oceanlcl"}:
        return "sea_lcl"
    if "air" in normalized:
        return "air"
    if normalized in {"parcel", "express", "courier", "parcelddp", "expressddp"}:
        return "parcel_ddp"
    return value or "unknown"


def _infer_seller_type(brand: str, seller_name: str, hint: str) -> str:
    normalized_hint = _slug(hint)
    if normalized_hint in {"brandowner", "brand", "manufacturer", "official"}:
        return "brand_owner"
    if normalized_hint in {"reseller", "dealer", "retailer", "merchant"}:
        return "reseller"
    if brand and seller_name and _slug(brand) and _slug(brand) in _slug(seller_name):
        return "brand_owner"
    return "reseller"


def _infer_fulfillment_type(value: str, fallback: str = "unknown") -> str:
    normalized = _slug(value)
    if normalized in {"fba", "amazonfba"}:
        return "FBA"
    if normalized in {"fbm", "merchantfulfilled", "merchant"}:
        return "merchant_fulfilled"
    if normalized in {"sellerfulfilled", "seller"}:
        return "seller_fulfilled"
    return fallback


def _extract_attribute_tokens(*texts: str) -> str:
    source = " ".join(text for text in texts if text).lower()
    tokens = []
    for phrase, token in ATTRIBUTE_KEYWORDS.items():
        if phrase in source and token not in tokens:
            tokens.append(token)
    return "|".join(tokens)


def _fit_rank_sales_curve(rows: list[dict[str, str]]) -> dict[str, float]:
    pairs = []
    for row in rows:
        units = _clean_int(_lookup(row, ("bought past month", "bought_past_month", "monthly sales", "estimated sales")))
        rank = _clean_int(_lookup(row, ("root bs rank", "root_bs_rank", "bs rank", "bs_rank", "rank")))
        units_value = int(units or "0")
        rank_value = int(rank or "0")
        if units_value > 0 and rank_value > 0:
            pairs.append((log(rank_value), log(units_value)))

    if len(pairs) < 10:
        return {"intercept": log(30), "slope": -0.55, "sample_size": len(pairs)}

    x_mean = sum(x for x, _ in pairs) / len(pairs)
    y_mean = sum(y for _, y in pairs) / len(pairs)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in pairs)
    denominator = sum((x - x_mean) ** 2 for x, _ in pairs)
    if denominator == 0:
        return {"intercept": log(30), "slope": -0.55, "sample_size": len(pairs)}
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    return {"intercept": intercept, "slope": slope, "sample_size": len(pairs)}


def _estimate_units_from_rank(rank: str, fitted_curve: dict[str, float]) -> str:
    rank_value = int(_clean_int(rank) or "0")
    if rank_value <= 0:
        return "0"
    estimate = exp(
        fitted_curve.get("intercept", log(30))
        + fitted_curve.get("slope", -0.55) * log(rank_value)
    )
    estimate = max(1, min(int(round(estimate)), 5000))
    return str(estimate)


def _review_rows_from_text(
    platform: str,
    canonical_sku: str,
    review_text_blob: str,
    review_date: str,
    rating: str,
    prefix: str,
) -> list[dict[str, str]]:
    if not review_text_blob:
        return []
    rows = []
    snippets = [snippet.strip() for snippet in review_text_blob.split("||") if snippet.strip()]
    for index, snippet in enumerate(snippets, start=1):
        rows.append(
            {
                "platform": platform,
                "canonical_sku": canonical_sku,
                "review_id": f"{prefix}-R{index}",
                "review_date": review_date,
                "rating": _clean_float(rating),
                "review_text": snippet,
            }
        )
    return rows


def _write_part2_bundle(
    output_dir: str | Path,
    listing_rows: list[dict[str, str]],
    sold_rows: list[dict[str, str]],
    product_rows: list[dict[str, str]],
    review_rows: list[dict[str, str]],
    manifest: dict,
) -> dict[str, str | int]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "listing_snapshots.csv", PART2_LISTING_SNAPSHOT_FIELDS, listing_rows)
    _write_csv(output_dir / "sold_transactions.csv", PART2_SOLD_TRANSACTION_FIELDS, sold_rows)
    _write_csv(output_dir / "product_catalog.csv", PART2_PRODUCT_CATALOG_FIELDS, product_rows)
    _write_csv(output_dir / "reviews.csv", PART2_REVIEW_FIELDS, review_rows)
    manifest_path = write_json(output_dir / "source_manifest.json", manifest)
    return {
        "output_dir": str(output_dir),
        "listing_snapshots": len(listing_rows),
        "sold_transactions": len(sold_rows),
        "product_catalog": len(product_rows),
        "reviews": len(review_rows),
        "manifest_json": str(manifest_path),
    }


def _merge_product_catalog_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for row in rows:
        canonical_sku = row["canonical_sku"]
        current = merged.get(canonical_sku)
        if current is None:
            merged[canonical_sku] = dict(row)
            continue
        for key, value in row.items():
            if value and not current.get(key):
                current[key] = value
    return list(merged.values())


def normalize_amazon_listings_export(
    raw_path: str | Path,
    output_path: str | Path,
) -> dict[str, str | int]:
    raw_rows = _read_csv(raw_path)
    normalized_rows = []

    for row in raw_rows:
        sku_id = _lookup(row, ("asin", "sku", "product id"))
        if not sku_id:
            continue
        normalized_rows.append(
            {
                "sku_id": sku_id,
                "platform": "Amazon",
                "brand": _lookup(row, ("brand", "brand name", "manufacturer")) or "Unknown",
                "list_price": _clean_currency(
                    _lookup(row, ("price", "buy box price", "current price"))
                ),
                "monthly_sales_estimate": _clean_int(
                    _lookup(row, ("monthly sales", "estimated sales", "sales"))
                ),
                "rating": _clean_float(_lookup(row, ("review rating", "rating", "stars"))),
                "review_count": _clean_int(
                    _lookup(row, ("review count", "reviews", "ratings total"))
                ),
            }
        )

    _write_csv(output_path, LISTINGS_FIELDS, normalized_rows)
    return {
        "template": "amazon_listings",
        "target_table": "listings",
        "rows_in": len(raw_rows),
        "rows_out": len(normalized_rows),
    }


def normalize_ebay_transactions_export(
    raw_path: str | Path,
    output_path: str | Path,
) -> dict[str, str | int]:
    raw_rows = _read_csv(raw_path)
    normalized_rows = []

    for row in raw_rows:
        sku_id = _lookup(row, ("item id", "listing id", "sku"))
        actual_price = _lookup(row, ("sold price", "sale price", "sold for"))
        if not sku_id or not actual_price:
            continue
        list_price = _lookup(row, ("list price", "original price", "start price")) or actual_price
        normalized_rows.append(
            {
                "sku_id": sku_id,
                "platform": "eBay",
                "date": _lookup(row, ("sale date", "date sold", "transaction date")),
                "list_price": _clean_currency(list_price),
                "actual_price": _clean_currency(actual_price),
                "units": _clean_int(_lookup(row, ("units sold", "quantity sold", "quantity"))),
            }
        )

    _write_csv(output_path, TRANSACTIONS_FIELDS, normalized_rows)
    return {
        "template": "ebay_transactions",
        "target_table": "transactions",
        "rows_in": len(raw_rows),
        "rows_out": len(normalized_rows),
    }


def normalize_tiktok_channels_export(
    raw_path: str | Path,
    output_path: str | Path,
) -> dict[str, str | int]:
    raw_rows = _read_csv(raw_path)

    total_visits = 0
    total_orders = 0
    total_revenue = 0.0
    total_ad_spend = 0.0

    for row in raw_rows:
        total_visits += int(_clean_int(_lookup(row, ("visitors", "views", "product views", "traffic"))))
        total_orders += int(_clean_int(_lookup(row, ("paid orders", "orders", "order count"))))
        total_revenue += float(_clean_currency(_lookup(row, ("gmv", "revenue", "sales amount"))))
        total_ad_spend += float(_clean_currency(_lookup(row, ("ad spend", "spend", "ads cost"))))

    normalized_rows = [
        {
            "channel": "TikTok Shop",
            "visits": str(total_visits),
            "orders": str(total_orders),
            "revenue": f"{total_revenue:.2f}",
            "ad_spend": f"{total_ad_spend:.2f}",
        }
    ]

    _write_csv(output_path, CHANNEL_FIELDS, normalized_rows)
    return {
        "template": "tiktok_channels",
        "target_table": "channels",
        "rows_in": len(raw_rows),
        "rows_out": len(normalized_rows),
    }


def normalize_tiktok_listings_export(
    raw_path: str | Path,
    output_path: str | Path,
) -> dict[str, str | int]:
    raw_rows = _read_csv(raw_path)
    normalized_rows = []

    for row in raw_rows:
        sku_id = _lookup(row, ("id", "listing id", "product id"))
        if not sku_id:
            continue
        normalized_rows.append(
            {
                "sku_id": sku_id,
                "platform": "TikTok Shop",
                "brand": _lookup(row, ("seller_name", "brand", "shop name")) or "Unknown",
                "list_price": _clean_currency(_lookup(row, ("price", "sale price", "current price"))),
                "monthly_sales_estimate": _clean_int(
                    _lookup(row, ("sold_count", "sales", "sold", "order count"))
                ),
                "rating": _clean_float(_lookup(row, ("rating", "review rating", "stars"))),
                "review_count": _clean_int(_lookup(row, ("review_count", "reviews", "ratings total"))),
            }
        )

    _write_csv(output_path, LISTINGS_FIELDS, normalized_rows)
    return {
        "template": "tiktok_listings",
        "target_table": "listings",
        "rows_in": len(raw_rows),
        "rows_out": len(normalized_rows),
    }


def normalize_amazon_part2_export(
    raw_path: str | Path,
    output_dir: str | Path,
    capture_date: str | None = None,
) -> dict[str, str | int]:
    raw_rows = _read_csv(raw_path)
    listing_rows = []
    sold_rows = []
    product_rows = []
    review_rows = []
    capture_date = _default_capture_date(capture_date)
    fitted_curve = _fit_rank_sales_curve(raw_rows)

    for row in raw_rows:
        listing_id = _lookup(row, ("asin", "listing id", "sku", "product id"))
        if not listing_id:
            continue
        brand = _lookup(row, ("brand", "brand name", "manufacturer")) or "Unknown"
        seller_name = _lookup(row, ("seller name", "seller", "merchant"))
        seller_type = _infer_seller_type(brand, seller_name, _lookup(row, ("seller type",)))
        list_price = _clean_currency(
            _lookup(row, ("list price", "msrp", "original price", "initial price", "initial_price", "price"))
        )
        sale_price = _clean_currency(
            _lookup(row, ("sale price", "current price", "buy box price", "final price", "final_price", "price"))
        )
        monthly_sales = _clean_int(
            _lookup(
                row,
                (
                    "monthly sales",
                    "estimated sales",
                    "sales",
                    "bought past month",
                    "bought_past_month",
                ),
            )
        )
        if int(monthly_sales or "0") <= 0:
            monthly_sales = _estimate_units_from_rank(
                _lookup(row, ("root bs rank", "root_bs_rank", "bs rank", "bs_rank", "rank")),
                fitted_curve,
            )
        canonical_sku = _lookup(row, ("canonical sku", "asin", "mpn", "upc")) or listing_id
        title = _lookup(row, ("title", "product title", "name"))
        category_path = _lookup(row, ("category", "category path", "browse node", "categories"))
        attribute_tokens = _extract_attribute_tokens(
            title,
            _lookup(row, ("attributes", "bullets", "bullet points", "features", "product_details")),
        )
        rating = _clean_float(_lookup(row, ("review rating", "rating", "stars")))
        review_count = _clean_int(_lookup(row, ("review count", "reviews", "reviews_count", "ratings total")))
        fulfillment_type = _infer_fulfillment_type(_lookup(row, ("fulfillment", "fulfilment", "ship by")))
        observed_capture_date = _lookup(row, ("capture date", "captured at", "timestamp")) or capture_date
        first_available_date = _lookup(row, ("date first available", "date_first_available"))

        listing_rows.append(
            {
                "platform": "Amazon",
                "listing_id": listing_id,
                "canonical_sku": canonical_sku,
                "brand": brand,
                "seller_id": _lookup(row, ("seller id", "merchant id")) or seller_name or brand,
                "captured_at": observed_capture_date,
                "list_price": list_price,
                "sale_price": sale_price,
                "currency": _lookup(row, ("currency",)) or "USD",
                "shipping_fee": _clean_currency(_lookup(row, ("shipping", "shipping fee"))),
                "rating_avg": rating,
                "review_count": review_count,
                "sold_count_window": monthly_sales,
                "sales_rank": _clean_int(
                    _lookup(row, ("sales rank", "bsr", "root bs rank", "root_bs_rank", "bs rank", "bs_rank", "rank"))
                ),
                "active_flag": _bool_flag(
                    _lookup(row, ("active", "status", "in stock", "availability", "is_available")) or "true"
                ),
                "seller_type": seller_type,
                "fulfillment_type": fulfillment_type,
            }
        )
        product_rows.append(
            {
                "canonical_sku": canonical_sku,
                "brand": brand,
                "category_path": category_path,
                "title": title,
                "attribute_tokens": attribute_tokens,
                "first_available_date": first_available_date,
            }
        )
        if int(monthly_sales or "0") > 0:
            sold_rows.append(
                {
                    "platform": "Amazon",
                    "sold_id": f"proxy-{listing_id}",
                    "listing_id": listing_id,
                    "canonical_sku": canonical_sku,
                    "sold_at": observed_capture_date[:10],
                    "transaction_price": sale_price,
                    "shipping_fee": _clean_currency(_lookup(row, ("shipping", "shipping fee"))),
                    "units": monthly_sales,
                    "seller_type": seller_type,
                }
            )
        review_rows.extend(
            _review_rows_from_text(
                "Amazon",
                canonical_sku,
                _lookup(row, ("review snippets", "review sample", "review text", "top reviews", "top_review")),
                observed_capture_date[:10],
                rating,
                listing_id,
            )
        )

    return _write_part2_bundle(
        output_dir,
        listing_rows,
        sold_rows,
        _merge_product_catalog_rows(product_rows),
        review_rows,
        {
            "platform": "Amazon",
            "transaction_mode": "bought_past_month_plus_rank_calibrated_proxy",
            "capture_date": capture_date,
            "rows_in": len(raw_rows),
            "rank_sales_curve": {
                "sample_size": fitted_curve.get("sample_size", 0),
                "intercept": round(fitted_curve.get("intercept", 0.0), 4),
                "slope": round(fitted_curve.get("slope", 0.0), 4),
            },
        },
    )


def normalize_ebay_part2_export(
    raw_path: str | Path,
    output_dir: str | Path,
) -> dict[str, str | int]:
    raw_rows = _read_csv(raw_path)
    listing_rows = []
    sold_rows = []
    product_rows = []
    review_rows = []

    for row in raw_rows:
        listing_id = _lookup(row, ("item id", "listing id", "sku"))
        sold_price = _lookup(row, ("sold price", "sale price", "sold for"))
        if not listing_id or not sold_price:
            continue
        brand = _lookup(row, ("brand name", "brand")) or "Unknown"
        seller_name = _lookup(row, ("seller name", "seller"))
        seller_type = _infer_seller_type(brand, seller_name, _lookup(row, ("seller type",)))
        sale_date = _lookup(row, ("sale date", "date sold", "transaction date")) or date.today().isoformat()
        list_price = _clean_currency(_lookup(row, ("list price", "original price", "start price")) or sold_price)
        title = _lookup(row, ("title", "item title", "name"))
        canonical_sku = _lookup(row, ("canonical sku", "mpn", "item id")) or listing_id
        category_path = _lookup(row, ("category", "category path"))
        attribute_tokens = _extract_attribute_tokens(
            title,
            _lookup(row, ("attributes", "item specifics", "features")),
        )
        rating = _clean_float(_lookup(row, ("rating", "review rating", "stars")))
        review_count = _clean_int(_lookup(row, ("review count", "reviews")))
        units = _clean_int(_lookup(row, ("units sold", "quantity sold", "quantity")) or "1")
        shipping_fee = _clean_currency(_lookup(row, ("shipping", "shipping fee")))

        listing_rows.append(
            {
                "platform": "eBay",
                "listing_id": listing_id,
                "canonical_sku": canonical_sku,
                "brand": brand,
                "seller_id": _lookup(row, ("seller id",)) or seller_name or brand,
                "captured_at": sale_date,
                "list_price": list_price,
                "sale_price": _clean_currency(sold_price),
                "currency": _lookup(row, ("currency",)) or "USD",
                "shipping_fee": shipping_fee,
                "rating_avg": rating,
                "review_count": review_count,
                "sold_count_window": units,
                "sales_rank": "0",
                "active_flag": "false",
                "seller_type": seller_type,
                "fulfillment_type": _infer_fulfillment_type(
                    _lookup(row, ("fulfillment", "shipping method")),
                    fallback="merchant_fulfilled",
                ),
            }
        )
        sold_rows.append(
            {
                "platform": "eBay",
                "sold_id": f"{listing_id}-{sale_date}",
                "listing_id": listing_id,
                "canonical_sku": canonical_sku,
                "sold_at": sale_date,
                "transaction_price": _clean_currency(sold_price),
                "shipping_fee": shipping_fee,
                "units": units,
                "seller_type": seller_type,
            }
        )
        product_rows.append(
            {
                "canonical_sku": canonical_sku,
                "brand": brand,
                "category_path": category_path,
                "title": title,
                "attribute_tokens": attribute_tokens,
            }
        )
        review_rows.extend(
            _review_rows_from_text(
                "eBay",
                canonical_sku,
                _lookup(row, ("review snippets", "review sample", "review text")),
                sale_date,
                rating,
                listing_id,
            )
        )

    return _write_part2_bundle(
        output_dir,
        listing_rows,
        sold_rows,
        _merge_product_catalog_rows(product_rows),
        review_rows,
        {
            "platform": "eBay",
            "transaction_mode": "observed_transactions",
            "rows_in": len(raw_rows),
        },
    )


def normalize_tiktok_part2_export(
    raw_path: str | Path,
    output_dir: str | Path,
    capture_date: str | None = None,
) -> dict[str, str | int]:
    raw_rows = _read_csv(raw_path)
    listing_rows = []
    sold_rows = []
    product_rows = []
    review_rows = []
    capture_date = _default_capture_date(capture_date)

    for row in raw_rows:
        listing_id = _lookup(row, ("id", "listing id", "product id"))
        if not listing_id:
            continue
        brand = _lookup(row, ("brand", "seller_name", "shop name")) or "Unknown"
        title = _lookup(row, ("title", "name"))
        discount_rate = _clean_percent(_lookup(row, ("discount", "discount rate")))
        sale_price = float(_clean_currency(_lookup(row, ("price", "sale price", "current price"))))
        if discount_rate and discount_rate < 1:
            list_price_value = sale_price / (1 - discount_rate)
        else:
            list_price_value = sale_price
        list_price = f"{list_price_value:.2f}"
        sold_count = _clean_int(_lookup(row, ("sold_count", "sales", "sold", "order count")))
        rating = _clean_float(_lookup(row, ("rating", "review rating", "stars")))
        review_count = _clean_int(_lookup(row, ("review_count", "reviews", "ratings total")))
        canonical_sku = _lookup(row, ("canonical sku", "id")) or listing_id
        attribute_tokens = _extract_attribute_tokens(
            title,
            _lookup(row, ("attributes", "features", "tags")),
        )
        seller_name = _lookup(row, ("seller_name", "shop name"))
        seller_type = _infer_seller_type(brand, seller_name, _lookup(row, ("seller type",)))

        listing_rows.append(
            {
                "platform": "TikTok Shop",
                "listing_id": listing_id,
                "canonical_sku": canonical_sku,
                "brand": brand,
                "seller_id": _lookup(row, ("seller_id", "shop_id")) or seller_name or brand,
                "captured_at": _lookup(row, ("capture date", "captured at")) or capture_date,
                "list_price": list_price,
                "sale_price": f"{sale_price:.2f}",
                "currency": _lookup(row, ("currency",)) or "USD",
                "shipping_fee": _clean_currency(_lookup(row, ("shipping", "shipping fee"))),
                "rating_avg": rating,
                "review_count": review_count,
                "sold_count_window": sold_count,
                "sales_rank": _clean_int(_lookup(row, ("sales rank", "rank"))),
                "active_flag": _bool_flag(_lookup(row, ("active", "status")) or "true"),
                "seller_type": seller_type,
                "fulfillment_type": _infer_fulfillment_type(
                    _lookup(row, ("fulfillment", "shipping method")),
                    fallback="seller_fulfilled",
                ),
            }
        )
        product_rows.append(
            {
                "canonical_sku": canonical_sku,
                "brand": brand,
                "category_path": _lookup(row, ("category", "category path")),
                "title": title,
                "attribute_tokens": attribute_tokens,
            }
        )
        if int(sold_count or "0") > 0:
            sold_rows.append(
                {
                    "platform": "TikTok Shop",
                    "sold_id": f"proxy-{listing_id}",
                    "listing_id": listing_id,
                    "canonical_sku": canonical_sku,
                    "sold_at": capture_date,
                    "transaction_price": f"{sale_price:.2f}",
                    "shipping_fee": _clean_currency(_lookup(row, ("shipping", "shipping fee"))),
                    "units": sold_count,
                    "seller_type": seller_type,
                }
            )
        review_rows.extend(
            _review_rows_from_text(
                "TikTok Shop",
                canonical_sku,
                _lookup(row, ("review snippets", "review sample", "review text", "top reviews")),
                capture_date,
                rating,
                listing_id,
            )
        )

    return _write_part2_bundle(
        output_dir,
        listing_rows,
        sold_rows,
        _merge_product_catalog_rows(product_rows),
        review_rows,
        {
            "platform": "TikTok Shop",
            "transaction_mode": "proxy_sold_count",
            "capture_date": capture_date,
            "rows_in": len(raw_rows),
        },
    )


def combine_part2_bundles(
    bundle_dirs: list[str | Path],
    output_dir: str | Path,
) -> dict[str, str | int]:
    listing_rows = []
    sold_rows = []
    product_rows = []
    review_rows = []

    for bundle_dir in bundle_dirs:
        bundle_dir = Path(bundle_dir)
        listing_rows.extend(_read_csv(bundle_dir / "listing_snapshots.csv"))
        sold_rows.extend(_read_csv(bundle_dir / "sold_transactions.csv"))
        product_rows.extend(_read_csv(bundle_dir / "product_catalog.csv"))
        review_rows.extend(_read_csv(bundle_dir / "reviews.csv"))

    return _write_part2_bundle(
        output_dir,
        listing_rows,
        sold_rows,
        _merge_product_catalog_rows(product_rows),
        review_rows,
        {
            "source_bundle_count": len(bundle_dirs),
            "mode": "combined_part2_bundle",
        },
    )


def normalize_part3_suppliers_export(
    raw_path: str | Path,
    output_path: str | Path,
) -> dict[str, str | int]:
    raw_rows = _read_csv(raw_path)
    normalized_rows = []

    for row in raw_rows:
        supplier_name = _lookup(row, ("supplier name", "vendor name", "supplier", "vendor"))
        supplier_id = _supplier_id_from_row(row)
        if not supplier_id or not supplier_name:
            continue
        factory_flag = _bool_flag(
            _lookup(row, ("factory flag", "direct factory", "factory", "manufacturer"))
            or _lookup(row, ("company type", "supplier type")),
            default="false",
        )
        normalized_rows.append(
            {
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
                "supplier_type": _normalize_supplier_type(
                    _lookup(row, ("supplier type", "company type", "vendor type")),
                    factory_flag,
                ),
                "region": _lookup(row, ("region", "province", "location", "city")) or "Unknown",
                "factory_flag": factory_flag,
                "oem_flag": _bool_flag(_lookup(row, ("oem flag", "oem service", "oem")), default="false"),
                "odm_flag": _bool_flag(_lookup(row, ("odm flag", "odm service", "odm")), default="false"),
                "main_category": _lookup(row, ("main category", "product line", "main product")) or "",
                "moq": _clean_int(_lookup(row, ("moq", "min order qty", "minimum order quantity"))),
                "sample_days": _clean_int(_lookup(row, ("sample days", "sample lead time", "sample lead time days"))),
                "production_days": _clean_int(
                    _lookup(row, ("production days", "production lead time", "lead time"))
                ),
                "capacity_score": _clean_float(_lookup(row, ("capacity score", "capacity", "capacity rating"))),
                "compliance_support_score": _clean_float(
                    _lookup(row, ("compliance support score", "compliance score", "compliance support"))
                ),
            }
        )

    _write_csv(output_path, PART3_SUPPLIER_FIELDS, normalized_rows)
    return {
        "template": "part3_suppliers",
        "target_table": "suppliers",
        "rows_in": len(raw_rows),
        "rows_out": len(normalized_rows),
    }


def normalize_part3_rfq_export(
    raw_path: str | Path,
    output_path: str | Path,
) -> dict[str, str | int]:
    raw_rows = _read_csv(raw_path)
    normalized_rows = []

    for index, row in enumerate(raw_rows, start=1):
        supplier_id = _supplier_id_from_row(row)
        sku_version = _lookup(row, ("sku version", "model", "sku", "product model"))
        if not supplier_id or not sku_version:
            continue
        moq_tier = _clean_int(_lookup(row, ("moq", "moq tier", "min order qty", "quantity")))
        unit_price = _clean_currency(_lookup(row, ("unit price", "quote price", "price", "quoted unit price")))
        sample_fee = _clean_currency(_lookup(row, ("sample fee", "sample charge", "sample cost")))
        tooling_fee = _clean_currency(_lookup(row, ("tooling fee", "tooling cost", "mold fee", "mould fee")))
        packaging_cost = _clean_currency(_lookup(row, ("packaging cost", "packing cost", "package cost")))
        customization_cost = _clean_currency(
            _lookup(row, ("customization cost", "custom logo cost", "custom cost", "branding cost"))
        )
        included_items = _lookup(row, ("included items", "quote included items", "included scope"))
        if not included_items:
            inferred_items = ["unit_price"]
            if packaging_cost not in {"", "0", "0.0"}:
                inferred_items.append("packaging")
            if customization_cost not in {"", "0", "0.0"}:
                inferred_items.append("customization")
            if tooling_fee not in {"", "0", "0.0"}:
                inferred_items.append("tooling")
            if sample_fee not in {"", "0", "0.0"}:
                inferred_items.append("sample")
            included_items = ",".join(inferred_items)
        price_breaks = _lookup(row, ("price breaks", "price ladder", "tiers json", "price breaks json"))
        if not price_breaks:
            price_breaks = json.dumps(
                [{"moq": int(moq_tier or 0), "unit_price": float(unit_price or 0)}],
                ensure_ascii=False,
            )
        normalized_rows.append(
            {
                "supplier_id": supplier_id,
                "sku_version": sku_version,
                "incoterm": _normalize_incoterm(_lookup(row, ("incoterm", "trade term", "trade terms"))),
                "moq_tier": moq_tier,
                "unit_price": unit_price,
                "sample_fee": sample_fee,
                "tooling_fee": tooling_fee,
                "packaging_cost": packaging_cost,
                "customization_cost": customization_cost,
                "currency": _lookup(row, ("currency",)) or "USD",
                "quote_date": _lookup(row, ("quote date", "date", "quoted at")) or date.today().isoformat(),
                "quote_id": _lookup(row, ("quote id", "rfq id", "id")) or f"Q{index:04d}",
                "product_spec_key": _lookup(row, ("product spec key", "spec key", "product spec")) or sku_version,
                "price_breaks_json": price_breaks,
                "lead_time_days": _clean_int(_lookup(row, ("lead time days", "quote lead time", "lead time"))),
                "payment_terms": _lookup(row, ("payment terms", "payment term", "payment")) or "",
                "certifications_list": _lookup(
                    row,
                    ("certifications", "certifications list", "certificates", "existing certs"),
                ) or "",
                "quote_valid_until": _lookup(row, ("quote valid until", "valid until", "expiry date")) or "",
                "source_confidence": _clean_confidence_score(
                    _lookup(row, ("source confidence", "confidence", "quote confidence"))
                ),
                "captured_at": _lookup(row, ("captured at", "captured date", "created at"))
                or _lookup(row, ("quote date", "date", "quoted at"))
                or date.today().isoformat(),
                "included_items": included_items,
            }
        )

    _write_csv(output_path, PART3_RFQ_FIELDS, normalized_rows)
    return {
        "template": "part3_rfq",
        "target_table": "rfq_quotes",
        "rows_in": len(raw_rows),
        "rows_out": len(normalized_rows),
    }


def normalize_part3_compliance_export(
    raw_path: str | Path,
    output_path: str | Path,
) -> dict[str, str | int]:
    raw_rows = _read_csv(raw_path)
    normalized_rows = []

    for row in raw_rows:
        requirement_name = _lookup(row, ("requirement name", "requirement", "rule", "certification"))
        market = _lookup(row, ("market", "country market")) or "US"
        if not requirement_name:
            continue
        normalized_rows.append(
            {
                "market": market,
                "category": _lookup(row, ("category", "product category")) or "",
                "requirement_type": _lookup(row, ("requirement type", "type")) or "other",
                "requirement_name": requirement_name,
                "mandatory_flag": _bool_flag(
                    _lookup(row, ("mandatory", "mandatory flag", "required")),
                    default="false",
                ),
                "estimated_cost": _clean_currency(_lookup(row, ("estimated cost", "estimated cost usd", "cost"))),
                "estimated_days": _clean_int(_lookup(row, ("estimated days", "days", "lead time days"))),
                "risk_level": _normalize_risk_level(_lookup(row, ("risk level", "risk", "severity"))),
                "notes": _lookup(row, ("notes", "comment", "remarks")),
            }
        )

    _write_csv(output_path, PART3_COMPLIANCE_FIELDS, normalized_rows)
    return {
        "template": "part3_compliance",
        "target_table": "compliance_requirements",
        "rows_in": len(raw_rows),
        "rows_out": len(normalized_rows),
    }


def normalize_part3_logistics_export(
    raw_path: str | Path,
    output_path: str | Path,
) -> dict[str, str | int]:
    raw_rows = _read_csv(raw_path)
    normalized_rows = []

    for row in raw_rows:
        origin = _lookup(row, ("origin", "origin port", "origin city"))
        destination = _lookup(row, ("destination", "destination warehouse", "destination port"))
        shipping_mode = _normalize_shipping_mode(_lookup(row, ("shipping mode", "shipping method", "mode")))
        if not origin or not destination or not shipping_mode:
            continue
        route_id = _lookup(row, ("route id", "route code", "lane id"))
        if not route_id:
            route_id = f"R-{_slug(origin)}-{_slug(destination)}-{_slug(shipping_mode)}"
        normalized_rows.append(
            {
                "route_id": route_id,
                "origin": origin,
                "destination": destination,
                "shipping_mode": shipping_mode,
                "incoterm": _normalize_incoterm(_lookup(row, ("incoterm", "trade term", "trade terms"))),
                "quote_basis": _lookup(row, ("quote basis", "basis")) or "per_unit",
                "cost_value": _clean_currency(_lookup(row, ("cost value", "unit freight", "freight", "quote price"))),
                "currency": _lookup(row, ("currency",)) or "USD",
                "lead_time_days": _clean_int(_lookup(row, ("lead time days", "lead time", "days"))),
                "volatility_score": _clean_float(_lookup(row, ("volatility score", "volatility", "variance score")) or "0.2"),
                "quote_date": _lookup(row, ("quote date", "date", "quoted at")) or date.today().isoformat(),
            }
        )

    _write_csv(output_path, PART3_LOGISTICS_FIELDS, normalized_rows)
    return {
        "template": "part3_logistics",
        "target_table": "logistics_quotes",
        "rows_in": len(raw_rows),
        "rows_out": len(normalized_rows),
    }


def normalize_part3_tariff_export(
    raw_path: str | Path,
    output_path: str | Path,
) -> dict[str, str | int]:
    raw_rows = _read_csv(raw_path)
    normalized_rows = []

    for row in raw_rows:
        market = _lookup(row, ("market", "country market"))
        hs_code = _lookup(row, ("hs code", "hts code", "tariff code"))
        if not market or not hs_code:
            continue
        normalized_rows.append(
            {
                "market": market,
                "hs_code": hs_code,
                "base_duty_rate": f"{_clean_percent(_lookup(row, ('base duty rate', 'base duty', 'duty rate'))):.4f}",
                "additional_duty_rate": f"{_clean_percent(_lookup(row, ('additional duty rate', 'additional duty', 'extra duty'))):.4f}",
                "brokerage_fee": _clean_currency(_lookup(row, ("brokerage fee", "broker fee"))),
                "port_fee": _clean_currency(_lookup(row, ("port fee", "port handling fee"))),
                "effective_date": _lookup(row, ("effective date", "date")) or date.today().isoformat(),
            }
        )

    _write_csv(output_path, PART3_TARIFF_FIELDS, normalized_rows)
    return {
        "template": "part3_tariff",
        "target_table": "tariff_tax",
        "rows_in": len(raw_rows),
        "rows_out": len(normalized_rows),
    }


def normalize_part3_shipment_export(
    raw_path: str | Path,
    output_path: str | Path,
) -> dict[str, str | int]:
    raw_rows = _read_csv(raw_path)
    normalized_rows = []

    for row in raw_rows:
        shipment_id = _lookup(row, ("shipment id", "shipment no", "shipment"))
        supplier_id = _supplier_id_from_row(row)
        if not shipment_id or not supplier_id:
            continue
        normalized_rows.append(
            {
                "shipment_id": shipment_id,
                "supplier_id": supplier_id,
                "shipping_mode": _normalize_shipping_mode(_lookup(row, ("shipping mode", "shipping method", "mode"))),
                "etd": _lookup(row, ("etd", "ship date")),
                "eta": _lookup(row, ("eta", "arrival date")),
                "customs_release_date": _lookup(row, ("customs release date", "customs release", "clearance date")),
                "warehouse_received_date": _lookup(row, ("warehouse received date", "warehouse received", "received date")),
                "sellable_date": _lookup(row, ("sellable date", "live date", "available date")),
                "delay_days": _clean_int(_lookup(row, ("delay days", "delay", "lateness days"))),
                "issue_type": _lookup(row, ("issue type", "issue", "problem")) or "",
                "node": _lookup(row, ("node", "current node", "shipment node")) or "",
                "delay_reason": _lookup(row, ("delay reason", "reason", "delay cause"))
                or _lookup(row, ("issue type", "issue", "problem"))
                or "",
                "cost_component": _clean_currency(
                    _lookup(row, ("cost component", "extra cost", "exception cost"))
                ),
            }
        )

    _write_csv(output_path, PART3_SHIPMENT_FIELDS, normalized_rows)
    return {
        "template": "part3_shipments",
        "target_table": "shipment_events",
        "rows_in": len(raw_rows),
        "rows_out": len(normalized_rows),
    }
