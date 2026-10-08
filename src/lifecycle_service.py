"""TTL decision and audit notification for throwaway payment artifacts."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class PaymentEvent:
    event_id: str
    occurred_at: datetime
    risk_score: float
    artifact_key: str


@dataclass(frozen=True)
class LifecycleDecision:
    expired: bool
    action: str
    notification: str


def evaluate(event: PaymentEvent, now: datetime, ttl: timedelta = timedelta(hours=24)) -> LifecycleDecision:
    expired = now >= event.occurred_at + ttl
    if not expired:
        return LifecycleDecision(False, "retain", f"payment {event.event_id}: retained")
    action = "review" if event.risk_score >= 0.7 else "delete"
    return LifecycleDecision(True, action, f"payment {event.event_id}: expired; action={action}")


def parse_event(data: dict) -> PaymentEvent:
    return PaymentEvent(
        event_id=str(data["event_id"]),
        occurred_at=datetime.fromisoformat(data["occurred_at"].replace("Z", "+00:00")),
        risk_score=float(data["risk_score"]),
        artifact_key=str(data["artifact_key"]),
    )


def demo_payload() -> dict:
    return {"event_id": "pay_1042", "occurred_at": "2026-09-03T08:00:00+00:00", "risk_score": 0.82, "artifact_key": "payments/pay_1042.json"}


if __name__ == "__main__":
    event = parse_event(demo_payload())
    decision = evaluate(event, datetime(2026, 9, 4, 8, tzinfo=timezone.utc))
    print(decision.notification)
