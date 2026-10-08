"""Runnable setup: create the bucket, then mint an audit artifact URL."""
from lifecycle_service import demo_payload, evaluate, parse_event
from infrai_client import InfraiClient
from datetime import datetime, timezone


def main() -> None:
    # The call shape mirrors infrai.storage.object.presign.
    bucket = "fintech-throwaway"
    event = parse_event(demo_payload())
    decision = evaluate(event, datetime.now(timezone.utc))
    client = InfraiClient()
    client.ensure_bucket(bucket)
    try:
        signed = client.presign_get(bucket, event.artifact_key)
        print({"event_id": event.event_id, "action": decision.action, "notification": decision.notification, "url": signed.get("url")})
    finally:
        client.delete_bucket(bucket)


if __name__ == "__main__":
    main()
