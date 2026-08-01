"""Resolve academic API keys from env + macOS Keychain (never log values)."""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

_RESOLVED_S2: Optional[str] = None

# Prefer env; then openclaw-namespaced Keychain items (same pattern as OpenAI).
S2_ENV_VARS = ("S2_API_KEY", "SEMANTIC_SCHOLAR_API_KEY", "SEMANTICSCHOLAR_API_KEY")
S2_KEYCHAIN_SERVICES = (
    "openclaw/fyp/s2-api-key",
    "openclaw/fyp/semantic-scholar-api-key",
    "openclaw/semantic-scholar-api-key",
    "openclaw/s2-api-key",
)
S2_KEYCHAIN_ACCOUNTS = ("lintware", "fyp", "default", "vas", "")


def resolve_s2_api_key(*, force: bool = False) -> Optional[str]:
    """Return Semantic Scholar API key or None. Caches after first lookup."""
    global _RESOLVED_S2
    if not force and _RESOLVED_S2 is not None:
        return _RESOLVED_S2 or None

    for var in S2_ENV_VARS:
        val = (os.environ.get(var) or "").strip()
        if val:
            _RESOLVED_S2 = val
            # Normalize into primary env var for downstream clients
            os.environ.setdefault("S2_API_KEY", val)
            logger.info("S2 API key loaded from env %s", var)
            return val

    for service in S2_KEYCHAIN_SERVICES:
        for account in S2_KEYCHAIN_ACCOUNTS:
            try:
                cmd = ["security", "find-generic-password", "-s", service, "-w"]
                if account:
                    cmd.extend(["-a", account])
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if proc.returncode != 0:
                    continue
                key = (proc.stdout or "").strip()
                if not key:
                    continue
                os.environ["S2_API_KEY"] = key
                _RESOLVED_S2 = key
                logger.info(
                    "S2 API key loaded from Keychain service=%s account=%s",
                    service,
                    account or "(none)",
                )
                return key
            except Exception as e:
                logger.debug("S2 keychain miss service=%s account=%r: %s", service, account, e)

    _RESOLVED_S2 = ""
    logger.info(
        "No S2 API key found (env %s or Keychain %s) — live ingest will use unauthenticated rate limits",
        "/".join(S2_ENV_VARS[:2]),
        S2_KEYCHAIN_SERVICES[0],
    )
    return None


def s2_key_status() -> dict[str, object]:
    """Non-secret status for CLI/diagnostics."""
    key = resolve_s2_api_key()
    source = "none"
    if key:
        if any((os.environ.get(v) or "").strip() == key for v in S2_ENV_VARS):
            # Could still be keychain-injected into env; report presence only
            source = "env_or_keychain"
        else:
            source = "resolved"
    return {
        "present": bool(key),
        "source": source if key else "none",
        "hint": (
            "export S2_API_KEY=... or store in Keychain: "
            "security add-generic-password -s 'openclaw/fyp/s2-api-key' -a lintware -w"
        ),
    }
