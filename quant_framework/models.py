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
