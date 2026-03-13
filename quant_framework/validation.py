from __future__ import annotations

from .metrics import _classify_hhi


SOURCE_REFERENCES = {
    "google_trends": {
        "label": "Google Trends Help",
        "url": "https://support.google.com/trends/answer/4365533",
    },
    "google_ads_conversion": {
        "label": "Google Ads Help - About conversion tracking",
        "url": "https://support.google.com/google-ads/answer/1722022",
    },
    "google_ads_roas": {
        "label": "Google Ads Help - About target ROAS bidding",
        "url": "https://support.google.com/google-ads/answer/6268637",
    },
    "doj_hhi": {
        "label": "U.S. DOJ and FTC Merger Guidelines",
        "url": "https://www.justice.gov/atr/merger-guidelines",
    },
    "openstax_elasticity": {
        "label": "OpenStax - Price Elasticity of Demand and Price Elasticity of Supply",
        "url": "https://openstax.org/books/principles-economics-3e/pages/5-1-price-elasticity-of-demand-and-price-elasticity-of-supply",
    },
    "nist_iqr": {
        "label": "NIST/SEMATECH e-Handbook of Statistical Methods",
        "url": "https://www.itl.nist.gov/div898/handbook/prc/section1/prc16.htm",
    },
    "umbrex_triangulation": {
        "label": "Umbrex - How to Estimate Market Size using Bottom-Up Analysis",
        "url": "https://umbrex.com/resources/market-sizing-playbook/how-to-estimate-market-size/how-to-estimate-market-size-using-bottom-up-analysis/",
    },
    "holoniq_market_sizing": {
        "label": "HolonIQ - Market Sizing 101",
        "url": "https://www.holoniq.com/notes/market-sizing-101",
    },
}


def _status(passed: bool, review: bool = False) -> str:
    if passed:
        return "pass"
    if review:
        return "review"
    return "fail"


