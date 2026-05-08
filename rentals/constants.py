"""Business constants for the car rental application."""

from decimal import Decimal

# Rental discounts
DISCOUNT_THRESHOLD_WEEK: int = 7
DISCOUNT_THRESHOLD_SHORT: int = 3
DISCOUNT_RATE_WEEK: Decimal = Decimal("0.10")
DISCOUNT_RATE_SHORT: Decimal = Decimal("0.05")

# Late fees
LATE_FEE_MULTIPLIER: Decimal = Decimal("2.0")

# Car category thresholds
STANDARD_RATE_MIN: Decimal = Decimal("300.00")
PREMIUM_RATE_MIN: Decimal = Decimal("500.00")

# Reward points
BASE_POINTS_PER_DAY: int = 10
STANDARD_BONUS_PER_DAY: int = 5
PREMIUM_BONUS_PER_DAY: int = 10

# Duration bonuses
WEEK_BONUS_DAYS: int = 7
WEEK_BONUS_POINTS: int = 50
EXTENDED_BONUS_DAYS: int = 14
EXTENDED_BONUS_POINTS: int = 150

# On-time return bonus
ON_TIME_BONUS: int = 25

# Tier thresholds (based on lifetime earned points)
SILVER_THRESHOLD: int = 500
GOLD_THRESHOLD: int = 1000

# Tier multipliers
BRONZE_MULTIPLIER: Decimal = Decimal("1.0")
SILVER_MULTIPLIER: Decimal = Decimal("1.25")
GOLD_MULTIPLIER: Decimal = Decimal("1.5")

# Point redemption
POINTS_PER_DISCOUNT: int = 100
DISCOUNT_VALUE: Decimal = Decimal("50.00")
MIN_REDEEM_POINTS: int = 100
