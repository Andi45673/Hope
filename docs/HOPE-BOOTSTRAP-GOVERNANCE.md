# HOPE Bootstrap Governance — HOLD

## Source authorities (9 October 2026)

| Item | Verified or reserved identity | Source of authority |
|---|---|---|
| HOPE Repository | `Andi45673/Hope` (ID 1411999594) | GitHub repository |
| User authority | `ANDI-USER-AUTHORITY` | AAF Google SSID registry |
| Director | `HOPE-DIR-001` | AAF Google SSID registry, reserved |
| Read-only SSID gateway | `HOPE-SSID-READER-001` | AAF Google SSID registry, reserved |
| Google identity | `hope-ssid-reader@spieleengine.iam.gserviceaccount.com` | GCP Cloud Shell creation output; file share independently verified |
| SSID master | `14gCpTfUNtcv-2_JYR1h5CtU2HmdtziOUadfxn9aaaks` | Native Google Sheet |

Current identity `Source_SHA` is not a runtime deployment SHA. The central Google Sheet is the
**single authoritative SSID registry**; local snapshots are ephemeral read-only derivatives.

## Authority diagram

User (`ANDI-USER-AUTHORITY`) -> HOPE Director (`HOPE-DIR-001`)
-> HOPE SSID gateway (`HOPE-SSID-READER-001`)
-> Google Sheet `System_Objects` (read only).

Director must neither invent agent IDs nor claim permission from a string.
Agent routing requires existing canonical SSID, owner, capability ACL,
runtime authentication, independent Protector QA, evidence and explicit release gate.
Until those capabilities exist, all proposals return HOLD.

## Strict gates

1. Source provenance: repository commit / SHA, registry SSID and referenced path, matching owner.
2. Independent offline tests: schema, unknown IDs, duplicates, parent/owner drift, missing bearer token, no write.
3. Independent Google OIDC provider scoped to Hope repo **ID 1411999594**, owner **ID 325983916** and approved workflow.
4. `roles/iam.workloadIdentityUser` only on the dedicated HOPE service account.
5. Live Google Sheets **read-only** OAuth scope and authenticated GET.
6. Agent and runtime contract/registry integration, independent Protector tests, rollback/known-good.
7. Formal promotion authorization only after existing release holds and independent gates are resolved.

Items 3–7 remain unverified. Do not report READY, VERIFIED_RUNTIME, or DEPLOYED based on repo source alone.

## Explicit exclusions

- No publishing secrets, service-account key JSON, or tokens.
- No direct writing to Google Sheets by ordinary agents.
- No booking, email sending, calendar changes or deployment from this bootstrap.
- No cross-engine authority from MyBook or Game Builder IDs.
- No GitHub repository identity claims without verification.
- No silent status promotion or auto-write to the canonical registry.

## Local offline validation

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
```

An eventual OIDC-protected proof can supply `GOOGLE_OAUTH_ACCESS_TOKEN` transiently:
```bash
PYTHONPATH=src python tools/hope_ssid_probe.py --live
```
Do not paste this token into an issue, PR, log or chat. The probe only prints PASS/HOLD information.
