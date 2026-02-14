"""
FortiEscrow Framework
=====================

A security-first, reusable escrow framework for the Tezos blockchain.

Architecture:
    contracts/
    ├── core/           # Main escrow contracts & invariants
    │   ├── escrow_base.py              # Base class & SimpleEscrow
    │   ├── escrow_multisig.py          # 2-of-3 MultiSig variant
    │   ├── escrow_factory.py           # Factory for deployment
    │   ├── invariants.py               # Formal invariant definitions
    │   └── invariants_enforcement.py   # Runtime invariant checking
    ├── interfaces/     # Types, errors, events
    │   ├── types.py
    │   ├── errors.py
    │   └── events.py
    ├── adapters/       # Integration adapters
    │   └── escrow_adapter.py
    └── utils/          # Validation & helpers
        ├── validators.py
        ├── amount_validator.py
        └── timeline_manager.py

Quick Start:
    from contracts.core import SimpleEscrow, MultiSigEscrow, EscrowFactory

    # Create a simple escrow
    escrow = SimpleEscrow(
        depositor=sp.address("tz1..."),
        beneficiary=sp.address("tz1..."),
        amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(86400)
    )

Security Features:
    - Explicit finite state machine (INIT → FUNDED → RELEASED/REFUNDED)
    - No admin privileges or super-user
    - Anti-fund-locking: permissionless recovery after timeout
    - Input validation on all parameters
    - Reentrancy protection via state-before-transfer pattern

Version: 2.0.0
License: MIT
"""

from contracts.core import (
    # State constants
    STATE_INIT,
    STATE_FUNDED,
    STATE_RELEASED,
    STATE_REFUNDED,
    MIN_TIMEOUT_SECONDS,
    MAX_TIMEOUT_SECONDS,

    # Error codes
    EscrowError,

    # Contracts
    SimpleEscrow,
    MultiSigEscrow,
    EscrowFactory,
)

from contracts.interfaces.events import (
    EscrowEvents,
    EventTag,
    EventLogger,
)

__version__ = "2.0.0"
__author__ = "FortiEscrow Labs"

__all__ = [
    # Version
    "__version__",

    # State constants
    "STATE_INIT",
    "STATE_FUNDED",
    "STATE_RELEASED",
    "STATE_REFUNDED",
    "MIN_TIMEOUT_SECONDS",
    "MAX_TIMEOUT_SECONDS",

    # Error codes
    "EscrowError",

    # Main contracts
    "SimpleEscrow",
    "MultiSigEscrow",
    "EscrowFactory",

    # Events
    "EscrowEvents",
    "EventTag",
    "EventLogger",
]