def build_methodology_validation(report: dict) -> dict:
    section_11 = report["sections"]["1.1"]["metrics"]
    section_13 = report["sections"]["1.3"]["metrics"]
    section_14 = report["sections"]["1.4"]["metrics"]
    section_15 = report["sections"]["1.5"]["metrics"]
    section_16 = report["sections"]["1.6"]["metrics"]

    checks = []

    trend_values = list(section_11.get("trend", {}).get("monthly_average_interest", {}).values())
    min_interest = min(trend_values) if trend_values else 0
    max_interest = max(trend_values) if trend_values else 0
    google_range_ok = bool(trend_values) and all(0 <= value <= 100 for value in trend_values)
    checks.append(
        {
            "check_id": "google_trends_relative_scale",
            "status": _status(google_range_ok, review=not trend_values),
            "source": SOURCE_REFERENCES["google_trends"],
            "method": "Demand metrics use Google Trends style 0-100 relative index values in one comparison window.",
            "evidence": {
                "min_interest": min_interest,
                "max_interest": max_interest,
                "missing_input": not bool(trend_values),
            },
        }
    )

    region_shares = section_11.get("regional_share", {})
    region_share_sum = sum(region_shares.values())
    checks.append(
        {
            "check_id": "regional_share_integrity",
            "status": _status(abs(region_share_sum - 1.0) <= 0.01, review=not region_shares),
            "source": SOURCE_REFERENCES["google_trends"],
            "method": "Regional demand shares should reconcile back to 100% of the modeled regional demand pool.",
            "evidence": {
                "regional_share_sum": round(region_share_sum, 4),
                "missing_input": not bool(region_shares),
            },
        }
    )

    hhi = section_13["bottom_up"].get("hhi", 0.0)
    expected_level = _classify_hhi(hhi)
    checks.append(
        {
            "check_id": "market_concentration_thresholds",
            "status": _status(
                section_13["bottom_up"].get("concentration_level") == expected_level
            ),
            "source": SOURCE_REFERENCES["doj_hhi"],
            "method": "Market concentration classification uses current DOJ/FTC HHI thresholds.",
            "evidence": {
                "hhi": hhi,
                "expected_level": expected_level,
                "reported_level": section_13["bottom_up"].get("concentration_level"),
            },
        }
    )

    top_down_sam = section_13["top_down"].get("sam", 0.0)
    bottom_up_market = section_13["bottom_up"].get("estimated_annual_market_size", 0.0)
    triangulation_gap = 0.0
    if top_down_sam:
        triangulation_gap = abs(bottom_up_market - top_down_sam) / top_down_sam
    checks.append(
        {
            "check_id": "market_size_triangulation_gap",
            "status": _status(triangulation_gap <= 0.15, review=triangulation_gap > 0.15),
            "source": SOURCE_REFERENCES["umbrex_triangulation"],
            "method": "Top-down and bottom-up estimates are triangulated; gaps above 15% require review rather than blind acceptance.",
            "evidence": {
                "top_down_sam": top_down_sam,
                "bottom_up_annual_market_size": bottom_up_market,
                "gap_ratio": round(triangulation_gap, 4),
            },
        }
    )
    checks.append(
        {
            "check_id": "market_size_dual_method_presence",
            "status": _status(bool(top_down_sam and bottom_up_market)),
            "source": SOURCE_REFERENCES["holoniq_market_sizing"],
            "method": "Market sizing keeps both top-down and bottom-up estimates instead of relying on one side only.",
            "evidence": {
                "has_top_down": bool(top_down_sam),
                "has_bottom_up": bool(bottom_up_market),
            },
        }
    )

    raw_sample_monthly_gmv = section_13["bottom_up"].get("sample_monthly_gmv_raw", 0.0)
    adjusted_sample_monthly_gmv = section_13["bottom_up"].get("sample_monthly_gmv", 0.0)
    winsorization_sane = adjusted_sample_monthly_gmv <= raw_sample_monthly_gmv or raw_sample_monthly_gmv == 0
    checks.append(
        {
            "check_id": "market_size_winsorization_sanity",
            "status": _status(winsorization_sane),
            "source": SOURCE_REFERENCES["nist_iqr"],
            "method": "Winsorized bottom-up GMV should not exceed the raw sample GMV when used to reduce estimator spikes.",
            "evidence": {
                "raw_sample_monthly_gmv": raw_sample_monthly_gmv,
                "adjusted_sample_monthly_gmv": adjusted_sample_monthly_gmv,
            },
        }
    )

    first_channel = section_14.get("channels", [None])[0] if section_14.get("channels") else None
    conversion_formula_ok = False
    roas_formula_ok = False
    if first_channel:
        if first_channel["visits"]:
            expected_conversion = round(first_channel["orders"] / first_channel["visits"], 4)
            conversion_formula_ok = first_channel["conversion_rate"] == expected_conversion
        else:
            conversion_formula_ok = first_channel["conversion_rate"] is None
        if first_channel["roas"] is not None:
            expected_roas = round(first_channel["revenue"] / first_channel["ad_spend"], 2)
            roas_formula_ok = abs(first_channel["roas"] - expected_roas) <= 0.01
        else:
            roas_formula_ok = first_channel["ad_spend"] in (0, 0.0, None)
    checks.append(
        {
            "check_id": "conversion_rate_formula",
            "status": _status(
                conversion_formula_ok,
                review=first_channel is None or not first_channel["visits"],
            ),
            "source": SOURCE_REFERENCES["google_ads_conversion"],
            "method": "Conversion rate is modeled as orders divided by visits/interactions.",
            "evidence": {
                "channel": first_channel["channel"] if first_channel else None,
                "conversion_rate": first_channel["conversion_rate"] if first_channel else None,
                "missing_input": first_channel is None or not first_channel["visits"],
            },
        }
    )
    checks.append(
        {
            "check_id": "roas_formula",
            "status": _status(
                roas_formula_ok,
                review=first_channel is None or not first_channel["ad_spend"],
            ),
            "source": SOURCE_REFERENCES["google_ads_roas"],
            "method": "ROAS is modeled as revenue divided by ad spend.",
            "evidence": {
                "channel": first_channel["channel"] if first_channel else None,
                "roas": first_channel["roas"] if first_channel else None,
                "missing_input": first_channel is None or not first_channel["ad_spend"],
            },
        }
    )

    listed_outlier_method_ok = (
        section_15.get("outlier_analysis", {}).get("method") == "tukey_iqr_fences_1.5_3.0"
    )
    transaction_outlier_method_ok = (
        section_16.get("outlier_analysis", {}).get("method") == "tukey_iqr_fences_1.5_3.0"
    )
    checks.append(
        {
            "check_id": "price_outlier_method",
            "status": _status(listed_outlier_method_ok and transaction_outlier_method_ok),
            "source": SOURCE_REFERENCES["nist_iqr"],
            "method": "Price outlier handling uses IQR/Tukey fences before distribution analysis.",
            "evidence": {
                "listed_price_method": section_15.get("outlier_analysis", {}).get("method"),
                "transaction_price_method": section_16.get("outlier_analysis", {}).get("method"),
            },
        }
    )

    elasticity_method_ok = section_16.get("elasticity_method") == "midpoint_absolute"
    checks.append(
        {
            "check_id": "price_elasticity_method",
            "status": _status(elasticity_method_ok),
            "source": SOURCE_REFERENCES["openstax_elasticity"],
            "method": "Price elasticity uses the midpoint method to reduce base-point bias.",
            "evidence": {
                "elasticity_method": section_16.get("elasticity_method"),
                "elasticity_consistency_ratio": section_16.get("elasticity_consistency_ratio"),
            },
        }
    )

    pass_count = sum(1 for check in checks if check["status"] == "pass")
    review_count = sum(1 for check in checks if check["status"] == "review")
    fail_count = sum(1 for check in checks if check["status"] == "fail")

    return {
        "summary": {
            "pass_count": pass_count,
            "review_count": review_count,
            "fail_count": fail_count,
        },
        "checks": checks,
    }


