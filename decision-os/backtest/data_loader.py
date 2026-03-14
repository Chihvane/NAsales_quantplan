from __future__ import annotations

import csv
import random
from datetime import date
from pathlib import Path


def month_sequence(start_year: int, start_month: int, end_year: int, end_month: int) -> list[date]:
    months: list[date] = []
    year = start_year
    month = start_month
    while (year, month) <= (end_year, end_month):
        months.append(date(year, month, 1))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


def _clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def generate_demo_panel(seed: int = 42) -> list[dict[str, str | float]]:
    rng = random.Random(seed)
    months = month_sequence(2019, 1, 2024, 12)
    opportunities = [
        {
            "entity_id": "OPP-GEN-001",
            "segment": "Portable Generator",
            "tam": 155_000_000,
            "cagr": 0.10,
            "hhi": 2100,
            "volatility": 0.18,
            "landed_cost": 42,
            "expected_price": 82,
            "platform_fee": 9,
            "required_capital": 140_000,
        },
        {
            "entity_id": "OPP-AUTO-001",
            "segment": "Auto Parts",
            "tam": 175_000_000,
            "cagr": 0.11,
            "hhi": 2400,
            "volatility": 0.16,
            "landed_cost": 36,
            "expected_price": 74,
            "platform_fee": 8,
            "required_capital": 120_000,
        },
        {
            "entity_id": "OPP-CIGAR-001",
            "segment": "Cigar Accessories",
            "tam": 82_000_000,
            "cagr": 0.08,
            "hhi": 3000,
            "volatility": 0.22,
            "landed_cost": 19,
            "expected_price": 41,
            "platform_fee": 6,
            "required_capital": 80_000,
        },
        {
            "entity_id": "OPP-EDC-001",
            "segment": "EDC",
            "tam": 98_000_000,
            "cagr": 0.14,
            "hhi": 2600,
            "volatility": 0.20,
            "landed_cost": 26,
            "expected_price": 58,
            "platform_fee": 7,
            "required_capital": 90_000,
        },
        {
            "entity_id": "OPP-CAMP-001",
            "segment": "Camping Gear",
            "tam": 134_000_000,
            "cagr": 0.12,
            "hhi": 2200,
            "volatility": 0.19,
            "landed_cost": 31,
            "expected_price": 69,
            "platform_fee": 8,
            "required_capital": 110_000,
        },
        {
            "entity_id": "OPP-LIGHT-001",
            "segment": "Tactical Light",
            "tam": 88_000_000,
            "cagr": 0.09,
            "hhi": 2900,
            "volatility": 0.21,
            "landed_cost": 24,
            "expected_price": 52,
            "platform_fee": 7,
            "required_capital": 85_000,
        },
    ]

    rows: list[dict[str, str | float]] = []
    for month_index, month_value in enumerate(months):
        macro_shock = 0.0
        supply_shock = 0.0
        if date(2020, 3, 1) <= month_value <= date(2020, 9, 1):
            macro_shock = -0.06
            supply_shock = 0.08
        if date(2021, 6, 1) <= month_value <= date(2022, 2, 1):
            macro_shock = -0.03
            supply_shock = 0.12
        if date(2022, 6, 1) <= month_value <= date(2023, 3, 1):
            macro_shock = -0.02
            supply_shock = 0.05

        seasonal = 0.03 if month_value.month in {5, 6, 11, 12} else -0.01
        for index, opportunity in enumerate(opportunities):
            entity_bias = (index - 2) * 0.004
            tam = opportunity["tam"] * (1 + 0.002 * month_index + seasonal + rng.uniform(-0.015, 0.015))
            cagr = _clip(opportunity["cagr"] + rng.uniform(-0.012, 0.012), 0.02, 0.25)
            hhi = _clip(opportunity["hhi"] + rng.uniform(-180, 180), 1200, 4500)
            volatility = _clip(opportunity["volatility"] + rng.uniform(-0.03, 0.03), 0.08, 0.40)
            landed_cost = opportunity["landed_cost"] * (1 + supply_shock + rng.uniform(-0.06, 0.08))
            expected_price = opportunity["expected_price"] * (1 + macro_shock / 2 + rng.uniform(-0.04, 0.05))
            platform_fee = opportunity["platform_fee"] * (1 + rng.uniform(-0.03, 0.05))
            unit_margin = expected_price - landed_cost - platform_fee
            margin_rate = unit_margin / max(expected_price, 1)
            forward_return_rate = _clip(
                margin_rate * 0.42 + seasonal + entity_bias + macro_shock - supply_shock / 2 + rng.uniform(-0.07, 0.07),
                -0.25,
                0.28,
            )
            benchmark_return_rate = _clip(
                0.035 + seasonal / 2 + macro_shock / 2 + rng.uniform(-0.04, 0.04),
                -0.18,
                0.18,
            )
            rows.append(
                {
                    "as_of_date": month_value.isoformat(),
                    "entity_id": opportunity["entity_id"],
                    "segment": opportunity["segment"],
                    "TAM": round(tam, 2),
                    "CAGR": round(cagr, 4),
                    "HHI": round(hhi, 2),
                    "volatility": round(volatility, 4),
                    "landed_cost": round(landed_cost, 2),
                    "expected_price": round(expected_price, 2),
                    "platform_fee": round(platform_fee, 2),
                    "required_capital": round(opportunity["required_capital"], 2),
                    "forward_return_rate": round(forward_return_rate, 4),
                    "benchmark_return_rate": round(benchmark_return_rate, 4),
                }
            )
    return rows


def write_panel_csv(output_path: str | Path, rows: list[dict[str, str | float]]) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("rows cannot be empty")
    fieldnames = list(rows[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def load_panel_csv(path: str | Path) -> list[dict[str, str | float]]:
    path = Path(path)
    rows: list[dict[str, str | float]] = []
    numeric_fields = {
        "TAM",
        "CAGR",
        "HHI",
        "volatility",
        "landed_cost",
        "expected_price",
        "platform_fee",
        "required_capital",
        "forward_return_rate",
        "benchmark_return_rate",
    }
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            normalized: dict[str, str | float] = {}
            for key, value in row.items():
                if key in numeric_fields:
                    normalized[key] = float(value)
                else:
                    normalized[key] = value
            rows.append(normalized)
    return rows
