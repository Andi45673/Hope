# HOPE Navigator

**Status:** BOOTSTRAP / HOLD — no deployed service or production release.

This repository is the independent source home for HOPE, the user's orchestration and personal navigation system. It is **not** the MyBook or Game Builder repository. The first bootstrap implementation is developed on an isolated feature branch and requires review before any merge.

## Trust ownership and stable identities

- Global user authority: `ANDI-USER-AUTHORITY`.
- HOPE Director: `HOPE-DIR-001` (reserved in canonical registry, not active).
- Central SSID read gateway: `HOPE-SSID-READER-001` (reserved; service account has Google Sheet Reader ACL, but no authenticated runtime probe).
- Single SSID truth: [AAF_SSID_Archive_Chat_Asset_Index](https://docs.google.com/spreadsheets/d/14gCpTfUNtcv-2_JYR1h5CtU2HmdtziOUadfxn9aaaks/edit).
- GitHub repository identity: `Andi45673/Hope` (repository ID `1411999594`).

HOPE components must fail closed for missing, duplicate or unverifiable SSIDs, and cannot create historical SSIDs or promote themselves. No Google private keys, user credentials or live registry writes in this repository.

**Gate:** review, independent tests, authenticated read-only Google Sheets proof, verified runtime identity and explicit user release approval. Until then HOPE remains `PLANNED / INACTIVE / HOLD`.
