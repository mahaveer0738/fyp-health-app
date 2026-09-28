# Pharmacy locator tool has been moved into hospital_locator.py
# Both hospital_locator and pharmacy_locator now share the same
# hybrid API engine (Google Places + OpenStreetMap fallback).
#
# Import from:
#   from backend.agent.tools.hospital_locator import pharmacy_locator

from backend.agent.tools.hospital_locator import pharmacy_locator

__all__ = ["pharmacy_locator"]
