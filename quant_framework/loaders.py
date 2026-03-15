from __future__ import annotations

from pathlib import Path

from .models import (
    ApprovalChainRecord,
    AuditEventRecord,
    B2BAccountRecord,
    CashFlowSnapshotRecord,
    ChannelRecord,
    ChannelBenchmarkRecord,
    ChannelRateCardRecord,
    ComplianceRequirementRecord,
    ConsumerHabitVectorRecord,
    DecisionNodeRecord,
    DecisionRuleRecord,
    DecisionTriggerRecord,
    DataDictionaryFieldRecord,
    EventLibraryRecord,
    EvidenceSourceRecord,
    EvidenceLineageRecord,
    CustomerCohortRecord,
    CustomerSegmentRecord,
    ExperimentRecord,
    ExperimentAssignmentRecord,
    ExperimentMetricRecord,
    FieldDictionaryRecord,
    GateThresholdRecord,
    InventoryPositionRecord,
    KPIDailySnapshotRecord,
    LandedCostScenarioRecord,
    ListingRecord,
    ListingSnapshotRecord,
    LogisticsQuoteRecord,
    MasterDataEntityRecord,
    MarketDestinationRecord,
    MarketSizeInputRecord,
    MarketingSpendRecord,
    Part4OptimizerRecord,
    Part4StressRecord,
    Part3OptimizerRecord,
    Part3ScenarioRecord,
    PolicyChangeLogRecord,
    PricingActionRecord,
    RFQQuoteRecord,
    ProductCatalogRecord,
    RegionDemandRecord,
    RegionWeightProfileRecord,
    ReorderPlanRecord,
    ReviewRecord,
    ReturnClaimRecord,
    SearchTrendRecord,
    ShipmentEventRecord,
    SoldTransactionRecord,
    SupplierRecord,
    StrategyAssumptionRecord,
    TariffTaxRecord,
    TrafficSessionRecord,
    TransactionRecord,
    UpdatePolicyRecord,
)
from .io_utils import read_csv_rows


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    return read_csv_rows(path)


def _parse_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    return normalized in {"1", "true", "yes", "y", "active"}


def load_decision_nodes(path: str | Path) -> list[DecisionNodeRecord]:
    return [
        DecisionNodeRecord(
            node_id=row["node_id"],
            parent_id=row.get("parent_id", ""),
            gate_id=row.get("gate_id", ""),
            stage=row.get("stage", ""),
            decision_question=row.get("decision_question", ""),
            domain=row.get("domain", ""),
            metric_ref=row.get("metric_ref", ""),
            owner_role=row.get("owner_role", ""),
            go_path=row.get("go_path", ""),
            hold_path=row.get("hold_path", ""),
            kill_path=row.get("kill_path", ""),
        )
        for row in _read_csv(path)
    ]


def load_evidence_sources(path: str | Path) -> list[EvidenceSourceRecord]:
    return [
        EvidenceSourceRecord(
            source_id=row["source_id"],
            topic=row.get("topic", ""),
            source_name=row.get("source_name", ""),
            source_type=row.get("source_type", ""),
            confidence_grade=row.get("confidence_grade", ""),
            collected_at=row.get("collected_at", ""),
            freshness_days=int(row.get("freshness_days", 0) or 0),
            version=row.get("version", ""),
            status=row.get("status", ""),
            owner_role=row.get("owner_role", ""),
        )
        for row in _read_csv(path)
    ]


def load_strategy_assumptions(path: str | Path) -> list[StrategyAssumptionRecord]:
    return [
        StrategyAssumptionRecord(
            assumption_id=row["assumption_id"],
            domain=row.get("domain", ""),
            assumption_text=row.get("assumption_text", ""),
            rationale=row.get("rationale", ""),
            confidence_grade=row.get("confidence_grade", ""),
            owner_role=row.get("owner_role", ""),
            validation_method=row.get("validation_method", ""),
            status=row.get("status", ""),
            due_date=row.get("due_date", ""),
        )
        for row in _read_csv(path)
    ]


