"""
FortiEscrow Adapter Interface (SAFE VERSION)
=============================================

Factory and registry adapter for FortiEscrow contracts.

IMPORTANT SECURITY NOTE:
    This adapter is a FACTORY + REGISTRY only.
    It does NOT provide pass-through operations for fund/release/refund.

    Why? Because Tezos inter-contract calls change sp.sender to the calling
    contract. If adapter called escrow.release(), sp.sender would be the
    adapter address, NOT the original user - breaking authorization.

Design Principles:
    1. FACTORY ONLY: Creates escrows, does not operate them
    2. NO PASS-THROUGH: Users must call escrow contracts directly
    3. NO FUND CUSTODY: Adapter never holds funds
    4. REGISTRY: Tracks created escrows for discovery
    5. VIEWS ONLY: Read-only queries for convenience

Architecture:
    ┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
    │   dApp UI   │────►│  EscrowAdapter  │────►│ SimpleEscrow │
    └─────────────┘     └─────────────────┘     └──────────────┘
           │                    │                      │
           │              (factory only)         (all operations)
           │              Creates escrows        fund/release/refund
           │                    │                      │
           └──────────────────────────────────────────►│
                    Direct calls for operations

Usage:
    # Step 1: Create escrow via adapter (factory)
    adapter.create_escrow({beneficiary, amount, timeout})
    # Returns escrow address

    # Step 2: Fund escrow DIRECTLY (not via adapter!)
    escrow.fund()  # Call escrow contract directly

    # Step 3: Release/refund DIRECTLY
    escrow.release()  # Call escrow contract directly
"""

import smartpy as sp

from contracts.core.escrow_base import (
    SimpleEscrow,
    EscrowError,
    STATE_INIT,
    STATE_FUNDED,
    STATE_RELEASED,
    STATE_REFUNDED,
    MIN_TIMEOUT_SECONDS,
    MAX_TIMEOUT_SECONDS,
)


# ==============================================================================
# ERROR CODES
# ==============================================================================

class AdapterError:
    """Adapter-specific error codes"""
    DISABLED_USE_DIRECT_CALL = "ADAPTER_DISABLED_USE_DIRECT_CALL"
    ESCROW_NOT_FOUND = "ADAPTER_ESCROW_NOT_FOUND"


# ==============================================================================
# TYPE DEFINITIONS
# ==============================================================================

# Request to create new escrow
CreateEscrowRequest = sp.TRecord(
    beneficiary=sp.TAddress,
    amount=sp.TNat,
    timeout_seconds=sp.TNat
).layout(("beneficiary", ("amount", "timeout_seconds")))


# ==============================================================================
# ESCROW ADAPTER CONTRACT
# ==============================================================================

