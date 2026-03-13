from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchTrendRecord:
    month: str
    keyword: str
    interest: float


@dataclass(frozen=True)
class RegionDemandRecord:
    region: str
    demand_score: float


@dataclass(frozen=True)
class CustomerSegmentRecord:
    dimension: str
    value: str
    count: int


@dataclass(frozen=True)
class ListingRecord:
    sku_id: str
    platform: str
    brand: str
    list_price: float
    monthly_sales_estimate: int
    rating: float
    review_count: int


@dataclass(frozen=True)
class TransactionRecord:
    sku_id: str
    platform: str
    date: str
    list_price: float
    actual_price: float
    units: int


@dataclass(frozen=True)
class ChannelRecord:
    channel: str
    visits: int
    orders: int
    revenue: float
    ad_spend: float = 0.0


@dataclass(frozen=True)
class ListingSnapshotRecord:
    platform: str
    listing_id: str
    canonical_sku: str
    brand: str
    seller_id: str
    captured_at: str
    list_price: float
    sale_price: float
    currency: str
    shipping_fee: float
    rating_avg: float
    review_count: int
    sold_count_window: int
    sales_rank: int
    active_flag: bool
    seller_type: str
    fulfillment_type: str


@dataclass(frozen=True)
class SoldTransactionRecord:
    platform: str
    sold_id: str
    listing_id: str
    canonical_sku: str
    sold_at: str
    transaction_price: float
    shipping_fee: float
    units: int
    seller_type: str


@dataclass(frozen=True)
class ProductCatalogRecord:
    canonical_sku: str
    brand: str
    category_path: str
    title: str
    attribute_tokens: str
    first_available_date: str = ""


@dataclass(frozen=True)
class ReviewRecord:
    platform: str
    canonical_sku: str
    review_id: str
    review_date: str
    rating: float
    review_text: str


@dataclass(frozen=True)
class MarketSizeAssumptions:
    tam: float
    online_penetration: float
    importable_share: float
    target_capture_share: float
    sample_coverage: float


@dataclass
class Part1Dataset:
    search_trends: list[SearchTrendRecord] = field(default_factory=list)
    region_demand: list[RegionDemandRecord] = field(default_factory=list)
    customer_segments: list[CustomerSegmentRecord] = field(default_factory=list)
    listings: list[ListingRecord] = field(default_factory=list)
    transactions: list[TransactionRecord] = field(default_factory=list)
    channels: list[ChannelRecord] = field(default_factory=list)


@dataclass(frozen=True)
class Part2Assumptions:
    leaderboard_size: int = 5
    sweet_spot_bins: int = 6
    whitespace_threshold: float = 0.05
    min_theme_mentions: int = 1
    min_attribute_support: int = 2


@dataclass
class Part2Dataset:
    listing_snapshots: list[ListingSnapshotRecord] = field(default_factory=list)
    sold_transactions: list[SoldTransactionRecord] = field(default_factory=list)
    product_catalog: list[ProductCatalogRecord] = field(default_factory=list)
    reviews: list[ReviewRecord] = field(default_factory=list)


@dataclass(frozen=True)
class SupplierRecord:
    supplier_id: str
    supplier_name: str
    supplier_type: str
    region: str
    factory_flag: bool
    oem_flag: bool
    odm_flag: bool
    main_category: str
    moq: int
    sample_days: int
    production_days: int
    capacity_score: float
    compliance_support_score: float


@dataclass(frozen=True)
class RFQQuoteRecord:
    supplier_id: str
    sku_version: str
    incoterm: str
    moq_tier: int
    unit_price: float
    sample_fee: float
    tooling_fee: float
    packaging_cost: float
    customization_cost: float
    currency: str
    quote_date: str
    quote_id: str = ""
    product_spec_key: str = ""
    price_breaks_json: str = ""
    lead_time_days: int = 0
    payment_terms: str = ""
    certifications_list: str = ""
    quote_valid_until: str = ""
    source_confidence: float = 0.0
    captured_at: str = ""
    included_items: str = ""


@dataclass(frozen=True)
class ComplianceRequirementRecord:
    market: str
    category: str
    requirement_type: str
    requirement_name: str
    mandatory_flag: bool
    estimated_cost: float
    estimated_days: int
    risk_level: str
    notes: str