PART2_SOURCE_REFERENCES = {
    "gmv_accounting": {
        "label": "Part 2 GMV Accounting",
        "url": "",
    },
    "price_distribution": {
        "label": "Part 2 Price Distribution and Sweet Spot",
        "url": "",
    },
    "attribute_outperformance": {
        "label": "Part 2 Attribute Outperformance",
        "url": "",
    },
    "review_sentiment": {
        "label": "Part 2 Review Sentiment",
        "url": "",
    },
    "survival_analysis": {
        "label": "Part 2 Listing Survival",
        "url": "",
    },
}


def build_part2_methodology_validation(report: dict) -> dict:
    section_21 = report["sections"]["2.1"]["metrics"]
    section_22 = report["sections"]["2.2"]["metrics"]
    section_24 = report["sections"]["2.4"]["metrics"]
    section_25 = report["sections"]["2.5"]["metrics"]
    section_26 = report["sections"]["2.6"]["metrics"]

    checks = []

    platform_mix = section_21.get("platform_mix", {})
    platform_sum = sum(platform_mix.values())
    checks.append(
        {
            "check_id": "platform_mix_integrity",
            "status": _status(abs(platform_sum - 1.0) <= 0.01, review=not platform_mix),
            "source": PART2_SOURCE_REFERENCES["gmv_accounting"],
            "method": "Platform GMV shares should reconcile back to 100% of observed GMV.",
            "evidence": {
                "platform_share_sum": round(platform_sum, 4),
                "missing_input": not bool(platform_mix),
            },
        }
    )

    brand_hhi = section_21.get("brand_hhi", 0.0)
    expected_level = _classify_hhi(brand_hhi)
    checks.append(
        {
            "check_id": "brand_concentration_thresholds",
            "status": _status(section_21.get("brand_concentration_level") == expected_level),
            "source": PART2_SOURCE_REFERENCES["gmv_accounting"],
            "method": "Brand concentration level should match HHI threshold classification.",
            "evidence": {
                "brand_hhi": brand_hhi,
                "expected_level": expected_level,
                "reported_level": section_21.get("brand_concentration_level"),
            },
        }
    )

    sweet_spot = section_22.get("sweet_spot_band", {})
    price_band_share = section_22.get("price_band_share", {})
    sweet_spot_consistent = True
    if sweet_spot and price_band_share:
        max_band = max(price_band_share, key=price_band_share.get)
        sweet_spot_consistent = sweet_spot.get("label") == max_band
    checks.append(
        {
            "check_id": "sweet_spot_consistency",
            "status": _status(sweet_spot_consistent, review=not price_band_share),
            "source": PART2_SOURCE_REFERENCES["price_distribution"],
            "method": "Sweet spot band should match the highest weighted price-band share.",
            "evidence": {
                "reported_sweet_spot": sweet_spot.get("label"),
                "max_share_band": max(price_band_share, key=price_band_share.get) if price_band_share else None,
                "missing_input": not bool(price_band_share),
            },
        }
    )

    discount_rate = (
        section_22.get("discount_depth", {}).get("weighted_average_discount_rate")
    )
    discount_ok = discount_rate is None or 0.0 <= discount_rate <= 1.0
    checks.append(
        {
            "check_id": "discount_rate_range",
            "status": _status(discount_ok, review=discount_rate is None),
            "source": PART2_SOURCE_REFERENCES["price_distribution"],
            "method": "Weighted average discount rate should stay within a 0-1 range.",
            "evidence": {
                "weighted_average_discount_rate": discount_rate,
            },
        }
    )

    price_realization_rate = section_22.get("price_realization_rate")
    realization_ok = price_realization_rate is None or 0.0 <= price_realization_rate <= 1.05
    checks.append(
        {
            "check_id": "price_realization_range",
            "status": _status(realization_ok, review=price_realization_rate is None),
            "source": PART2_SOURCE_REFERENCES["price_distribution"],
            "method": "Realized price as a share of listed price should remain within a realistic retail range.",
            "evidence": {
                "price_realization_rate": price_realization_rate,
            },
        }
    )

    attributes = section_24.get("top_attributes", [])
    attribute_ok = all(
        -1.0 <= item.get("outperformance", 0.0) <= 1.0
        and -1.0 <= item.get("adjusted_outperformance", 0.0) <= 1.0
        for item in attributes
    )
    checks.append(
        {
            "check_id": "attribute_outperformance_range",
            "status": _status(attribute_ok, review=not attributes),
            "source": PART2_SOURCE_REFERENCES["attribute_outperformance"],
            "method": "Attribute outperformance is a share delta and should remain between -1 and 1.",
            "evidence": {
                "attribute_count": len(attributes),
                "missing_input": not bool(attributes),
            },
        }
    )

    sentiment_mix = section_25.get("sentiment_mix", {})
    sentiment_sum = sum(sentiment_mix.values())
    checks.append(
        {
            "check_id": "sentiment_mix_integrity",
            "status": _status(abs(sentiment_sum - 1.0) <= 0.02, review=not sentiment_mix),
            "source": PART2_SOURCE_REFERENCES["review_sentiment"],
            "method": "Positive, neutral, and negative review shares should approximately reconcile to 100%.",
            "evidence": {
                "sentiment_share_sum": round(sentiment_sum, 4),
                "missing_input": not bool(sentiment_mix),
            },
        }
    )

    survival_curve = section_26.get("survival_curve", [])
    monotonic = all(
        survival_curve[index]["survival_rate"] <= survival_curve[index - 1]["survival_rate"]
        for index in range(1, len(survival_curve))
    )
    checks.append(
        {
            "check_id": "survival_curve_monotonicity",
            "status": _status(monotonic, review=not survival_curve),
            "source": PART2_SOURCE_REFERENCES["survival_analysis"],
            "method": "Kaplan-Meier style survival estimates should be non-increasing over time.",
            "evidence": {
                "curve_points": len(survival_curve),
                "missing_input": not bool(survival_curve),
            },
        }
    )

    exit_risk = section_26.get("price_band_exit_risk", {})
    exit_risk_ok = all(0.0 <= value <= 1.0 for value in exit_risk.values())
    checks.append(
        {
            "check_id": "exit_risk_range",
            "status": _status(exit_risk_ok, review=not exit_risk),
            "source": PART2_SOURCE_REFERENCES["survival_analysis"],
            "method": "Price-band exit risk is a rate and should remain within a 0-1 range.",
            "evidence": {
                "band_count": len(exit_risk),
                "missing_input": not bool(exit_risk),
            },
        }
    )

    pass_count = sum(1 for check in checks if check["status"] == "pass")
    review_count = sum(1 for check in checks if check["status"] == "review")
    fail_count = sum(1 for check in checks if check["status"] == "fail")

    return {
        "summary": {
            "pass_count": pass_count,
            "review_count": review_count,
            "fail_count": fail_count,
        },
        "checks": checks,
    }


