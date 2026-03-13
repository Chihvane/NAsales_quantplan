from __future__ import annotations

from pathlib import Path

from .models import (
    B2BAccountRecord,
    CashFlowSnapshotRecord,
    ChannelRecord,
    ChannelRateCardRecord,
    ComplianceRequirementRecord,
    CustomerCohortRecord,
    CustomerSegmentRecord,
    ExperimentRecord,
    InventoryPositionRecord,
    KPIDailySnapshotRecord,
    LandedCostScenarioRecord,
    ListingRecord,
    ListingSnapshotRecord,
    LogisticsQuoteRecord,
    MarketingSpendRecord,
    PolicyChangeLogRecord,
    PricingActionRecord,
    RFQQuoteRecord,
    ProductCatalogRecord,
    RegionDemandRecord,
    ReorderPlanRecord,
    ReviewRecord,
    ReturnClaimRecord,
    SearchTrendRecord,
    ShipmentEventRecord,
    SoldTransactionRecord,
    SupplierRecord,
    TariffTaxRecord,
    TrafficSessionRecord,
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
            quote_id=row.get("quote_id", ""),
            product_spec_key=row.get("product_spec_key", ""),
            price_breaks_json=row.get("price_breaks_json", ""),
            lead_time_days=int(row.get("lead_time_days", 0) or 0),
            payment_terms=row.get("payment_terms", ""),
            certifications_list=row.get("certifications_list", ""),
            quote_valid_until=row.get("quote_valid_until", ""),
            source_confidence=float(row.get("source_confidence", 0) or 0),
            captured_at=row.get("captured_at", ""),
            included_items=row.get("included_items", ""),
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
            node=row.get("node", ""),
            delay_reason=row.get("delay_reason", ""),
            cost_component=float(row.get("cost_component", 0) or 0),
        )
        for row in _read_csv(path)
    ]


def load_landed_cost_scenarios(path: str | Path) -> list[LandedCostScenarioRecord]:
    return [
        LandedCostScenarioRecord(
            scenario_id=row["scenario_id"],
            canonical_sku=row["canonical_sku"],
            channel=row["channel"],
            mode=row.get("mode", ""),
            landed_cost_p10=float(row.get("landed_cost_p10", 0) or 0),
            landed_cost_p50=float(row.get("landed_cost_p50", 0) or 0),
            landed_cost_p90=float(row.get("landed_cost_p90", 0) or 0),
            sell_price=float(row.get("sell_price", 0) or 0),
            working_capital_cost=float(row.get("working_capital_cost", 0) or 0),
            return_reserve=float(row.get("return_reserve", 0) or 0),
            scenario_confidence_score=float(row.get("scenario_confidence_score", 0) or 0),
        )
        for row in _read_csv(path)
    ]


def load_channel_rate_cards(path: str | Path) -> list[ChannelRateCardRecord]:
    return [
        ChannelRateCardRecord(
            channel=row["channel"],
            fee_type=row["fee_type"],
            fee_basis=row["fee_basis"],
            fee_rate=float(row.get("fee_rate", 0) or 0),
            fixed_fee=float(row.get("fixed_fee", 0) or 0),
            effective_date=row.get("effective_date", ""),
            source_ref=row.get("source_ref", ""),
            notes=row.get("notes", ""),
        )
        for row in _read_csv(path)
    ]


def load_marketing_spend(path: str | Path) -> list[MarketingSpendRecord]:
    return [
        MarketingSpendRecord(
            date=row["date"],
            channel=row["channel"],
            campaign_id=row.get("campaign_id", ""),
            traffic_source=row.get("traffic_source", ""),
            spend=float(row.get("spend", 0) or 0),
            impressions=int(row.get("impressions", 0) or 0),
            clicks=int(row.get("clicks", 0) or 0),
            attributed_orders=int(row.get("attributed_orders", 0) or 0),
            attributed_revenue=float(row.get("attributed_revenue", 0) or 0),
        )
        for row in _read_csv(path)
    ]


def load_traffic_sessions(path: str | Path) -> list[TrafficSessionRecord]:
    return [
        TrafficSessionRecord(
            date=row["date"],
            channel=row["channel"],
            traffic_source=row.get("traffic_source", ""),
            sessions=int(row.get("sessions", 0) or 0),
            product_page_views=int(row.get("product_page_views", 0) or 0),
            add_to_cart=int(row.get("add_to_cart", 0) or 0),
            checkout_start=int(row.get("checkout_start", 0) or 0),
            orders=int(row.get("orders", 0) or 0),
        )
        for row in _read_csv(path)
    ]


def load_returns_claims(path: str | Path) -> list[ReturnClaimRecord]:
    return [
        ReturnClaimRecord(
            date=row["date"],
            channel=row["channel"],
            order_id=row["order_id"],
            sku_id=row["sku_id"],
            return_flag=_parse_bool(row.get("return_flag", False)),
            refund_amount=float(row.get("refund_amount", 0) or 0),
            return_reason=row.get("return_reason", ""),
            claim_cost=float(row.get("claim_cost", 0) or 0),
            dispute_flag=_parse_bool(row.get("dispute_flag", False)),
        )
        for row in _read_csv(path)
    ]