@dataclass(frozen=True)
class LogisticsQuoteRecord:
    route_id: str
    origin: str
    destination: str
    shipping_mode: str
    incoterm: str
    quote_basis: str
    cost_value: float
    currency: str
    lead_time_days: int
    volatility_score: float
    quote_date: str


@dataclass(frozen=True)
class TariffTaxRecord:
    market: str
    hs_code: str
    base_duty_rate: float
    additional_duty_rate: float
    brokerage_fee: float
    port_fee: float
    effective_date: str


@dataclass(frozen=True)
class ShipmentEventRecord:
    shipment_id: str
    supplier_id: str
    shipping_mode: str
    etd: str
    eta: str
    customs_release_date: str
    warehouse_received_date: str
    sellable_date: str
    delay_days: int
    issue_type: str
    node: str = ""
    delay_reason: str = ""
    cost_component: float = 0.0


@dataclass(frozen=True)
class Part3Assumptions:
    target_market: str = "US"
    target_sell_price: float = 699.0
    target_order_units: int = 500
    channel_fee_rate: float = 0.15
    marketing_fee_rate: float = 0.08
    return_rate: float = 0.04
    return_cost_per_unit: float = 24.0
    working_capital_rate: float = 0.02


@dataclass
class Part3Dataset:
    suppliers: list[SupplierRecord] = field(default_factory=list)
    rfq_quotes: list[RFQQuoteRecord] = field(default_factory=list)
    compliance_requirements: list[ComplianceRequirementRecord] = field(default_factory=list)
    logistics_quotes: list[LogisticsQuoteRecord] = field(default_factory=list)
    tariff_tax: list[TariffTaxRecord] = field(default_factory=list)
    shipment_events: list[ShipmentEventRecord] = field(default_factory=list)


@dataclass(frozen=True)
class LandedCostScenarioRecord:
    scenario_id: str
    canonical_sku: str
    channel: str
    mode: str
    landed_cost_p10: float
    landed_cost_p50: float
    landed_cost_p90: float
    sell_price: float
    working_capital_cost: float = 0.0
    return_reserve: float = 0.0
    scenario_confidence_score: float = 0.0


@dataclass(frozen=True)
class ChannelRateCardRecord:
    channel: str
    fee_type: str
    fee_basis: str
    fee_rate: float
    fixed_fee: float
    effective_date: str
    source_ref: str = ""
    notes: str = ""


@dataclass(frozen=True)
class MarketingSpendRecord:
    date: str
    channel: str
    campaign_id: str
    traffic_source: str
    spend: float
    impressions: int
    clicks: int
    attributed_orders: int
    attributed_revenue: float


@dataclass(frozen=True)
class TrafficSessionRecord:
    date: str
    channel: str
    traffic_source: str
    sessions: int
    product_page_views: int
    add_to_cart: int
    checkout_start: int
    orders: int


@dataclass(frozen=True)
class ReturnClaimRecord:
    date: str
    channel: str
    order_id: str
    sku_id: str
    return_flag: bool
    refund_amount: float
    return_reason: str
    claim_cost: float
    dispute_flag: bool = False


@dataclass(frozen=True)
class CustomerCohortRecord:
    cohort_month: str
    channel: str
    customers: int
    repeat_customers: int
    repeat_orders: int
    repeat_revenue: float


@dataclass(frozen=True)
class InventoryPositionRecord:
    date: str
    channel: str
    warehouse: str
    sku_id: str
    on_hand_units: int
    inbound_units: int
    sell_through_units: int
    storage_cost: float


@dataclass(frozen=True)
class ExperimentRecord:
    experiment_id: str
    channel: str
    hypothesis: str
    start_date: str
    end_date: str
    primary_metric: str
    mde: float
    split_ratio: float
    stop_rule: str
    status: str


@dataclass(frozen=True)
class B2BAccountRecord:
    account_id: str
    account_type: str
    region: str
    discount_rate: float
    payment_terms_days: int
    rebate_rate: float
    annual_target: float


@dataclass(frozen=True)
class Part4Assumptions:
    target_payback_months: float = 6.0
    max_loss_probability: float = 0.25
    min_contribution_margin_rate: float = 0.05
    target_repeat_rate: float = 0.2
    target_inventory_days: float = 45.0
    risk_penalty_lambda: float = 0.4
    minimum_experiment_days: int = 7


