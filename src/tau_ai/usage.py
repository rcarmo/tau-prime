"""Provider-neutral token usage and deterministic pricing."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True, slots=True)
class ProviderUsage:
    """Token accounting reported for one provider response."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cache_write_1h_tokens: int = 0

    def __post_init__(self) -> None:
        values = (
            self.input_tokens,
            self.output_tokens,
            self.cache_read_tokens,
            self.cache_write_tokens,
            self.cache_write_1h_tokens,
        )
        if any(value < 0 for value in values):
            raise ValueError("Usage token counts must not be negative")


@dataclass(frozen=True, slots=True)
class UsagePricing:
    """USD rates per million tokens for one model."""

    input: Decimal
    output: Decimal
    cache_read: Decimal
    cache_write: Decimal
    cache_write_1h: Decimal | None = None


def usage_cost_microunits(usage: ProviderUsage, pricing: UsagePricing) -> int:
    """Calculate cost in millionths of a dollar.

    Anthropic reports one-hour writes as a subset of total cache writes. Clamp
    malformed over-reporting and retain the five-minute rate as the fallback
    for catalogs that predate the one-hour field.
    """
    one_hour = min(usage.cache_write_1h_tokens, usage.cache_write_tokens)
    five_minute = usage.cache_write_tokens - one_hour
    one_hour_rate = pricing.cache_write_1h or pricing.cache_write
    cost = (
        Decimal(usage.input_tokens) * pricing.input
        + Decimal(usage.output_tokens) * pricing.output
        + Decimal(usage.cache_read_tokens) * pricing.cache_read
        + Decimal(five_minute) * pricing.cache_write
        + Decimal(one_hour) * one_hour_rate
    )
    return int(cost.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
