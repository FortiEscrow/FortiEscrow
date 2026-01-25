"""
FortiEscrow Factory Contract
============================

Factory pattern for deploying and managing multiple escrow instances.

Features:
    - Deploy new escrow contracts
    - Track all deployed escrows
    - Query escrows by party (depositor/beneficiary)
    - Escrow registry for discovery

Security:
    - No admin privileges
    - Factory cannot control deployed escrows
    - Each escrow is independent once deployed
    - Registry is append-only (no deletions)
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
    MAX_TIMEOUT_SECONDS
)


# ==============================================================================
# TYPE DEFINITIONS
# ==============================================================================

# Parameters for creating a new escrow
CreateEscrowParams = sp.TRecord(
    beneficiary=sp.TAddress,
    amount=sp.TNat,
    timeout_seconds=sp.TNat
).layout(("beneficiary", ("amount", "timeout_seconds")))

# Escrow registry entry
EscrowEntry = sp.TRecord(
    escrow_address=sp.TAddress,
    depositor=sp.TAddress,
    beneficiary=sp.TAddress,
    amount=sp.TNat,
    created_at=sp.TTimestamp,
    escrow_id=sp.TNat
)

# Query result for escrow lookup
EscrowQueryResult = sp.TRecord(
    found=sp.TBool,
    escrow=sp.TOption(EscrowEntry)
)


# ==============================================================================
# FACTORY CONTRACT
# ==============================================================================

class EscrowFactory(sp.Contract):
    """
    Factory for deploying FortiEscrow contracts.

    This contract:
        1. Deploys new SimpleEscrow instances
        2. Maintains a registry of all escrows
        3. Provides query functions for discovery
        4. Has NO control over deployed escrows

    Why Use a Factory:
        - Standardized deployment
        - Central registry for discovery
        - Easier integration with dApps
        - Gas-efficient batch queries
    """

    def __init__(self):
        """Initialize the factory with empty registry"""

        self.init(
            # Counter for escrow IDs (auto-increment)
            next_escrow_id=sp.nat(0),

            # Registry: escrow_id -> EscrowEntry
            escrows=sp.big_map(
                tkey=sp.TNat,
                tvalue=EscrowEntry
            ),

            # Index: depositor -> list of escrow_ids
            escrows_by_depositor=sp.big_map(
                tkey=sp.TAddress,
                tvalue=sp.TList(sp.TNat)
            ),

            # Index: beneficiary -> list of escrow_ids
            escrows_by_beneficiary=sp.big_map(
                tkey=sp.TAddress,
                tvalue=sp.TList(sp.TNat)
            ),

            # Total escrows created (for stats)
            total_escrows=sp.nat(0),

            # Total value escrowed (cumulative, for stats)
            total_value_escrowed=sp.nat(0)
        )

    # ==========================================================================
    # ENTRY POINT: create_escrow()
    # ==========================================================================

    @sp.entry_point
    def create_escrow(self, params):
        """
        Deploy a new SimpleEscrow contract.

        The caller becomes the depositor.
        Funds are NOT transferred here - caller must fund the escrow separately.

        Args:
            params.beneficiary: Address to receive funds on release
            params.amount: Escrow amount in mutez
            params.timeout_seconds: Timeout for force-refund

        Security Checks:
            - Beneficiary != sender (no self-escrow)
            - Amount > 0
            - Timeout within allowed range

        Effects:
            - New escrow contract deployed
            - Entry added to registry
            - Indexes updated
        """

        sp.set_type(params, CreateEscrowParams)

        # ===== VALIDATION =====

        # Sender is the depositor
        depositor = sp.sender

        # Cannot escrow to self
        sp.verify(
            depositor != params.beneficiary,
            EscrowError.SAME_PARTY
        )

        # Amount must be positive
        sp.verify(
            params.amount > sp.nat(0),
            EscrowError.ZERO_AMOUNT
        )

        # Timeout validation
        sp.verify(
            params.timeout_seconds >= sp.nat(MIN_TIMEOUT_SECONDS),
            EscrowError.TIMEOUT_TOO_SHORT
        )
        sp.verify(
            params.timeout_seconds <= sp.nat(MAX_TIMEOUT_SECONDS),
            EscrowError.TIMEOUT_TOO_LONG
        )

        # ===== DEPLOY ESCROW =====

        # Create new escrow contract
        escrow_contract = sp.create_contract(
            contract=SimpleEscrow(
                depositor=depositor,
                beneficiary=params.beneficiary,
                amount=params.amount,
                timeout_seconds=params.timeout_seconds
            ),
            amount=sp.tez(0)  # No initial funding from factory
        )

        # ===== REGISTRY UPDATE =====

        escrow_id = self.data.next_escrow_id

        # Create registry entry
        entry = sp.record(
            escrow_address=escrow_contract,
            depositor=depositor,
            beneficiary=params.beneficiary,
            amount=params.amount,
            created_at=sp.now,
            escrow_id=escrow_id
        )

        # Add to main registry
        self.data.escrows[escrow_id] = entry

        # Update depositor index
        with sp.if_(self.data.escrows_by_depositor.contains(depositor)):
            # Append to existing list
            current_list = self.data.escrows_by_depositor[depositor]
            self.data.escrows_by_depositor[depositor] = sp.cons(escrow_id, current_list)
        with sp.else_():
            # Create new list
            self.data.escrows_by_depositor[depositor] = [escrow_id]

        # Update beneficiary index
        with sp.if_(self.data.escrows_by_beneficiary.contains(params.beneficiary)):
            current_list = self.data.escrows_by_beneficiary[params.beneficiary]
            self.data.escrows_by_beneficiary[params.beneficiary] = sp.cons(escrow_id, current_list)
        with sp.else_():
            self.data.escrows_by_beneficiary[params.beneficiary] = [escrow_id]

        # Update counters
        self.data.next_escrow_id = escrow_id + 1
        self.data.total_escrows = self.data.total_escrows + 1
        self.data.total_value_escrowed = self.data.total_value_escrowed + params.amount

    # ==========================================================================
    # VIEW: get_escrow()
    # ==========================================================================

    @sp.onchain_view()
    def get_escrow(self, escrow_id):
        """
        Get escrow details by ID.

        Args:
            escrow_id: The escrow ID to look up

        Returns:
            EscrowQueryResult with found=True and entry if exists,
            or found=False if not found
        """
        sp.set_type(escrow_id, sp.TNat)

        with sp.if_(self.data.escrows.contains(escrow_id)):
            sp.result(
                sp.record(
                    found=True,
                    escrow=sp.some(self.data.escrows[escrow_id])
                )
            )
        with sp.else_():
            sp.result(
                sp.record(
                    found=False,
                    escrow=sp.none
                )
            )

    # ==========================================================================
    # VIEW: get_escrows_by_depositor()
    # ==========================================================================

    @sp.onchain_view()
    def get_escrows_by_depositor(self, depositor):
        """
        Get all escrow IDs for a depositor.

        Args:
            depositor: Address to look up

        Returns:
            List of escrow IDs (may be empty)
        """
        sp.set_type(depositor, sp.TAddress)

        with sp.if_(self.data.escrows_by_depositor.contains(depositor)):
            sp.result(self.data.escrows_by_depositor[depositor])
        with sp.else_():
            sp.result(sp.list([], t=sp.TNat))

    # ==========================================================================
    # VIEW: get_escrows_by_beneficiary()
    # ==========================================================================

    @sp.onchain_view()
    def get_escrows_by_beneficiary(self, beneficiary):
        """
        Get all escrow IDs for a beneficiary.

        Args:
            beneficiary: Address to look up

        Returns:
            List of escrow IDs (may be empty)
        """
        sp.set_type(beneficiary, sp.TAddress)

        with sp.if_(self.data.escrows_by_beneficiary.contains(beneficiary)):
            sp.result(self.data.escrows_by_beneficiary[beneficiary])
        with sp.else_():
            sp.result(sp.list([], t=sp.TNat))

    # ==========================================================================
    # VIEW: get_stats()
    # ==========================================================================

    @sp.onchain_view()
    def get_stats(self):
        """
        Get factory statistics.

        Returns:
            - total_escrows: Number of escrows created
            - total_value_escrowed: Cumulative value (in mutez)
            - next_escrow_id: Next ID to be assigned
        """
        sp.result(
            sp.record(
                total_escrows=self.data.total_escrows,
                total_value_escrowed=self.data.total_value_escrowed,
                next_escrow_id=self.data.next_escrow_id
            )
        )

    # ==========================================================================
    # VIEW: get_escrow_address()
    # ==========================================================================

    @sp.onchain_view()
    def get_escrow_address(self, escrow_id):
        """
        Get just the contract address for an escrow ID.

        Useful for direct contract interaction.

        Args:
            escrow_id: The escrow ID

        Returns:
            Option[address] - Some(address) if found, None otherwise
        """
        sp.set_type(escrow_id, sp.TNat)

        with sp.if_(self.data.escrows.contains(escrow_id)):
            sp.result(sp.some(self.data.escrows[escrow_id].escrow_address))
        with sp.else_():
            sp.result(sp.none)


# ==============================================================================
# COMPILATION TARGET
# ==============================================================================

@sp.add_compilation_target("EscrowFactory")
def compile_escrow_factory():
    """Compile EscrowFactory for deployment"""
    return EscrowFactory()