def load_gate_thresholds(path: str | Path) -> list[GateThresholdRecord]:
    return [
        GateThresholdRecord(
            gate_id=row["gate_id"],
            gate_name=row.get("gate_name", ""),
            metric_name=row.get("metric_name", ""),
            operator=row.get("operator", ""),
            threshold_value=float(row.get("threshold_value", 0) or 0),
            unit=row.get("unit", ""),
            source_grade_min=row.get("source_grade_min", ""),
            approver_role=row.get("approver_role", ""),
            decision_if_fail=row.get("decision_if_fail", ""),
            market_code=row.get("market_code", ""),
        )
        for row in _read_csv(path)
    ]


def load_approval_chain(path: str | Path) -> list[ApprovalChainRecord]:
    return [
        ApprovalChainRecord(
            gate_id=row["gate_id"],
            step_order=int(row.get("step_order", 0) or 0),
            role_name=row.get("role_name", ""),
            owner_name=row.get("owner_name", ""),
            action_type=row.get("action_type", ""),
            status=row.get("status", ""),
            signed_at=row.get("signed_at", ""),
            veto_flag=_parse_bool(row.get("veto_flag", False)),
        )
        for row in _read_csv(path)
    ]


def load_update_policies(path: str | Path) -> list[UpdatePolicyRecord]:
    return [
        UpdatePolicyRecord(
            scope_id=row["scope_id"],
            scope_name=row.get("scope_name", ""),
            update_frequency_days=int(row.get("update_frequency_days", 0) or 0),
            expiry_days=int(row.get("expiry_days", 0) or 0),
            event_trigger=row.get("event_trigger", ""),
            owner_role=row.get("owner_role", ""),
            sla_days=int(row.get("sla_days", 0) or 0),
            status=row.get("status", ""),
        )
        for row in _read_csv(path)
    ]


def load_field_dictionary(path: str | Path) -> list[FieldDictionaryRecord]:
    return [
        FieldDictionaryRecord(
            field_name=row["field_name"],
            field_group=row.get("field_group", ""),
            definition=row.get("definition", ""),
            data_type=row.get("data_type", ""),
            naming_style=row.get("naming_style", ""),
            source_table=row.get("source_table", ""),
            reusable_flag=_parse_bool(row.get("reusable_flag", False)),
            required_flag=_parse_bool(row.get("required_flag", False)),
        )
        for row in _read_csv(path)
    ]


def load_market_destination_registry(path: str | Path) -> list[MarketDestinationRecord]:
    return [
        MarketDestinationRecord(
            market_code=row["market_code"],
            market_name=row.get("market_name", ""),
            region_group=row.get("region_group", ""),
            default_currency=row.get("default_currency", ""),
            analysis_method=row.get("analysis_method", ""),
            habit_model_family=row.get("habit_model_family", ""),
            regulatory_complexity=float(row.get("regulatory_complexity", 0) or 0),
            logistics_complexity=float(row.get("logistics_complexity", 0) or 0),
            fx_risk=float(row.get("fx_risk", 0) or 0),
            digital_maturity=float(row.get("digital_maturity", 0) or 0),
            cross_border_acceptance=float(row.get("cross_border_acceptance", 0) or 0),
            active_flag=_parse_bool(row.get("active_flag", True)),
            notes=row.get("notes", ""),
        )
        for row in _read_csv(path)
    ]


def load_consumer_habit_vectors(path: str | Path) -> list[ConsumerHabitVectorRecord]:
    return [
        ConsumerHabitVectorRecord(
            market_code=row["market_code"],
            category_key=row.get("category_key", ""),
            period=row.get("period", ""),
            price_sensitivity=float(row.get("price_sensitivity", 0) or 0),
            brand_loyalty=float(row.get("brand_loyalty", 0) or 0),
            quality_premium_preference=float(row.get("quality_premium_preference", 0) or 0),
            novelty_seeking=float(row.get("novelty_seeking", 0) or 0),
            social_proof_dependency=float(row.get("social_proof_dependency", 0) or 0),
            discount_dependency=float(row.get("discount_dependency", 0) or 0),
            delivery_speed_preference=float(row.get("delivery_speed_preference", 0) or 0),
            return_aversion=float(row.get("return_aversion", 0) or 0),
            cross_border_affinity=float(row.get("cross_border_affinity", 0) or 0),
            content_driven_discovery=float(row.get("content_driven_discovery", 0) or 0),
            payment_friction_tolerance=float(row.get("payment_friction_tolerance", 0) or 0),
            offline_affinity=float(row.get("offline_affinity", 0) or 0),
            evidence_bundle=row.get("evidence_bundle", ""),
            updated_at=row.get("updated_at", ""),
            owner_role=row.get("owner_role", ""),
        )
        for row in _read_csv(path)
    ]


