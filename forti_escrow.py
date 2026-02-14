"""
FortiEscrow: Security-First Escrow Framework for Tezos
======================================================

A reusable, auditable escrow framework implementing explicit finite state machine:
    INIT → FUNDED → (RELEASED | REFUNDED)

Quick Start
-----------

1. Simple 2-Party Escrow:

    from forti_escrow import SimpleEscrow

    escrow = SimpleEscrow(
        depositor=sp.address("tz1Alice"),
        beneficiary=sp.address("tz1Bob"),
        amount=sp.nat(1_000_000),       # 1 XTZ
        timeout_seconds=sp.nat(86400)    # 24 hours
    )

2. Multi-Signature Escrow (2-of-3):

    from forti_escrow import MultiSigEscrow

    escrow = MultiSigEscrow(
        depositor=sp.address("tz1Alice"),
        beneficiary=sp.address("tz1Bob"),
        arbiter=sp.address("tz1Carol"),
        amount=sp.nat(10_000_000),
        timeout_seconds=sp.nat(604800)   # 7 days
    )

3. Factory Deployment:

    from forti_escrow import EscrowFactory

    factory = EscrowFactory()
    # Deploy via: factory.create_escrow(params)

Security Design Principles
--------------------------
1. No super-admin or unilateral fund control
2. Anti fund-locking: timeout + permissionless recovery
3. All state transitions explicit and validated
4. Security invariants enforced at all points
5. Threat-model driven, not convenience-driven

State Machine
-------------
    - INIT (0): Contract initialized, awaiting funding
    - FUNDED (1): Funds received, awaiting release or refund
    - RELEASED (2): Escrow completed, funds to beneficiary [terminal]
    - REFUNDED (3): Escrow canceled, funds to depositor [terminal]

Critical Invariants
-------------------
    - Only FUNDED state can transition to RELEASED or REFUNDED
    - Balance must match escrow_amount when FUNDED
    - State transitions are atomic and cannot be reversed
    - No funds are locked indefinitely (timeout recovery)

For more details, see:
    - contracts/core/escrow_base.py       - Base implementation
    - contracts/core/escrow_multisig.py   - MultiSig variant
    - contracts/core/escrow_factory.py    - Factory pattern
    - tests/                              - Test suite
"""

import smartpy as sp

# Re-export from contracts package
from contracts.core.escrow_base import (
    # State constants
    STATE_INIT,
    STATE_FUNDED,
    STATE_RELEASED,
    STATE_REFUNDED,
    STATE_NAMES,
    MIN_TIMEOUT_SECONDS,
    MAX_TIMEOUT_SECONDS,

    # Error codes
    EscrowError,

    # Type definitions
    EscrowConfig,
    EscrowStatus,

    # Contracts
    EscrowBase,
    SimpleEscrow,
)

from contracts.core.escrow_multisig import (
    MultiSigEscrow,
    DISPUTE_NONE,
    DISPUTE_PENDING,
    DISPUTE_RESOLVED,
    VOTE_RELEASE,
    VOTE_REFUND,
)

from contracts.core.escrow_factory import (
    EscrowFactory,
    CreateEscrowParams,
    EscrowEntry,
)

from contracts.interfaces.events import (
    EscrowEvents,
    EventTag,
    EventLogger,
)

from contracts.utils.validators import (
    Validators,
    ValidationError,
    ValidationConstants,
    validate_escrow_params,
    validate_multisig_params,
)

# Package metadata
__version__ = "2.0.0"
__author__ = "FortiEscrow Labs"
__license__ = "MIT"

# Public API
__all__ = [
    # Metadata
    "__version__",
    "__author__",
    "__license__",

    # State constants
    "STATE_INIT",
    "STATE_FUNDED",
    "STATE_RELEASED",
    "STATE_REFUNDED",
    "STATE_NAMES",
    "MIN_TIMEOUT_SECONDS",
    "MAX_TIMEOUT_SECONDS",

    # MultiSig constants
    "DISPUTE_NONE",
    "DISPUTE_PENDING",
    "DISPUTE_RESOLVED",
    "VOTE_RELEASE",
    "VOTE_REFUND",

    # Error codes
    "EscrowError",
    "ValidationError",

    # Type definitions
    "EscrowConfig",
    "EscrowStatus",
    "CreateEscrowParams",
    "EscrowEntry",

    # Main contracts
    "EscrowBase",
    "SimpleEscrow",
    "MultiSigEscrow",
    "EscrowFactory",

    # Events
    "EscrowEvents",
    "EventTag",
    "EventLogger",

    # Utilities
    "Validators",
    "ValidationConstants",
    "validate_escrow_params",
    "validate_multisig_params",
]


# ==============================================================================
# COMPILATION TARGETS
# ==============================================================================

if __name__ == "__main__":
    """
    Example deployment configurations for testing/demonstration.
    Run with: python -m smartpy compile forti_escrow.py
    """

    # Example 1: Simple Escrow
    @sp.add_compilation_target("SimpleEscrow_Example")
    def simple_escrow_example():
        return SimpleEscrow(
            depositor=sp.address("tz1Depositor"),
            beneficiary=sp.address("tz1Beneficiary"),
            amount=sp.nat(1_000_000),
            timeout_seconds=sp.nat(7 * 24 * 3600)  # 1 week
        )

    # Example 2: MultiSig Escrow
    @sp.add_compilation_target("MultiSigEscrow_Example")
    def multisig_escrow_example():
        return MultiSigEscrow(
            depositor=sp.address("tz1Depositor"),
            beneficiary=sp.address("tz1Beneficiary"),
            arbiter=sp.address("tz1Arbiter"),
            amount=sp.nat(10_000_000),
            timeout_seconds=sp.nat(30 * 24 * 3600)  # 30 days
        )

    # Example 3: Factory
    @sp.add_compilation_target("EscrowFactory_Example")
    def factory_example():
        return EscrowFactory()

    print("FortiEscrow Framework v" + __version__)
    print("Compilation targets generated.")
