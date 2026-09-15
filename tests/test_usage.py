from decimal import Decimal

import pytest

from tau_ai.anthropic import _anthropic_usage
from tau_ai.usage import ProviderUsage, UsagePricing, usage_cost_microunits
from tau_coding.provider_catalog import catalog_model_pricing


def test_anthropic_usage_extracts_one_hour_cache_creation_breakdown() -> None:
    usage = _anthropic_usage(
        {
            "input_tokens": 100,
            "output_tokens": 20,
            "cache_read_input_tokens": 30,
            "cache_creation_input_tokens": 40,
            "cache_creation": {
                "ephemeral_5m_input_tokens": 25,
                "ephemeral_1h_input_tokens": 15,
            },
        }
    )

    assert usage == ProviderUsage(
        input_tokens=100,
        output_tokens=20,
        cache_read_tokens=30,
        cache_write_tokens=40,
        cache_write_1h_tokens=15,
    )


def test_usage_prices_one_hour_cache_writes_separately() -> None:
    pricing = UsagePricing(
        input=Decimal("3"),
        output=Decimal("15"),
        cache_read=Decimal("0.30"),
        cache_write=Decimal("3.75"),
        cache_write_1h=Decimal("6"),
    )
    usage = ProviderUsage(
        input_tokens=100,
        output_tokens=20,
        cache_read_tokens=50,
        cache_write_tokens=40,
        cache_write_1h_tokens=10,
    )

    assert usage_cost_microunits(usage, pricing) == 788


def test_usage_pricing_falls_back_for_old_catalogs_and_caps_one_hour_subset() -> None:
    pricing = UsagePricing(
        input=Decimal("0"),
        output=Decimal("0"),
        cache_read=Decimal("0"),
        cache_write=Decimal("2"),
    )

    assert (
        usage_cost_microunits(
            ProviderUsage(cache_write_tokens=5, cache_write_1h_tokens=20),
            pricing,
        )
        == 10
    )


def test_usage_aggregation_preserves_cache_write_breakdown() -> None:
    assert ProviderUsage(input_tokens=3, cache_write_tokens=7) + ProviderUsage(
        output_tokens=5,
        cache_write_tokens=11,
        cache_write_1h_tokens=2,
    ) == ProviderUsage(
        input_tokens=3,
        output_tokens=5,
        cache_write_tokens=18,
        cache_write_1h_tokens=2,
    )


def test_catalog_pricing_is_exact_and_unknown_models_remain_unpriced() -> None:
    pricing = catalog_model_pricing("anthropic", "claude-sonnet-4-6")

    assert pricing is not None
    assert pricing.cache_write == Decimal("3.75")
    assert pricing.cache_write_1h == Decimal("6")
    assert catalog_model_pricing("anthropic", "claude-future") is None
    assert catalog_model_pricing("custom-anthropic", "claude-sonnet-4-6") is None


def test_usage_rejects_negative_counts() -> None:
    with pytest.raises(ValueError, match="negative"):
        ProviderUsage(cache_write_1h_tokens=-1)