def load_region_weight_profiles(path: str | Path) -> list[RegionWeightProfileRecord]:
    return [
        RegionWeightProfileRecord(
            market_code=row["market_code"],
            profile_id=row.get("profile_id", ""),
            version=row.get("version", ""),
            factor_weight_market_attract=float(row.get("factor_weight_market_attract", 0) or 0),
            factor_weight_demand_stability=float(row.get("factor_weight_demand_stability", 0) or 0),
            factor_weight_customer_fit=float(row.get("factor_weight_customer_fit", 0) or 0),
            factor_weight_channel_efficiency=float(row.get("factor_weight_channel_efficiency", 0) or 0),
            factor_weight_channel_risk=float(row.get("factor_weight_channel_risk", 0) or 0),
            factor_weight_price_realization=float(row.get("factor_weight_price_realization", 0) or 0),
            geo_fit_weight=float(row.get("geo_fit_weight", 0) or 0),
            habit_fit_weight=float(row.get("habit_fit_weight", 0) or 0),
            penalty_fx_risk=float(row.get("penalty_fx_risk", 0) or 0),
            penalty_compliance_risk=float(row.get("penalty_compliance_risk", 0) or 0),
            penalty_logistics_volatility=float(row.get("penalty_logistics_volatility", 0) or 0),
            calibration_method=row.get("calibration_method", ""),
            calibration_window=row.get("calibration_window", ""),
            updated_at=row.get("updated_at", ""),
            owner_role=row.get("owner_role", ""),
            active_flag=_parse_bool(row.get("active_flag", True)),
        )
        for row in _read_csv(path)
    ]


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


def load_market_size_inputs(path: str | Path) -> list[MarketSizeInputRecord]:
    return [
        MarketSizeInputRecord(
            market_segment=row["market_segment"],
            tam=float(row["tam"]),
            sam=float(row["sam"]),
            som=float(row["som"]),
            ecommerce_penetration=float(row.get("ecommerce_penetration", 0) or 0),
            importable_share=float(row.get("importable_share", 0) or 0),
            cagr=float(row.get("cagr", 0) or 0),
            source=row.get("source", ""),
            confidence_grade=row.get("confidence_grade", ""),
        )
        for row in _read_csv(path)
    ]


def load_channel_benchmarks(path: str | Path) -> list[ChannelBenchmarkRecord]:
    return [
        ChannelBenchmarkRecord(
            channel=row["channel"],
            benchmark_conversion_rate=float(row.get("benchmark_conversion_rate", 0) or 0),
            benchmark_average_order_value=float(row.get("benchmark_average_order_value", 0) or 0),
            benchmark_roas=float(row.get("benchmark_roas", 0) or 0),
            benchmark_cac=float(row.get("benchmark_cac", 0) or 0),
        )
        for row in _read_csv(path)
    ]


def load_event_library(path: str | Path) -> list[EventLibraryRecord]:
    return [
        EventLibraryRecord(
            event_id=row["event_id"],
            event_date=row["event_date"],
            event_type=row.get("event_type", ""),
            market_scope=row.get("market_scope", ""),
            event_name=row.get("event_name", ""),
            severity=float(row.get("severity", 0) or 0),
            expected_direction=row.get("expected_direction", ""),
            source_ref=row.get("source_ref", ""),
            market_code=row.get("market_code", ""),
            scope_key=row.get("scope_key", ""),
        )
        for row in _read_csv(path)
    ]


