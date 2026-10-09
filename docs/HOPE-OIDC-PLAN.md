# Separate HOPE OIDC plan (NOT YET APPLIED)

The existing provider `github/providers/videospiele` belongs only to Game Builder;
`github/providers/mybook` belongs only to MyBook. Do not broaden either.

A dedicated `github/providers/hope` must be created and constrained to repository
ID `1411999594`, owner ID `325983916`, the approved feature/ref and a manual
`workflow_dispatch` proof file. It must use issuer
`https://token.actions.githubusercontent.com` and mapping for
`google.subject`, `attribute.repository_id`, `attribute.repository_owner_id`,
`attribute.ref`, `attribute.event_name`, and `attribute.workflow_ref`.

Grant `roles/iam.workloadIdentityUser` on
`hope-ssid-reader@spieleengine.iam.gserviceaccount.com` to
`principalSet://iam.googleapis.com/projects/957694117473/locations/global/workloadIdentityPools/github/attribute.repository_id/1411999594`.
This is a future step requiring explicit operator execution in Cloud Shell.
Do not grant this principal to MyBook or Game Builder accounts.

An approved **read-only** proof workflow should request short-lived
`https://www.googleapis.com/auth/spreadsheets.readonly` token, call
`PYTHONPATH=src python tools/hope_ssid_probe.py --live` and verify
`LIVE_SHEET_READ_PASS_NOT_RUNTIME_INTEGRATION`.
Its manual dispatch may require a separate inert default-branch workflow.

The current bootstrap workflow runs only credential-free offline checks.
No Google Cloud IAM change or OAuth test has been performed by this branch.
