"""
FortiEscrow Adapters
====================

Lightweight adapter interfaces for dApp integration.

Adapters provide:
    - Simplified API
    - Batch operations
    - Convenience queries
    - Event aggregation

Security Guarantee:
    Adapters are PASS-THROUGH only.
    They cannot bypass escrow authorization.
    They never hold funds.
"""

from contracts.adapters.escrow_adapter import (
    EscrowAdapter,
    CreateEscrowRequest,
)

__all__ = [
    "EscrowAdapter",
    "CreateEscrowRequest",
]
