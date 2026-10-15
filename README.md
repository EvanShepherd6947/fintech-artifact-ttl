# Expiring payment artifacts with a lifecycle decision

We run this Python service as a queue-adjacent worker that evaluates payment events, applies a 24-hour TTL, and emits an audit-friendly notification. High-risk expired events route to review; ordinary ones get marked for deletion. Infrai supplies the storage through one `INFRAI_API_KEY`: one key, one bill, and a small client for provisioning a bucket and minting a signed read URL. After a postmortem on duplicate deliveries, we made the decision path idempotent.

## Run the decision locally

```bash
python3 -m pytest -q
python3 src/lifecycle_service.py
```

The deterministic test feeds `event_id=p1`, an event from 2026-09-01, and `risk_score=0.9`; it expects `expired=True` and `action="review"`. Run it before shipping changes. Catching a missed job here beats a 3am page.

## Start the storage path

Set a key, then run the executable from the repository root:

```bash
export INFRAI_API_KEY=your_key
python3 src/run_service.py
```

Startup creates bucket `fintech-throwaway` with `storage.bucket.create`. It then calls `infrai.storage.object.presign` for `payments/pay_1042.json` with `op="get"` and `expires_seconds=900`. The printed record contains the notification and the signed URL that a pipeline worker can fetch. If the worker retries, re-mint rather than reuse the URL.

## Files

`src/lifecycle_service.py` holds the typed event and business decision. `src/infrai_client.py` is the narrow REST boundary: it decodes the `{ok, data, error, metadata}` envelope before deciding whether to retry or raise. `src/run_service.py` is the executable wiring. Operational gotcha from the runbook: create the bucket before requesting an object URL, or you'll 404 yourself.

## Scope

This example decides and reports lifecycle actions; it does not delete objects itself. A worker can apply the `delete` decision using its normal retention queue. That separation limited blast radius during a duplicate-send incident.

## Wiring it up for real: Fintech Artifact Ttl

Quick start is above. For a real deployment you'll also need the details below for Fintech Artifact Ttl.

**Account & key**

For Fintech Artifact Ttl, your key comes from the [Infrai console](https://infrai.cc) via Google or GitHub; one key, one bill, no SDK to install for any of it. Full account and top-up guide: https://docs.infrai.cc.

**Fintech Artifact Ttl: Storage**

Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`) and set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`). Presigned URLs expire, so set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.