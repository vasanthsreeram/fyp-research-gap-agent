"""Shared OpenAI-compatible client helpers + keychain lookup."""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

_LLM_AVAILABLE: Optional[bool] = None
_RESOLVED_KEY: Optional[str] = None

# Keychain service from overnight build brief
KEYCHAIN_SERVICE = "openclaw/tgcallskill/openai-api-key"
KEYCHAIN_ACCOUNTS = ("lintware", "openai", "default", "")


def resolve_openai_api_key() -> Optional[str]:
    """Resolve OPENAI_API_KEY from env, then macOS Keychain (never log the value)."""
    global _RESOLVED_KEY
    if _RESOLVED_KEY is not None:
        return _RESOLVED_KEY or None

    env_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if env_key:
        _RESOLVED_KEY = env_key
        return env_key

    for account in KEYCHAIN_ACCOUNTS:
        try:
            cmd = ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"]
            if account:
                cmd.extend(["-a", account])
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if proc.returncode == 0:
                key = (proc.stdout or "").strip()
                if key:
                    os.environ["OPENAI_API_KEY"] = key
                    _RESOLVED_KEY = key
                    logger.info("Loaded OpenAI API key from Keychain service %s", KEYCHAIN_SERVICE)
                    return key
        except Exception as e:
            logger.debug("Keychain lookup failed (account=%r): %s", account, e)

    _RESOLVED_KEY = ""
    return None


def llm_available() -> bool:
    """True if an OpenAI-compatible client can be constructed with a key."""
    global _LLM_AVAILABLE
    if _LLM_AVAILABLE is not None:
        return _LLM_AVAILABLE
    key = resolve_openai_api_key()
    if not key:
        _LLM_AVAILABLE = False
        return False
    try:
        from openai import OpenAI

        client = OpenAI(api_key=key, timeout=8)
        # Lightweight probe — list models can be slow/blocked; just construct is enough
        # if we have a key. A real call happens at extract time.
        _ = client
        _LLM_AVAILABLE = True
    except Exception:
        _LLM_AVAILABLE = False
    return _LLM_AVAILABLE


def get_client():
    """Return OpenAI client or raise."""
    key = resolve_openai_api_key()
    if not key:
        raise RuntimeError("No OPENAI_API_KEY available")
    from openai import OpenAI

    base = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE")
    if base:
        return OpenAI(api_key=key, base_url=base, timeout=60)
    return OpenAI(api_key=key, timeout=60)