class EscrowAdapter(sp.Contract):
    """
    Factory and registry adapter for FortiEscrow.

    This contract provides:
        1. Escrow factory (create new escrows)
        2. Escrow registry (track created escrows)
        3. Index queries (find escrows by party)

    REMOVED (Security Risk):
        - fund_escrow: Would break authorization (sp.sender = adapter)
        - release_escrow: Would break authorization
        - refund_escrow: Would break authorization
        - force_refund_escrow: Would work but misleading API
        - create_and_fund: Would lock funds (state=INIT with balance>0)

    Users MUST call escrow contracts directly for operations.
    """

    def __init__(self):
        """Initialize adapter with empty registry."""
        self.init(
            # Registry of created escrows (for batch queries)
            escrow_count=sp.nat(0),
            escrows=sp.big_map(
                tkey=sp.TNat,
                tvalue=sp.TAddress
            ),

            # Index by depositor (for "my escrows" queries)
            by_depositor=sp.big_map(
                tkey=sp.TAddress,
                tvalue=sp.TList(sp.TNat)
            ),

            # Index by beneficiary
            by_beneficiary=sp.big_map(
                tkey=sp.TAddress,
                tvalue=sp.TList(sp.TNat)
            )
        )

    # ==========================================================================
    # FACTORY: CREATE ESCROW (SAFE)
    # ==========================================================================

    @sp.entry_point
    def create_escrow(self, params):
        """
        Create a new escrow contract.

        The caller becomes the depositor.
        Escrow is created but NOT funded.

        IMPORTANT: After creation, caller must fund the escrow DIRECTLY
        by calling escrow.fund() on the escrow contract address.

        Args:
            params.beneficiary: Recipient address
            params.amount: Escrow amount in mutez
            params.timeout_seconds: Timeout duration

        Security:
            - Caller becomes depositor (sp.sender stored in escrow)
            - No funds transferred (amount=0)
            - Escrow is independent once created
            - Caller must fund escrow directly (not via adapter)
        """
        sp.set_type(params, CreateEscrowRequest)

        # Reject any attached funds (prevent accidental loss)
        sp.verify(sp.amount == sp.tez(0), EscrowError.AMOUNT_MISMATCH)

        depositor = sp.sender

        # Validate (same checks as escrow, but fail early for UX)
        sp.verify(depositor != params.beneficiary, EscrowError.SAME_PARTY)
        sp.verify(params.amount > sp.nat(0), EscrowError.ZERO_AMOUNT)
        sp.verify(
            params.timeout_seconds >= sp.nat(MIN_TIMEOUT_SECONDS),
            EscrowError.TIMEOUT_TOO_SHORT
        )
        sp.verify(
            params.timeout_seconds <= sp.nat(MAX_TIMEOUT_SECONDS),
            EscrowError.TIMEOUT_TOO_LONG
        )

        # Deploy escrow contract (NO funds attached)
        escrow_address = sp.create_contract(
            contract=SimpleEscrow(
                depositor=depositor,
                beneficiary=params.beneficiary,
                amount=params.amount,
                timeout_seconds=params.timeout_seconds
            ),
            amount=sp.tez(0)  # MUST be zero - user funds directly
        )

        # Register in adapter (for queries only)
        escrow_id = self.data.escrow_count

        self.data.escrows[escrow_id] = escrow_address
        self.data.escrow_count = escrow_id + 1

        # Index by depositor
        with sp.if_(self.data.by_depositor.contains(depositor)):
            current = self.data.by_depositor[depositor]
            self.data.by_depositor[depositor] = sp.cons(escrow_id, current)
        with sp.else_():
            self.data.by_depositor[depositor] = [escrow_id]

        # Index by beneficiary
        with sp.if_(self.data.by_beneficiary.contains(params.beneficiary)):
            current = self.data.by_beneficiary[params.beneficiary]
            self.data.by_beneficiary[params.beneficiary] = sp.cons(escrow_id, current)
        with sp.else_():
            self.data.by_beneficiary[params.beneficiary] = [escrow_id]

    # ==========================================================================
    # DISABLED OPERATIONS (Explicitly fail with helpful message)
    # ==========================================================================

    @sp.entry_point
    def fund_escrow(self, escrow_address):
        """
        DISABLED: Fund escrow directly instead.

        This operation was removed because Tezos inter-contract calls
        change sp.sender to the adapter contract, breaking authorization.

        To fund an escrow:
            1. Get escrow address from get_escrow_address view
            2. Call escrow.fund() directly with exact amount
        """
        sp.set_type(escrow_address, sp.TAddress)
        sp.failwith(AdapterError.DISABLED_USE_DIRECT_CALL)

    @sp.entry_point
    def release_escrow(self, escrow_address):
        """
        DISABLED: Release escrow directly instead.

        To release an escrow:
            1. Call escrow.release() directly as depositor
        """
        sp.set_type(escrow_address, sp.TAddress)
        sp.failwith(AdapterError.DISABLED_USE_DIRECT_CALL)

    @sp.entry_point
    def refund_escrow(self, escrow_address):
        """
        DISABLED: Refund escrow directly instead.

        To refund an escrow:
            1. Call escrow.refund() directly as depositor
        """
        sp.set_type(escrow_address, sp.TAddress)
        sp.failwith(AdapterError.DISABLED_USE_DIRECT_CALL)

    @sp.entry_point
    def force_refund_escrow(self, escrow_address):
        """
        DISABLED: Force refund escrow directly instead.

        To force refund after timeout:
            1. Call escrow.force_refund() directly
        """
        sp.set_type(escrow_address, sp.TAddress)
        sp.failwith(AdapterError.DISABLED_USE_DIRECT_CALL)

    @sp.entry_point
    def create_and_fund(self, params):
        """
        DISABLED: This operation was removed due to fund-lock risk.

        Previously, this would send funds during contract creation,
        but the escrow would be in INIT state (not FUNDED), causing
        permanent fund lock with no recovery path.

        Safe alternative:
            1. Call create_escrow (no funds)
            2. Call escrow.fund() directly with exact amount
        """
        sp.set_type(params, CreateEscrowRequest)
        sp.failwith(AdapterError.DISABLED_USE_DIRECT_CALL)

    # ==========================================================================
    # VIEW: GET ESCROW ADDRESS
    # ==========================================================================

    @sp.onchain_view()
    def get_escrow_address(self, escrow_id):
        """
        Get escrow contract address by ID.

        Use this to get the address for direct contract calls.
        """
        sp.set_type(escrow_id, sp.TNat)

        with sp.if_(self.data.escrows.contains(escrow_id)):
            sp.result(sp.some(self.data.escrows[escrow_id]))
        with sp.else_():
            sp.result(sp.none)

    # ==========================================================================
    # VIEW: GET MY ESCROWS (AS DEPOSITOR)
    # ==========================================================================

    @sp.onchain_view()
    def get_my_escrows_as_depositor(self, depositor):
        """
        Get all escrow IDs where address is depositor.

        Useful for "My Escrows" UI section.
        """
        sp.set_type(depositor, sp.TAddress)

        with sp.if_(self.data.by_depositor.contains(depositor)):
            sp.result(self.data.by_depositor[depositor])
        with sp.else_():
            sp.result(sp.list([], t=sp.TNat))

    # ==========================================================================
    # VIEW: GET MY ESCROWS (AS BENEFICIARY)
    # ==========================================================================

    @sp.onchain_view()
    def get_my_escrows_as_beneficiary(self, beneficiary):
        """
        Get all escrow IDs where address is beneficiary.

        Useful for "Incoming Payments" UI section.
        """
        sp.set_type(beneficiary, sp.TAddress)

        with sp.if_(self.data.by_beneficiary.contains(beneficiary)):
            sp.result(self.data.by_beneficiary[beneficiary])
        with sp.else_():
            sp.result(sp.list([], t=sp.TNat))

    # ==========================================================================
    # VIEW: GET ADAPTER STATS
    # ==========================================================================

    @sp.onchain_view()
    def get_stats(self):
        """Get adapter statistics"""
        sp.result(
            sp.record(
                total_escrows=self.data.escrow_count
            )
        )