PART3_SOURCE_REFERENCES = {
    "supply_structure": {
        "label": "Part 3 Supply Structure",
        "url": "",
    },
    "quote_structure": {
        "label": "Part 3 Quote Structure",
        "url": "",
    },
    "compliance_gating": {
        "label": "Part 3 Compliance Gating",
        "url": "",
    },
    "logistics_execution": {
        "label": "Part 3 Logistics Execution",
        "url": "",
    },
    "landed_cost": {
        "label": "Part 3 Landed Cost",
        "url": "",
    },
}


def build_part3_methodology_validation(report: dict) -> dict:
    section_31 = report["sections"]["3.1"]["metrics"]
    section_32 = report["sections"]["3.2"]["metrics"]
    section_33 = report["sections"]["3.3"]["metrics"]
    section_34 = report["sections"]["3.4"]["metrics"]
    section_35 = report["sections"]["3.5"]["metrics"]
    section_36 = report["sections"]["3.6"]["metrics"]
    section_37 = report["sections"]["3.7"]["metrics"]

    checks = []

    supplier_type_share = section_31.get("supplier_type_share", {})
    supplier_share_sum = sum(supplier_type_share.values())
    checks.append(
        {
            "check_id": "supplier_type_share_integrity",
            "status": _status(abs(supplier_share_sum - 1.0) <= 0.01, review=not supplier_type_share),
            "source": PART3_SOURCE_REFERENCES["supply_structure"],
            "method": "Supplier type shares should reconcile back to the full supplier pool.",
            "evidence": {
                "supplier_share_sum": round(supplier_share_sum, 4),
                "missing_input": not bool(supplier_type_share),
            },
        }
    )

    moq_curve = section_32.get("moq_curve", [])
    moq_curve_sorted = all(
        moq_curve[index]["moq_tier"] >= moq_curve[index - 1]["moq_tier"]
        for index in range(1, len(moq_curve))
    )
    checks.append(
        {
            "check_id": "moq_curve_order",
            "status": _status(moq_curve_sorted, review=not moq_curve),
            "source": PART3_SOURCE_REFERENCES["quote_structure"],
            "method": "MOQ tiers should be sorted ascending before interpreting the quote curve.",
            "evidence": {
                "curve_points": len(moq_curve),
                "missing_input": not bool(moq_curve),
            },
        }
    )

    risk_distribution = section_33.get("risk_distribution", {})
    risk_share_sum = sum(risk_distribution.values())
    checks.append(
        {
            "check_id": "compliance_risk_distribution_integrity",
            "status": _status(abs(risk_share_sum - 1.0) <= 0.02, review=not risk_distribution),
            "source": PART3_SOURCE_REFERENCES["compliance_gating"],
            "method": "Compliance risk distribution should approximately sum to 100% of tracked requirements.",
            "evidence": {
                "risk_share_sum": round(risk_share_sum, 4),
                "missing_input": not bool(risk_distribution),
            },
        }
    )

    best_routes = section_34.get("best_routes", [])
    routes_sorted = all(
        best_routes[index]["route_score"] <= best_routes[index - 1]["route_score"]
        for index in range(1, len(best_routes))
    )
    delay_rate = section_34.get("delay_rate")
    delay_rate_ok = delay_rate is None or 0.0 <= delay_rate <= 1.0
    checks.append(
        {
            "check_id": "route_score_order_and_delay_range",
            "status": _status(routes_sorted and delay_rate_ok, review=not best_routes),
            "source": PART3_SOURCE_REFERENCES["logistics_execution"],
            "method": "Recommended routes should be sorted by route_score, and delay rate must stay within a 0-1 range.",
            "evidence": {
                "route_count": len(best_routes),
                "delay_rate": delay_rate,
                "missing_input": not bool(best_routes),
            },
        }
    )

    best_scenario = section_35.get("best_scenario", {})
    monte_carlo = section_35.get("monte_carlo", {})
    margin_rate = best_scenario.get("net_margin_rate")
    landed_cost = best_scenario.get("landed_cost", 0.0)
    sell_price = section_35.get("target_sell_price", 0.0)
    landed_cost_ok = landed_cost <= sell_price
    margin_range_ok = margin_rate is not None and -1.0 <= margin_rate <= 1.0
    checks.append(
        {
            "check_id": "landed_cost_margin_range",
            "status": _status(landed_cost_ok and margin_range_ok, review=not best_scenario),
            "source": PART3_SOURCE_REFERENCES["landed_cost"],
            "method": "Best-scenario landed cost should not exceed the modeled sell price, and net margin rate must remain within a valid range.",
            "evidence": {
                "landed_cost": landed_cost,
                "sell_price": sell_price,
                "net_margin_rate": margin_rate,
                "missing_input": not bool(best_scenario),
            },
        }
    )

    percentile_bands = monte_carlo.get("percentile_bands", {}).get("net_margin_rate", {})
    monte_carlo_order_ok = (
        percentile_bands.get("p10", 0.0)
        <= percentile_bands.get("p50", 0.0)
        <= percentile_bands.get("p90", 0.0)
    ) if percentile_bands else False
    loss_probability = monte_carlo.get("loss_probability")
    loss_probability_ok = loss_probability is None or 0.0 <= loss_probability <= 1.0
    checks.append(
        {
            "check_id": "monte_carlo_percentile_order",
            "status": _status(monte_carlo_order_ok and loss_probability_ok, review=not percentile_bands),
            "source": PART3_SOURCE_REFERENCES["landed_cost"],
            "method": "Monte Carlo percentile bands should be monotonic and scenario loss probability must stay within a 0-1 range.",
            "evidence": {
                "percentile_bands": percentile_bands,
                "loss_probability": loss_probability,
                "missing_input": not bool(percentile_bands),
            },
        }
    )

    priority_risks = section_36.get("priority_risks", [])
    risk_scores_ok = all(0.0 <= row.get("severity_score", 0.0) <= 1.0 for row in priority_risks)
    checks.append(
        {
            "check_id": "risk_score_range",
            "status": _status(risk_scores_ok, review=not priority_risks),
            "source": PART3_SOURCE_REFERENCES["landed_cost"],
            "method": "Risk severity scores are normalized to a 0-1 range.",
            "evidence": {
                "risk_count": len(priority_risks),
                "missing_input": not bool(priority_risks),
            },
        }
    )

    recommendation = section_37.get("recommendation")
    recommendation_ok = recommendation in {"recommended_entry", "pilot_first", "hold"}
    checks.append(
        {
            "check_id": "entry_recommendation_enum",
            "status": _status(recommendation_ok, review=recommendation is None),
            "source": PART3_SOURCE_REFERENCES["landed_cost"],
            "method": "Entry recommendation should map to the fixed recommendation enum.",
            "evidence": {
                "recommendation": recommendation,
            },
        }
    )

    pass_count = sum(1 for check in checks if check["status"] == "pass")
    review_count = sum(1 for check in checks if check["status"] == "review")
    fail_count = sum(1 for check in checks if check["status"] == "fail")

    return {
        "summary": {
            "pass_count": pass_count,
            "review_count": review_count,
            "fail_count": fail_count,
        },
        "checks": checks,
    }