def load_master_data_entities(path: str | Path) -> list[MasterDataEntityRecord]:
    return [
        MasterDataEntityRecord(
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            entity_name=row.get("entity_name", ""),
            owner_role=row.get("owner_role", ""),
            version=row.get("version", ""),
            approved_flag=_parse_bool(row.get("approved_flag", False)),
            active_flag=_parse_bool(row.get("active_flag", False)),
            duplicate_flag=_parse_bool(row.get("duplicate_flag", False)),
            missing_required_field_count=int(row.get("missing_required_field_count", 0) or 0),
            updated_at=row.get("updated_at", ""),
        )
        for row in _read_csv(path)
    ]


def load_data_dictionary_fields(path: str | Path) -> list[DataDictionaryFieldRecord]:
    return [
        DataDictionaryFieldRecord(
            field_name=row["field_name"],
            field_group=row.get("field_group", ""),
            entity_type=row.get("entity_type", ""),
            data_type=row.get("data_type", ""),
            required_flag=_parse_bool(row.get("required_flag", False)),
            enum_flag=_parse_bool(row.get("enum_flag", False)),
            validation_rule=row.get("validation_rule", ""),
            version=row.get("version", ""),
            approved_flag=_parse_bool(row.get("approved_flag", False)),
        )
        for row in _read_csv(path)
    ]


def load_evidence_lineage(path: str | Path) -> list[EvidenceLineageRecord]:
    return [
        EvidenceLineageRecord(
            lineage_id=row["lineage_id"],
            source_id=row.get("source_id", ""),
            target_metric_id=row.get("target_metric_id", ""),
            dataset_version=row.get("dataset_version", ""),
            transform_step_count=int(row.get("transform_step_count", 0) or 0),
            script_version=row.get("script_version", ""),
            generated_at=row.get("generated_at", ""),
            approval_ref=row.get("approval_ref", ""),
            reproducible_flag=_parse_bool(row.get("reproducible_flag", False)),
            reconstruction_minutes=int(row.get("reconstruction_minutes", 0) or 0),
        )
        for row in _read_csv(path)
    ]


def load_audit_events(path: str | Path) -> list[AuditEventRecord]:
    return [
        AuditEventRecord(
            audit_id=row["audit_id"],
            event_type=row.get("event_type", ""),
            object_type=row.get("object_type", ""),
            object_id=row.get("object_id", ""),
            actor_role=row.get("actor_role", ""),
            happened_at=row.get("happened_at", ""),
            immutable_flag=_parse_bool(row.get("immutable_flag", False)),
            approval_ref=row.get("approval_ref", ""),
            status=row.get("status", ""),
        )
        for row in _read_csv(path)
    ]


def load_decision_rules(path: str | Path) -> list[DecisionRuleRecord]:
    return [
        DecisionRuleRecord(
            rule_id=row["rule_id"],
            scenario=row.get("scenario", ""),
            gate_name=row.get("gate_name", ""),
            metric_name=row.get("metric_name", ""),
            operator=row.get("operator", ""),
            threshold_value=float(row.get("threshold_value", 0) or 0),
            severity=row.get("severity", ""),
            approver_role=row.get("approver_role", ""),
            active_flag=_parse_bool(row.get("active_flag", False)),
            version=row.get("version", ""),
            stop_loss_flag=_parse_bool(row.get("stop_loss_flag", False)),
        )
        for row in _read_csv(path)
    ]


