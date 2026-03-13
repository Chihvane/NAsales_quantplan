from __future__ import annotations

from pathlib import Path

from .models import (
    ChannelRecord,
    ComplianceRequirementRecord,
    CustomerSegmentRecord,
    ListingRecord,
    ListingSnapshotRecord,
    LogisticsQuoteRecord,
    RFQQuoteRecord,
    ProductCatalogRecord,
    RegionDemandRecord,
    ReviewRecord,
    SearchTrendRecord,
    ShipmentEventRecord,
    SoldTransactionRecord,
    SupplierRecord,
    TariffTaxRecord,
    TransactionRecord,
)
from .io_utils import read_csv_rows


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    return read_csv_rows(path)


def _parse_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    return normalized in {"1", "true", "yes", "y", "active"}


def load_search_trends(path: str | Path) -> list[SearchTrendRecord]:
    return [
        SearchTrendRecord(
            month=row["month"],
            keyword=row["keyword"],
            interest=float(row["interest"]),
        )
        for row in _read_csv(path)
    ]


def load_region_demand(path: str | Path) -> list[RegionDemandRecord]:
    return [
        RegionDemandRecord(
            region=row["region"],
            demand_score=float(row["demand_score"]),
        )
        for row in _read_csv(path)
    ]


def load_customer_segments(path: str | Path) -> list[CustomerSegmentRecord]:
    return [
        CustomerSegmentRecord(
            dimension=row["dimension"],
            value=row["value"],
            count=int(row["count"]),
        )
        for row in _read_csv(path)
    ]


def load_listings(path: str | Path) -> list[ListingRecord]:
    return [
        ListingRecord(
            sku_id=row["sku_id"],
            platform=row["platform"],
            brand=row["brand"],
            list_price=float(row["list_price"]),
            monthly_sales_estimate=int(row["monthly_sales_estimate"]),
            rating=float(row["rating"]),
            review_count=int(row["review_count"]),
        )
        for row in _read_csv(path)
    ]


def load_transactions(path: str | Path) -> list[TransactionRecord]:
    return [
        TransactionRecord(
            sku_id=row["sku_id"],
            platform=row["platform"],
            date=row["date"],
            list_price=float(row["list_price"]),
            actual_price=float(row["actual_price"]),
            units=int(row["units"]),
        )
        for row in _read_csv(path)
    ]


def load_channels(path: str | Path) -> list[ChannelRecord]:
    return [
        ChannelRecord(
            channel=row["channel"],
            visits=int(row["visits"]),
            orders=int(row["orders"]),
            revenue=float(row["revenue"]),
            ad_spend=float(row.get("ad_spend", 0) or 0),
        )
        for row in _read_csv(path)
    ]


def load_listing_snapshots(path: str | Path) -> list[ListingSnapshotRecord]:
    return [
        ListingSnapshotRecord(
            platform=row["platform"],
            listing_id=row["listing_id"],
            canonical_sku=row["canonical_sku"],
            brand=row["brand"],
            seller_id=row.get("seller_id", ""),
            captured_at=row["captured_at"],
            list_price=float(row["list_price"]),
            sale_price=float(row.get("sale_price", row["list_price"]) or row["list_price"]),
            currency=row.get("currency", "USD"),
            shipping_fee=float(row.get("shipping_fee", 0) or 0),
            rating_avg=float(row.get("rating_avg", 0) or 0),
            review_count=int(row.get("review_count", 0) or 0),
            sold_count_window=int(row.get("sold_count_window", 0) or 0),
            sales_rank=int(row.get("sales_rank", 0) or 0),
            active_flag=_parse_bool(row.get("active_flag", True)),
            seller_type=row.get("seller_type", "unknown"),
            fulfillment_type=row.get("fulfillment_type", "unknown"),
        )
        for row in _read_csv(path)
    ]


def load_sold_transactions(path: str | Path) -> list[SoldTransactionRecord]:
    return [
        SoldTransactionRecord(
            platform=row["platform"],
            sold_id=row["sold_id"],
            listing_id=row["listing_id"],
            canonical_sku=row["canonical_sku"],
            sold_at=row["sold_at"],
            transaction_price=float(row["transaction_price"]),
            shipping_fee=float(row.get("shipping_fee", 0) or 0),
            units=int(row.get("units", 1) or 1),
            seller_type=row.get("seller_type", "unknown"),
        )
        for row in _read_csv(path)
    ]


def load_product_catalog(path: str | Path) -> list[ProductCatalogRecord]:
    return [
        ProductCatalogRecord(
            canonical_sku=row["canonical_sku"],
            brand=row["brand"],
            category_path=row.get("category_path", ""),
            title=row.get("title", ""),
            attribute_tokens=row.get("attribute_tokens", ""),
            first_available_date=row.get("first_available_date", ""),
        )
        for row in _read_csv(path)
    ]


