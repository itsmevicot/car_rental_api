"""Tests for reward serializers."""

from types import SimpleNamespace

from rest_framework import serializers

from rewards.serializers import RewardRedeemSerializer


def test_reward_redeem_serializer_requires_customer_email_for_staff() -> None:
    serializer = RewardRedeemSerializer(
        data={"rental_id": "0192d5e0-7a1a-7b3a-8c4d-1234567890ab", "points_to_redeem": 100},
        context={"request": SimpleNamespace(user=SimpleNamespace(is_staff=True))},
    )
    assert serializer.is_valid() is False
    assert serializer.errors == {
        "customer_email": [
            serializers.ErrorDetail(
                string="This field is required when redeeming as staff.", code="invalid"
            )
        ]
    }