def load_decision_triggers(path: str | Path) -> list[DecisionTriggerRecord]:
    return [
        DecisionTriggerRecord(
            trigger_id=row["trigger_id"],
            rule_id=row.get("rule_id", ""),
            object_scope=row.get("object_scope", ""),
            triggered_at=row.get("triggered_at", ""),
            observed_value=float(row.get("observed_value", 0) or 0),
            decision_status=row.get("decision_status", ""),
            resolved_flag=_parse_bool(row.get("resolved_flag", False)),
            approval_ref=row.get("approval_ref", ""),
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


def load_part3_scenario_registry(path: str | Path) -> list[Part3ScenarioRecord]:
    return [
        Part3ScenarioRecord(
            scenario_id=row["scenario_id"],
            scenario_name=row.get("scenario_name", ""),
            shock_target=row.get("shock_target", ""),
            shock_multiplier=float(row.get("shock_multiplier", 1) or 1),
            severity=row.get("severity", ""),
            active_flag=_parse_bool(row.get("active_flag", False)),
            notes=row.get("notes", ""),
        )
        for row in _read_csv(path)
    ]


def load_part3_optimizer_registry(path: str | Path) -> list[Part3OptimizerRecord]:
    return [
        Part3OptimizerRecord(
            optimizer_id=row["optimizer_id"],
            objective_name=row.get("objective_name", ""),
            objective_type=row.get("objective_type", ""),
            risk_measure=row.get("risk_measure", ""),
            max_loss_probability=float(row.get("max_loss_probability", 0) or 0),
            min_net_margin_rate=float(row.get("min_net_margin_rate", 0) or 0),
            min_confidence_score=float(row.get("min_confidence_score", 0) or 0),
            max_lead_time_days=int(row.get("max_lead_time_days", 0) or 0),
            max_landed_cost=float(row.get("max_landed_cost", 0) or 0),
            capital_limit=float(row.get("capital_limit", 0) or 0),
            active_flag=_parse_bool(row.get("active_flag", False)),
        )
        for row in _read_csv(path)
    ]


def load_part4_optimizer_registry(path: str | Path) -> list[Part4OptimizerRecord]:
    return [
        Part4OptimizerRecord(
            optimizer_id=row["optimizer_id"],
            objective_name=row.get("objective_name", ""),
            objective_type=row.get("objective_type", ""),
            risk_measure=row.get("risk_measure", ""),
            max_loss_probability=float(row.get("max_loss_probability", 0) or 0),
            min_contribution_margin_rate=float(row.get("min_contribution_margin_rate", 0) or 0),
            min_priority_score=float(row.get("min_priority_score", 0) or 0),
            max_payback_months=float(row.get("max_payback_months", 0) or 0),
            max_paid_share=float(row.get("max_paid_share", 0) or 0),
            capital_limit=float(row.get("capital_limit", 0) or 0),
            active_flag=_parse_bool(row.get("active_flag", False)),
            objective_lambda=float(row.get("objective_lambda", 0.4) or 0.4),
            turnover_penalty_lambda=float(row.get("turnover_penalty_lambda", 0.15) or 0.15),
            max_single_channel_weight=float(row.get("max_single_channel_weight", 0.6) or 0.6),
        )
        for row in _read_csv(path)
    ]


def load_part4_stress_registry(path: str | Path) -> list[Part4StressRecord]:
    return [
        Part4StressRecord(
            scenario_id=row["scenario_id"],
            scenario_name=row.get("scenario_name", ""),
            shock_target=row.get("shock_target", ""),
            shock_multiplier=float(row.get("shock_multiplier", 1) or 1),
            severity=row.get("severity", ""),
            channel_scope=row.get("channel_scope", "all"),
            active_flag=_parse_bool(row.get("active_flag", False)),
            notes=row.get("notes", ""),
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


def load_experiment_assignments(path: str | Path) -> list[ExperimentAssignmentRecord]:
    return [
        ExperimentAssignmentRecord(
            experiment_id=row["experiment_id"],
            entity_id=row["entity_id"],
            variant=row["variant"],
            assigned_at=row["assigned_at"],
            channel=row.get("channel", ""),
        )
        for row in _read_csv(path)
    ]


def load_experiment_metrics(path: str | Path) -> list[ExperimentMetricRecord]:
    return [
        ExperimentMetricRecord(
            experiment_id=row["experiment_id"],
            date=row["date"],
            variant=row["variant"],
            metric_name=row["metric_name"],
            exposures=int(row.get("exposures", 0) or 0),
            conversions=int(row.get("conversions", 0) or 0),
            value=float(row.get("value", 0) or 0),
            ci_low=float(row.get("ci_low", 0) or 0),
            ci_high=float(row.get("ci_high", 0) or 0),
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