# ==============================================================================
# SECURITY DOCUMENTATION
# ==============================================================================

"""
SECURITY MODEL: Factory-Only Adapter
=====================================

This adapter follows the FACTORY-ONLY pattern:

1. CREATES escrows (factory function)
2. TRACKS escrows (registry)
3. QUERIES escrows (views)

It does NOT:
- Fund escrows (would break authorization)
- Release escrows (would break authorization)
- Refund escrows (would break authorization)
- Hold any funds (zero custody)

WHY NO PASS-THROUGH?
--------------------
In Tezos, when Contract A calls Contract B:
    sp.sender in B = A (the calling contract)
    sp.source in B = original transaction signer

FortiEscrow uses sp.sender for authorization:
    sp.verify(sp.sender == self.data.depositor, ...)

If adapter called escrow.release():
    sp.sender = adapter address ≠ depositor
    → ALWAYS FAILS

We could use sp.source, but that has security implications
(any contract in call chain could trigger release).

CORRECT USAGE PATTERN
---------------------
# 1. Create via adapter (factory)
adapter.create_escrow({beneficiary, amount, timeout})
# Returns escrow_id, lookup address via get_escrow_address

# 2. Fund DIRECTLY
escrow_contract.fund().with_amount(amount)

# 3. Release/Refund DIRECTLY
escrow_contract.release()  # or .refund() or .force_refund()

The adapter is purely for escrow creation and discovery.
All operations must be done directly on the escrow contract.
"""


# ==============================================================================
# COMPILATION TARGET
# ==============================================================================

@sp.add_compilation_target("EscrowAdapter")
def compile_adapter():
    return EscrowAdapter()
