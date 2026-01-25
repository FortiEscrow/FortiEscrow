"""
FortiEscrow Core Contracts
==========================

Main escrow contract implementations.

Contracts:
    - EscrowBase: Abstract base class with state machine
    - SimpleEscrow: Basic 2-party escrow
    - MultiSigEscrow: 2-of-3 multi-signature escrow
    - EscrowFactory: Factory for deploying escrow instances

Usage:
    from contracts.core import SimpleEscrow, MultiSigEscrow, EscrowFactory
"""

from contracts.core.escrow_base import (
    # Constants
    STATE_INIT,
    STATE_FUNDED,
    STATE_RELEASED,
    STATE_REFUNDED,
    MIN_TIMEOUT_SECONDS,
    MAX_TIMEOUT_SECONDS,

    # Error codes
    EscrowError,

    # Contracts
    EscrowBase,
    SimpleEscrow,
)

from contracts.core.escrow_multisig import (
    MultiSigEscrow,
    DISPUTE_NONE,
    DISPUTE_PENDING,
    VOTE_RELEASE,
    VOTE_REFUND,
)

from contracts.core.escrow_factory import (
    EscrowFactory,
)

__version__ = "2.0.0"

__all__ = [
    # Constants
    "STATE_INIT",
    "STATE_FUNDED",
    "STATE_RELEASED",
    "STATE_REFUNDED",
    "MIN_TIMEOUT_SECONDS",
    "MAX_TIMEOUT_SECONDS",

    # MultiSig constants
    "DISPUTE_NONE",
    "DISPUTE_PENDING",
    "VOTE_RELEASE",
    "VOTE_REFUND",

    # Error codes
    "EscrowError",

    # Contracts
    "EscrowBase",
    "SimpleEscrow",
    "MultiSigEscrow",
    "EscrowFactory",
]