@dataclass
class Part4Dataset:
    listing_snapshots: list[ListingSnapshotRecord] = field(default_factory=list)
    sold_transactions: list[SoldTransactionRecord] = field(default_factory=list)
    product_catalog: list[ProductCatalogRecord] = field(default_factory=list)
    landed_cost_scenarios: list[LandedCostScenarioRecord] = field(default_factory=list)
    channel_rate_cards: list[ChannelRateCardRecord] = field(default_factory=list)
    marketing_spend: list[MarketingSpendRecord] = field(default_factory=list)
    traffic_sessions: list[TrafficSessionRecord] = field(default_factory=list)
    returns_claims: list[ReturnClaimRecord] = field(default_factory=list)
    customer_cohorts: list[CustomerCohortRecord] = field(default_factory=list)
    inventory_positions: list[InventoryPositionRecord] = field(default_factory=list)
    experiment_registry: list[ExperimentRecord] = field(default_factory=list)
    b2b_accounts: list[B2BAccountRecord] = field(default_factory=list)


@dataclass(frozen=True)
class KPIDailySnapshotRecord:
    date: str
    channel: str
    revenue: float
    contribution_profit: float
    ad_spend: float
    refunds: float
    disputes: int
    inventory_value: float
    operating_status: str


@dataclass(frozen=True)
class PricingActionRecord:
    date: str
    channel: str
    sku_id: str
    action_type: str
    old_price: float
    new_price: float
    promo_flag: bool
    bundle_flag: bool
    owner: str


@dataclass(frozen=True)
class ReorderPlanRecord:
    date: str
    sku_id: str
    warehouse: str
    reorder_point: int
    safety_stock: int
    target_cover_days: float
    planned_units: int
    eta: str


@dataclass(frozen=True)
class PolicyChangeLogRecord:
    platform: str
    policy_type: str
    effective_date: str
    source_url: str
    impact_level: str
    change_summary: str


@dataclass(frozen=True)
class CashFlowSnapshotRecord:
    date: str
    channel: str
    receivable: float
    payable: float
    inventory_cash_lock: float
    ad_cash_out: float
    refund_cash_out: float


@dataclass(frozen=True)
class Part5Assumptions:
    target_health_score: float = 0.65
    min_contribution_margin_rate: float = 0.08
    max_refund_rate: float = 0.1
    max_dispute_rate: float = 0.03
    target_inventory_days: float = 45.0
    target_repeat_rate: float = 0.18
    min_experiment_weeks: int = 1
    max_budget_burn_ratio: float = 0.4
    budget_allocation_max_share: float = 0.55


@dataclass
class Part5Dataset:
    listing_snapshots: list[ListingSnapshotRecord] = field(default_factory=list)
    sold_transactions: list[SoldTransactionRecord] = field(default_factory=list)
    product_catalog: list[ProductCatalogRecord] = field(default_factory=list)
    landed_cost_scenarios: list[LandedCostScenarioRecord] = field(default_factory=list)
    channel_rate_cards: list[ChannelRateCardRecord] = field(default_factory=list)
    marketing_spend: list[MarketingSpendRecord] = field(default_factory=list)
    traffic_sessions: list[TrafficSessionRecord] = field(default_factory=list)
    returns_claims: list[ReturnClaimRecord] = field(default_factory=list)
    customer_cohorts: list[CustomerCohortRecord] = field(default_factory=list)
    inventory_positions: list[InventoryPositionRecord] = field(default_factory=list)
    experiment_registry: list[ExperimentRecord] = field(default_factory=list)
    b2b_accounts: list[B2BAccountRecord] = field(default_factory=list)
    kpi_daily_snapshots: list[KPIDailySnapshotRecord] = field(default_factory=list)
    pricing_actions: list[PricingActionRecord] = field(default_factory=list)
    reorder_plan: list[ReorderPlanRecord] = field(default_factory=list)
    policy_change_log: list[PolicyChangeLogRecord] = field(default_factory=list)
    cash_flow_snapshots: list[CashFlowSnapshotRecord] = field(default_factory=list)
