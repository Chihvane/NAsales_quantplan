import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quant_framework.charts import generate_part1_chart_assets  # noqa: E402
from quant_framework.cleaners import normalize_tiktok_listings_export  # noqa: E402
from quant_framework.io_utils import write_csv_rows, write_json  # noqa: E402
from quant_framework.part1 import build_part1_quant_report  # noqa: E402
from quant_framework.pipeline import DEFAULT_ASSUMPTIONS, build_dataset_from_directory  # noqa: E402


def _clean_currency(value: str) -> float:
    cleaned = "".join(ch for ch in value if ch.isdigit() or ch in ".-")
    return float(cleaned) if cleaned else 0.0


def _clean_int(value: str) -> int:
    cleaned = "".join(ch for ch in value if ch.isdigit() or ch == "-")
    return int(cleaned) if cleaned else 0


def _clean_percent(value: str) -> float:
    cleaned = "".join(ch for ch in value if ch.isdigit() or ch in ".-")
    return float(cleaned) / 100 if cleaned else 0.0


def _write_empty_support_tables(data_dir: Path) -> None:
    write_csv_rows(
        data_dir / "search_trends.csv",
        ["month", "keyword", "interest"],
        [],
    )
    write_csv_rows(
        data_dir / "region_demand.csv",
        ["region", "demand_score"],
        [],
    )
    write_csv_rows(
        data_dir / "customer_segments.csv",
        ["dimension", "value", "count"],
        [],
    )


def _derive_transactions_and_channels(raw_csv: Path, data_dir: Path) -> dict:
    transactions = []
    total_orders = 0
    total_revenue = 0.0

    with raw_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            sku_id = row.get("id", "").strip()
            if not sku_id:
                continue
            actual_price = _clean_currency(row.get("price", "0"))
            sold_count = _clean_int(row.get("sold_count", "0"))
            discount = _clean_percent(row.get("discount", "0"))
            if sold_count <= 0:
                continue
            list_price = actual_price / (1 - discount) if 0 < discount < 1 else actual_price
            transactions.append(
                {
                    "sku_id": sku_id,
                    "platform": "TikTok Shop",
                    "date": "2026-03-11",
                    "list_price": f"{list_price:.2f}",
                    "actual_price": f"{actual_price:.2f}",
                    "units": str(sold_count),
                }
            )
            total_orders += sold_count
            total_revenue += actual_price * sold_count

    write_csv_rows(
        data_dir / "transactions.csv",
        ["sku_id", "platform", "date", "list_price", "actual_price", "units"],
        transactions,
    )
    write_csv_rows(
        data_dir / "channels.csv",
        ["channel", "visits", "orders", "revenue", "ad_spend"],
        [
            {
                "channel": "TikTok Shop",
                "visits": "0",
                "orders": str(total_orders),
                "revenue": f"{total_revenue:.2f}",
                "ad_spend": "0.00",
            }
        ],
    )
    return {
        "transactions_rows": len(transactions),
        "channel_orders": total_orders,
        "channel_revenue": round(total_revenue, 2),
    }


def main() -> None:
    raw_csv = ROOT / "external_inputs" / "tiktok-labubu.csv"
    if not raw_csv.exists():
        raise SystemExit(f"Missing raw input: {raw_csv}")

    output_dir = ROOT / "external_inputs" / "tiktok_open_demo"
    data_dir = output_dir / "data"
    charts_dir = output_dir / "charts"
    output_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    listing_summary = normalize_tiktok_listings_export(
        raw_csv,
        data_dir / "listings.csv",
    )
    derived_summary = _derive_transactions_and_channels(raw_csv, data_dir)
    _write_empty_support_tables(data_dir)

    dataset = build_dataset_from_directory(data_dir)
    report = build_part1_quant_report(dataset, DEFAULT_ASSUMPTIONS)
    report_path = write_json(output_dir / "report.json", report)
    chart_paths = generate_part1_chart_assets(report, charts_dir)

    payload = {
        "raw_input": str(raw_csv),
        "listing_cleaning": listing_summary,
        "derived_tables": derived_summary,
        "report_json": str(report_path),
        "charts": chart_paths,
        "validation_summary": report.get("validation", {}).get("summary", {}),
        "notes": [
            "This open-source sample is TikTok Shop data in THB and not a North America dataset.",
            "Demand, region, and customer inputs were unavailable from the raw sample and were left empty on purpose.",
            "Transactions and channel tables were derived from sold_count and price fields for pipeline execution only.",
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
