"""Fail-closed, read-only adapter to the one canonical AAF SSID Google Sheet.

This code does NOT grant permissions, create or mutate SSIDs, or deploy HOPE.
It requires a short-lived bearer token supplied by a trusted runtime (OIDC).
No private key or refresh token is ever stored or logged.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

SHEET_ID = "14gCpTfUNtcv-2_JYR1h5CtU2HmdtziOUadfxn9aaaks"
SHEET_RANGE = "System_Objects!A:S"  # entire used column range; never an A1:S500 truncation
API_URL = (
    "https://sheets.googleapis.com/v4/spreadsheets/"
    + SHEET_ID + "/values/" + quote(SHEET_RANGE, safe="")
)
HEADER = (
    "System_SSID", "Object_Type", "Canonical_Name", "Parent_SSID",
    "Owner_SSID", "Scope", "Source_Repository", "Source_Branch",
    "Source_Path", "Source_SHA", "Source_JSON_Path", "Source_Reference",
    "Development_State", "Integration_State", "Canonical_State",
    "Runtime_State", "Card_Status", "Last_Verified_At", "Notes",
)
MANDATORY = frozenset({
    "ANDI-USER-AUTHORITY", "HOPE-DIR-001", "HOPE-SSID-READER-001",
})


class RegistryError(RuntimeError):
    """A validation or authentication failure: never continue with stale identity data."""


@dataclass(frozen=True)
class RegistrySnapshot:
    """Validated immutable view; cannot be used to perform any write."""

    objects: Mapping[str, Mapping[str, str]]

    def require(self, ssid: str) -> Mapping[str, str]:
        if not ssid or ssid not in self.objects:
            raise RegistryError("Unknown or missing canonical SSID")
        return self.objects[ssid]


def parse_registry(raw: dict) -> RegistrySnapshot:
    if not isinstance(raw, dict) or not isinstance(raw.get("values"), list):
        raise RegistryError("Google Sheets response lacks a values array")
    rows = raw["values"]
    if not rows or tuple(rows[0]) != HEADER:
        raise RegistryError("Canonical registry schema drift")
    found: dict[str, Mapping[str, str]] = {}
    for row_num, row in enumerate(rows[1:], start=2):
        if not isinstance(row, list):
            raise RegistryError(f"Malformed row {row_num}")
        if not row or not any(cell != "" for cell in row):
            continue
        if len(row) > len(HEADER) or not all(isinstance(v, str) for v in row):
            raise RegistryError(f"Malformed columns in row {row_num}")
        values = row + [""] * (len(HEADER) - len(row))
        ssid = values[0].strip()
        if not ssid:
            raise RegistryError(f"Record without SSID at row {row_num}")
        if ssid != values[0] or ssid in found:
            raise RegistryError(f"Invalid or duplicate SSID at row {row_num}")
        found[ssid] = MappingProxyType(dict(zip(HEADER, values)))
    if not MANDATORY.issubset(found):
        raise RegistryError("Required HOPE or authority SSIDs missing")
    director = found["HOPE-DIR-001"]
    reader = found["HOPE-SSID-READER-001"]
    if director["Parent_SSID"] != "ANDI-USER-AUTHORITY":
        raise RegistryError("HOPE director authority parent mismatch")
    if director["Owner_SSID"] != "ANDI-USER-AUTHORITY":
        raise RegistryError("HOPE director owner mismatch")
    if reader["Parent_SSID"] != "HOPE-DIR-001":
        raise RegistryError("Reader must be owned by HOPE hierarchy")
    if reader["Owner_SSID"] != "HOPE-DIR-001":
        raise RegistryError("Reader owner mismatch")
    if reader["Scope"] != "HOPE_SYSTEM" or director["Scope"] != "HOPE_SYSTEM":
        raise RegistryError("HOPE scope mismatch")
    return RegistrySnapshot(MappingProxyType(found))


def read_live_snapshot(access_token: str | None = None, *, opener=urlopen) -> RegistrySnapshot:
    """HTTPS GET only. The token is never printed, stored or written."""
    token = access_token if access_token is not None else os.environ.get("GOOGLE_OAUTH_ACCESS_TOKEN", "")
    if not token or any(ch.isspace() for ch in token):
        raise RegistryError("A valid short-lived Google OAuth access token is required")
    request = Request(
        API_URL,
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        method="GET",
    )
    try:
        with opener(request, timeout=20) as response:
            if response.status != 200:
                raise RegistryError("Canonical Google Sheet request failed")
            data = response.read(5_000_001)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        # Do not surface exception text: some HTTP clients include request details.
        raise RegistryError("Unable to authenticate and read canonical SSID registry") from None
    if len(data) > 5_000_000:
        raise RegistryError("Registry response larger than configured safety limit")
    try:
        document = json.loads(data)
    except (ValueError, UnicodeDecodeError):
        raise RegistryError("Registry response is not JSON") from None
    return parse_registry(document)
