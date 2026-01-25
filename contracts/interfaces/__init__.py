"""
FortiEscrow Interfaces
======================

Shared type definitions, error codes, and event system.

Modules:
    - types: Type definitions for escrow data structures
    - errors: Centralized error codes
    - events: Event emission system for indexers

Usage:
    from contracts.interfaces.events import EscrowEvents, EventTag
    from contracts.interfaces.errors import FortiEscrowError
"""

from contracts.interfaces import types, errors, events

__all__ = [
    "types",
    "errors",
    "events",
]
