"""Business constants for the rewards domain."""

from decimal import Decimal

BASE_POINTS_PER_DAY: int = 10
STANDARD_BONUS_PER_DAY: int = 5
PREMIUM_BONUS_PER_DAY: int = 10
WEEK_BONUS_DAYS: int = 7
WEEK_BONUS_POINTS: int = 50
EXTENDED_BONUS_DAYS: int = 14
EXTENDED_BONUS_POINTS: int = 150
ON_TIME_BONUS: int = 25
SILVER_THRESHOLD: int = 500
GOLD_THRESHOLD: int = 1000
BRONZE_MULTIPLIER: Decimal = Decimal("1.0")
SILVER_MULTIPLIER: Decimal = Decimal("1.25")
GOLD_MULTIPLIER: Decimal = Decimal("1.5")
POINTS_PER_DISCOUNT: int = 100
DISCOUNT_VALUE: Decimal = Decimal("50.00")
MIN_REDEEM_POINTS: int = 100

# History query param validation sets
ALLOWED_EXPORT_FORMATS: frozenset[str] = frozenset({"csv", "pdf"})
ALLOWED_TYPES: frozenset[str] = frozenset({"earned", "redeemed"})
ALLOWED_ORDERING: frozenset[str] = frozenset({"created_at", "points", "type"})
