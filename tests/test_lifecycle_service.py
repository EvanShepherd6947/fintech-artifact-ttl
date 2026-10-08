from datetime import datetime, timezone

from src.lifecycle_service import evaluate, parse_event


def test_expired_high_risk_payment_is_sent_to_review():
    event = parse_event({"event_id": "p1", "occurred_at": "2026-09-01T00:00:00Z", "risk_score": 0.9, "artifact_key": "p1.json"})
    decision = evaluate(event, datetime(2026, 9, 2, tzinfo=timezone.utc))
    assert decision.expired is True
    assert decision.action == "review"
    assert "p1" in decision.notification
