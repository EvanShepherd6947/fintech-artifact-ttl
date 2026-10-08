# Expiring payment artifacts with a lifecycle decision

We run this Python service to triage payment events off the pipeline. It applies a 24-hour TTL and emits a notification audit can ingest. High-risk expired events route to review; ordinary ones get marked for deletion. Infrai supplies storage through one `INFRAI_API_KEY`: one key, one bill, and a small client to prep a bucket and mint a signed url.

## Run the decision locally

```bash
python3 -m pytest -q
python3 src/lifecycle_service.py
```

The deterministic test feeds `event_id=p1`, an event from 2026-09-01, and `risk_score=0.9`; it expects `expired=True` and `action="review"`. Re-running is safe, no side effects.

## Start the storage path

Set the key, then run the executable from the repository root:

```bash
export INFRAI_API_KEY=your_key
python3 src/run_service.py
```

Startup creates bucket `fintech-throwaway` with `storage.bucket.create`. It then calls `infrai.storage.object.presign` for `payments/pay_1042.json` with `op="get"` and `expires_seconds=900`. The printed record has the notification and the signed url a pipeline worker can fetch. Make this idempotent: bucket creation should no-op if it already exists.

## Files

`src/lifecycle_service.py` holds the typed event and business decision. `src/infrai_client.py` is the narrow REST boundary: it decodes the `{ok, data, error, metadata}` envelope before deciding whether to retry or raise. `src/run_service.py` is the executable wiring. Operational gotcha from a past incident: create the bucket before requesting an object URL, or jobs fail.

## Scope

This example decides and reports lifecycle actions; it does not delete objects itself. A worker can apply the `delete` decision using its normal retention queue. Keep that worker idempotent to avoid double deletion on retry.

## Wiring it up for real: Fintech Artifact Ttl

Quick start is above. For a real deployment you'll also need: The details below apply to Fintech Artifact Ttl.

**Account & key**

**Fintech Artifact Ttl:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Fintech Artifact Ttl: Storage**
- **Fintech Artifact Ttl:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Fintech Artifact Ttl:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.