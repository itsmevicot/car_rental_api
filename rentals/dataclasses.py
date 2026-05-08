"""Domain dataclasses for the rentals domain."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RentalReturnResult:
    """Value object returned by the rental return flow.

    Carries the updated rental, the points awarded, and the reward transaction
    identifier so callers can act on any of these without additional queries.
    """

    rental: object
    points_earned: int
    reward_transaction_id: UUID