def load_customer_cohorts(path: str | Path) -> list[CustomerCohortRecord]:
    return [
        CustomerCohortRecord(
            cohort_month=row["cohort_month"],
            channel=row["channel"],
            customers=int(row.get("customers", 0) or 0),
            repeat_customers=int(row.get("repeat_customers", 0) or 0),
            repeat_orders=int(row.get("repeat_orders", 0) or 0),
            repeat_revenue=float(row.get("repeat_revenue", 0) or 0),
        )
        for row in _read_csv(path)
    ]


def load_inventory_positions(path: str | Path) -> list[InventoryPositionRecord]:
    return [
        InventoryPositionRecord(
            date=row["date"],
            channel=row["channel"],
            warehouse=row.get("warehouse", ""),
            sku_id=row["sku_id"],
            on_hand_units=int(row.get("on_hand_units", 0) or 0),
            inbound_units=int(row.get("inbound_units", 0) or 0),
            sell_through_units=int(row.get("sell_through_units", 0) or 0),
            storage_cost=float(row.get("storage_cost", 0) or 0),
        )
        for row in _read_csv(path)
    ]


def load_experiment_registry(path: str | Path) -> list[ExperimentRecord]:
    return [
        ExperimentRecord(
            experiment_id=row["experiment_id"],
            channel=row["channel"],
            hypothesis=row.get("hypothesis", ""),
            start_date=row.get("start_date", ""),
            end_date=row.get("end_date", ""),
            primary_metric=row.get("primary_metric", ""),
            mde=float(row.get("mde", 0) or 0),
            split_ratio=float(row.get("split_ratio", 0) or 0),
            stop_rule=row.get("stop_rule", ""),
            status=row.get("status", ""),
        )
        for row in _read_csv(path)
    ]


def load_b2b_accounts(path: str | Path) -> list[B2BAccountRecord]:
    return [
        B2BAccountRecord(
            account_id=row["account_id"],
            account_type=row.get("account_type", ""),
            region=row.get("region", ""),
            discount_rate=float(row.get("discount_rate", 0) or 0),
            payment_terms_days=int(row.get("payment_terms_days", 0) or 0),
            rebate_rate=float(row.get("rebate_rate", 0) or 0),
            annual_target=float(row.get("annual_target", 0) or 0),
        )
        for row in _read_csv(path)
    ]


def load_kpi_daily_snapshots(path: str | Path) -> list[KPIDailySnapshotRecord]:
    return [
        KPIDailySnapshotRecord(
            date=row["date"],
            channel=row["channel"],
            revenue=float(row.get("revenue", 0) or 0),
            contribution_profit=float(row.get("contribution_profit", 0) or 0),
            ad_spend=float(row.get("ad_spend", 0) or 0),
            refunds=float(row.get("refunds", 0) or 0),
            disputes=int(row.get("disputes", 0) or 0),
            inventory_value=float(row.get("inventory_value", 0) or 0),
            operating_status=row.get("operating_status", ""),
        )
        for row in _read_csv(path)
    ]


def load_pricing_actions(path: str | Path) -> list[PricingActionRecord]:
    return [
        PricingActionRecord(
            date=row["date"],
            channel=row["channel"],
            sku_id=row["sku_id"],
            action_type=row.get("action_type", ""),
            old_price=float(row.get("old_price", 0) or 0),
            new_price=float(row.get("new_price", 0) or 0),
            promo_flag=_parse_bool(row.get("promo_flag", False)),
            bundle_flag=_parse_bool(row.get("bundle_flag", False)),
            owner=row.get("owner", ""),
        )
        for row in _read_csv(path)
    ]


def load_reorder_plan(path: str | Path) -> list[ReorderPlanRecord]:
    return [
        ReorderPlanRecord(
            date=row["date"],
            sku_id=row["sku_id"],
            warehouse=row.get("warehouse", ""),
            reorder_point=int(row.get("reorder_point", 0) or 0),
            safety_stock=int(row.get("safety_stock", 0) or 0),
            target_cover_days=float(row.get("target_cover_days", 0) or 0),
            planned_units=int(row.get("planned_units", 0) or 0),
            eta=row.get("eta", ""),
        )
        for row in _read_csv(path)
    ]


def load_policy_change_log(path: str | Path) -> list[PolicyChangeLogRecord]:
    return [
        PolicyChangeLogRecord(
            platform=row["platform"],
            policy_type=row.get("policy_type", ""),
            effective_date=row.get("effective_date", ""),
            source_url=row.get("source_url", ""),
            impact_level=row.get("impact_level", ""),
            change_summary=row.get("change_summary", ""),
        )
        for row in _read_csv(path)
    ]


def load_cash_flow_snapshots(path: str | Path) -> list[CashFlowSnapshotRecord]:
    return [
        CashFlowSnapshotRecord(
            date=row["date"],
            channel=row["channel"],
            receivable=float(row.get("receivable", 0) or 0),
            payable=float(row.get("payable", 0) or 0),
            inventory_cash_lock=float(row.get("inventory_cash_lock", 0) or 0),
            ad_cash_out=float(row.get("ad_cash_out", 0) or 0),
            refund_cash_out=float(row.get("refund_cash_out", 0) or 0),
        )
        for row in _read_csv(path)
    ]
