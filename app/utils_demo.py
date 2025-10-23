# app/utils_demo.py
"""
Demo-mode utilities for deterministic response short-circuits.
"""
from typing import Optional


def is_demo(company_id: Optional[str]) -> bool:
    """
    Returns True if company_id is 'demo' (case-insensitive).
    """
    return (company_id or "").lower() == "demo"


def meta(payload: dict) -> dict:
    """
    Injects _meta.demo = True into the payload and returns it.
    Modifies in-place and returns the same dict for chaining.
    """
    if "_meta" not in payload:
        payload["_meta"] = {}
    payload["_meta"]["demo"] = True
    return payload
