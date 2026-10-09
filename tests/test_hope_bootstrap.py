"""No cloud network or credentials: deterministic bootstrap regression gates."""

import json
import unittest
from urllib.error import URLError
from unittest.mock import patch

from hope.director import HopeDirector
from hope.ssid_gateway import (
    API_URL, HEADER, RegistryError, parse_registry, read_live_snapshot
)


def record(ssid, *, parent="", owner="", scope="GLOBAL", status="HOLD"):
    values = {x: "" for x in HEADER}
    values.update({
        "System_SSID": ssid,
        "Parent_SSID": parent,
        "Owner_SSID": owner,
        "Scope": scope,
        "Runtime_State": "INACTIVE",
        "Card_Status": status,
    })
    return [values[key] for key in HEADER]


def valid_document():
    return {"values": [
        list(HEADER),
        record("ANDI-USER-AUTHORITY"),
        record("HOPE-DIR-001", parent="ANDI-USER-AUTHORITY",
               owner="ANDI-USER-AUTHORITY", scope="HOPE_SYSTEM"),
        record("HOPE-SSID-READER-001", parent="HOPE-DIR-001",
               owner="HOPE-DIR-001", scope="HOPE_SYSTEM"),
    ]}


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, max_bytes):
        return self.payload[:max_bytes]


class RegistryTests(unittest.TestCase):
    def test_valid_snapshot(self):
        obj = parse_registry(valid_document())
        self.assertEqual(obj.require("HOPE-DIR-001")["Runtime_State"], "INACTIVE")

    def test_missing_authority_fails(self):
        d = valid_document()
        d["values"].pop(1)
        with self.assertRaises(RegistryError):
            parse_registry(d)

    def test_duplicate_ssid_fails(self):
        d = valid_document()
        d["values"].append(d["values"][2].copy())
        with self.assertRaisesRegex(RegistryError, "duplicate"):
            parse_registry(d)

    def test_missing_ssid_record_fails(self):
        d = valid_document()
        d["values"].append(record(""))
        with self.assertRaisesRegex(RegistryError, "without SSID"):
            parse_registry(d)

    def test_schema_drift_fails(self):
        d = valid_document()
        d["values"][0][3] = "Parent_Fake"
        with self.assertRaisesRegex(RegistryError, "schema drift"):
            parse_registry(d)

    def test_wrong_reader_owner_fails(self):
        d = valid_document()
        d["values"][3][HEADER.index("Owner_SSID")] = "BOOK-DIR-001"
        with self.assertRaisesRegex(RegistryError, "owner mismatch"):
            parse_registry(d)

    def test_wrong_director_parent_fails(self):
        d = valid_document()
        d["values"][2][HEADER.index("Parent_SSID")] = "BOOK-DIR-001"
        with self.assertRaises(RegistryError):
            parse_registry(d)

    def test_wrong_reader_scope_fails(self):
        d = valid_document()
        d["values"][3][HEADER.index("Scope")] = "MYBOOK_SYSTEM"
        with self.assertRaises(RegistryError):
            parse_registry(d)

    def test_empty_response_fails(self):
        with self.assertRaises(RegistryError):
            parse_registry({"values": []})

    def test_registry_data_immutable(self):
        snapshot = parse_registry(valid_document())
        with self.assertRaises(TypeError):
            snapshot.objects["NEW"] = {}
        with self.assertRaises(TypeError):
            snapshot.require("HOPE-DIR-001")["Runtime_State"] = "ACTIVE"

    def test_https_get_only_and_token_not_leaked(self):
        captured = []
        def opener(request, *, timeout):
            captured.append((request, timeout))
            return FakeResponse(valid_document())
        with patch.dict("os.environ", {}, clear=True):
            snapshot = read_live_snapshot("ephemeral-token", opener=opener)
        self.assertIn("HOPE-DIR-001", snapshot.objects)
        request, timeout = captured[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.full_url, API_URL)
        self.assertEqual(timeout, 20)
        self.assertEqual(request.get_header("Authorization"), "Bearer ephemeral-token")

    def test_network_failure_fails_closed(self):
        def opener(*args, **kwargs):
            raise URLError("network unavailable")
        with self.assertRaisesRegex(RegistryError, "Unable to authenticate"):
            read_live_snapshot("ephemeral-token", opener=opener)

    def test_missing_token_fails_closed(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RegistryError, "token is required"):
                read_live_snapshot()

    def test_token_with_whitespace_is_rejected(self):
        with self.assertRaises(RegistryError):
            read_live_snapshot("bad token")

    def test_registry_beyond_row_500_still_scanned(self):
        d = valid_document()
        for idx in range(600):
            d["values"].append(record(f"FAKE-UNREGISTERED-{idx:03}"))
        d["values"].append(d["values"][2].copy())
        with self.assertRaisesRegex(RegistryError, "duplicate"):
            parse_registry(d)


class DirectorTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = parse_registry(valid_document())

    def test_director_never_self_promotes(self):
        r = HopeDirector(self.snapshot).propose(
            agent_ssid="HOPE-SSID-READER-001", capability="ssid.read"
        )
        self.assertFalse(r.allowed)
        self.assertEqual(r.reason, "HOPE_RUNTIME_HOLD")

    def test_unknown_agent_fails_closed(self):
        with self.assertRaisesRegex(RegistryError, "Unknown"):
            HopeDirector(self.snapshot).propose(
                agent_ssid="MISSING-AGENT", capability="calendar.read"
            )

    def test_missing_capability_fails_closed(self):
        with self.assertRaises(RegistryError):
            HopeDirector(self.snapshot).propose(
                agent_ssid="HOPE-SSID-READER-001", capability=""
            )

    def test_cross_owner_not_authorized(self):
        d = valid_document()
        d["values"].append(record("BOOK-UNVERIFIED-TEST", parent="BOOK-DIR-001",
                                 owner="BOOK-DIR-001", scope="MYBOOK_SYSTEM"))
        snapshot = parse_registry(d)
        r = HopeDirector(snapshot).propose(
            agent_ssid="BOOK-UNVERIFIED-TEST", capability="repo.write"
        )
        self.assertFalse(r.allowed)
        self.assertEqual(r.reason, "OWNER_NOT_AUTHORIZED")


if __name__ == "__main__":
    unittest.main()