def load_reviews(path: str | Path) -> list[ReviewRecord]:
    return [
        ReviewRecord(
            platform=row["platform"],
            canonical_sku=row["canonical_sku"],
            review_id=row["review_id"],
            review_date=row["review_date"],
            rating=float(row.get("rating", 0) or 0),
            review_text=row.get("review_text", ""),
        )
        for row in _read_csv(path)
    ]


def load_suppliers(path: str | Path) -> list[SupplierRecord]:
    return [
        SupplierRecord(
            supplier_id=row["supplier_id"],
            supplier_name=row["supplier_name"],
            supplier_type=row["supplier_type"],
            region=row["region"],
            factory_flag=_parse_bool(row.get("factory_flag", False)),
            oem_flag=_parse_bool(row.get("oem_flag", False)),
            odm_flag=_parse_bool(row.get("odm_flag", False)),
            main_category=row.get("main_category", ""),
            moq=int(row.get("moq", 0) or 0),
            sample_days=int(row.get("sample_days", 0) or 0),
            production_days=int(row.get("production_days", 0) or 0),
            capacity_score=float(row.get("capacity_score", 0) or 0),
            compliance_support_score=float(row.get("compliance_support_score", 0) or 0),
        )
        for row in _read_csv(path)
    ]


def load_rfq_quotes(path: str | Path) -> list[RFQQuoteRecord]:
    return [
        RFQQuoteRecord(
            supplier_id=row["supplier_id"],
            sku_version=row["sku_version"],
            incoterm=row["incoterm"],
            moq_tier=int(row.get("moq_tier", 0) or 0),
            unit_price=float(row.get("unit_price", 0) or 0),
            sample_fee=float(row.get("sample_fee", 0) or 0),
            tooling_fee=float(row.get("tooling_fee", 0) or 0),
            packaging_cost=float(row.get("packaging_cost", 0) or 0),
            customization_cost=float(row.get("customization_cost", 0) or 0),
            currency=row.get("currency", "USD"),
            quote_date=row.get("quote_date", ""),
        )
        for row in _read_csv(path)
    ]


def load_compliance_requirements(path: str | Path) -> list[ComplianceRequirementRecord]:
    return [
        ComplianceRequirementRecord(
            market=row["market"],
            category=row["category"],
            requirement_type=row["requirement_type"],
            requirement_name=row["requirement_name"],
            mandatory_flag=_parse_bool(row.get("mandatory_flag", False)),
            estimated_cost=float(row.get("estimated_cost", 0) or 0),
            estimated_days=int(row.get("estimated_days", 0) or 0),
            risk_level=row.get("risk_level", "medium"),
            notes=row.get("notes", ""),
        )
        for row in _read_csv(path)
    ]


def load_logistics_quotes(path: str | Path) -> list[LogisticsQuoteRecord]:
    return [
        LogisticsQuoteRecord(
            route_id=row["route_id"],
            origin=row["origin"],
            destination=row["destination"],
            shipping_mode=row["shipping_mode"],
            incoterm=row["incoterm"],
            quote_basis=row.get("quote_basis", "per_unit"),
            cost_value=float(row.get("cost_value", 0) or 0),
            currency=row.get("currency", "USD"),
            lead_time_days=int(row.get("lead_time_days", 0) or 0),
            volatility_score=float(row.get("volatility_score", 0) or 0),
            quote_date=row.get("quote_date", ""),
        )
        for row in _read_csv(path)
    ]


def load_tariff_tax(path: str | Path) -> list[TariffTaxRecord]:
    return [
        TariffTaxRecord(
            market=row["market"],
            hs_code=row["hs_code"],
            base_duty_rate=float(row.get("base_duty_rate", 0) or 0),
            additional_duty_rate=float(row.get("additional_duty_rate", 0) or 0),
            brokerage_fee=float(row.get("brokerage_fee", 0) or 0),
            port_fee=float(row.get("port_fee", 0) or 0),
            effective_date=row.get("effective_date", ""),
        )
        for row in _read_csv(path)
    ]


def load_shipment_events(path: str | Path) -> list[ShipmentEventRecord]:
    return [
        ShipmentEventRecord(
            shipment_id=row["shipment_id"],
            supplier_id=row["supplier_id"],
            shipping_mode=row["shipping_mode"],
            etd=row["etd"],
            eta=row["eta"],
            customs_release_date=row["customs_release_date"],
            warehouse_received_date=row["warehouse_received_date"],
            sellable_date=row["sellable_date"],
            delay_days=int(row.get("delay_days", 0) or 0),
            issue_type=row.get("issue_type", ""),
        )
        for row in _read_csv(path)
    ]
