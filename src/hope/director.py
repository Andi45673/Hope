"""Inactive HOPE director: identity-based intent routing proposals only.

No autonomous actions, deployments, agent installation, service-account
impersonation, or SSID mutations are permitted by this bootstrap.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ssid_gateway import RegistryError, RegistrySnapshot


@dataclass(frozen=True)
class RoutingDecision:
    candidate_ssid: str
    requested_capability: str
    allowed: bool
    reason: str


class HopeDirector:
    DIRECTOR_SSID = "HOPE-DIR-001"

    def __init__(self, snapshot: RegistrySnapshot) -> None:
        self._snapshot = snapshot
        director = snapshot.require(self.DIRECTOR_SSID)
        if director["Owner_SSID"] != "ANDI-USER-AUTHORITY":
            raise RegistryError("Invalid director authority")

    def propose(self, *, agent_ssid: str, capability: str) -> RoutingDecision:
        if not agent_ssid or not capability or not capability.strip():
            raise RegistryError("Routing requires a registered SSID and capability")
        candidate = self._snapshot.require(agent_ssid)
        # A centrally reserved ID or ACTIVE string is not authorization.
        # No runtime owner/capability policy or signed release exists yet.
        if candidate["Owner_SSID"] not in ("HOPE-DIR-001", "ANDI-USER-AUTHORITY"):
            return RoutingDecision(agent_ssid, capability, False, "OWNER_NOT_AUTHORIZED")
        return RoutingDecision(agent_ssid, capability, False, "HOPE_RUNTIME_HOLD")
