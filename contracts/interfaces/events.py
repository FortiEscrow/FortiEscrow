"""
FortiEscrow Event Definitions

Emitted events for escrow state changes.
"""

import smartpy as sp


class EscrowEvent:
    """Base class for escrow events"""
    pass


class FundedEvent(EscrowEvent):
    """Emitted when escrow is funded"""
    pass


class ReleasedEvent(EscrowEvent):
    """Emitted when funds are released"""
    pass


class RefundedEvent(EscrowEvent):
    """Emitted when funds are refunded"""
    pass


class ForcedRefundEvent(EscrowEvent):
    """Emitted when timeout-driven recovery occurs"""
    pass
