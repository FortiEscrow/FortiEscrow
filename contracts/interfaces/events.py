"""
FortiEscrow Event System
========================

Structured event emission for escrow state changes.

Tezos Event Model:
    - Events are emitted via contract operations
    - Off-chain indexers (TzKT, TZKT) capture events
    - Events enable real-time dApp updates
    - Event logs are immutable and auditable

Event Categories:
    1. Lifecycle Events: Fund, Release, Refund
    2. Voting Events: VoteCast, VoteChanged (for MultiSig)
    3. Dispute Events: DisputeRaised, DisputeResolved
    4. Admin Events: FactoryDeploy, ParameterUpdate

Usage:
    from contracts.interfaces.events import EscrowEvents

    # In contract entry point
    EscrowEvents.emit_funded(escrow_id, depositor, amount)
"""

import smartpy as sp


# ==============================================================================
# EVENT TYPE DEFINITIONS
# ==============================================================================

# Lifecycle event payloads
FundedEventPayload = sp.TRecord(
    escrow_id=sp.TOption(sp.TNat),    # None for standalone contracts
    depositor=sp.TAddress,
    amount=sp.TNat,
    deadline=sp.TTimestamp,
    timestamp=sp.TTimestamp
)

ReleasedEventPayload = sp.TRecord(
    escrow_id=sp.TOption(sp.TNat),
    beneficiary=sp.TAddress,
    amount=sp.TNat,
    timestamp=sp.TTimestamp
)

RefundedEventPayload = sp.TRecord(
    escrow_id=sp.TOption(sp.TNat),
    depositor=sp.TAddress,
    amount=sp.TNat,
    reason=sp.TString,                 # "voluntary", "timeout", "dispute"
    timestamp=sp.TTimestamp
)

# Voting event payloads (for MultiSig)
VoteCastPayload = sp.TRecord(
    escrow_id=sp.TOption(sp.TNat),
    voter=sp.TAddress,
    vote_type=sp.TString,              # "release" or "refund"
    release_votes=sp.TNat,
    refund_votes=sp.TNat,
    timestamp=sp.TTimestamp
)

# Dispute event payloads
DisputeRaisedPayload = sp.TRecord(
    escrow_id=sp.TOption(sp.TNat),
    raised_by=sp.TAddress,
    reason=sp.TString,
    timestamp=sp.TTimestamp
)

DisputeResolvedPayload = sp.TRecord(
    escrow_id=sp.TOption(sp.TNat),
    resolved_by=sp.TAddress,
    outcome=sp.TString,                # "released", "refunded"
    timestamp=sp.TTimestamp
)

# Factory event payloads
EscrowCreatedPayload = sp.TRecord(
    escrow_id=sp.TNat,
    escrow_address=sp.TAddress,
    depositor=sp.TAddress,
    beneficiary=sp.TAddress,
    amount=sp.TNat,
    timeout_seconds=sp.TNat,
    timestamp=sp.TTimestamp
)


# ==============================================================================
# EVENT TAGS (for indexer filtering)
# ==============================================================================

class EventTag:
    """Event type identifiers for indexer filtering"""

    # Lifecycle events
    FUNDED = "escrow_funded"
    RELEASED = "escrow_released"
    REFUNDED = "escrow_refunded"
    FORCE_REFUNDED = "escrow_force_refunded"

    # Voting events
    VOTE_CAST = "vote_cast"
    VOTE_CHANGED = "vote_changed"
    CONSENSUS_REACHED = "consensus_reached"

    # Dispute events
    DISPUTE_RAISED = "dispute_raised"
    DISPUTE_RESOLVED = "dispute_resolved"

    # Factory events
    ESCROW_CREATED = "escrow_created"


# ==============================================================================
# EVENT EMITTER CLASS
# ==============================================================================

class EscrowEvents:
    """
    Static methods for emitting escrow events.

    Events are stored in contract storage as a log list,
    which indexers can query and process.

    For gas efficiency, events can also be emitted via
    internal transactions to a dedicated event logger contract.
    """

    # ==========================================================================
    # LIFECYCLE EVENTS
    # ==========================================================================

    @staticmethod
    def emit_funded(storage, escrow_id, depositor, amount, deadline):
        """
        Emit event when escrow is funded.

        Args:
            storage: Contract storage (must have 'events' list)
            escrow_id: Escrow ID (None for standalone)
            depositor: Depositor address
            amount: Funded amount
            deadline: Calculated deadline
        """
        event = sp.record(
            event_type=EventTag.FUNDED,
            payload=sp.record(
                escrow_id=escrow_id,
                depositor=depositor,
                amount=amount,
                deadline=deadline,
                timestamp=sp.now
            )
        )
        # Note: Actual emission depends on contract architecture
        # This is a reference implementation

    @staticmethod
    def emit_released(storage, escrow_id, beneficiary, amount):
        """
        Emit event when funds are released.

        Args:
            storage: Contract storage
            escrow_id: Escrow ID
            beneficiary: Recipient address
            amount: Released amount
        """
        event = sp.record(
            event_type=EventTag.RELEASED,
            payload=sp.record(
                escrow_id=escrow_id,
                beneficiary=beneficiary,
                amount=amount,
                timestamp=sp.now
            )
        )

    @staticmethod
    def emit_refunded(storage, escrow_id, depositor, amount, reason):
        """
        Emit event when funds are refunded.

        Args:
            storage: Contract storage
            escrow_id: Escrow ID
            depositor: Refund recipient
            amount: Refunded amount
            reason: Refund reason (voluntary/timeout/dispute)
        """
        event = sp.record(
            event_type=EventTag.REFUNDED,
            payload=sp.record(
                escrow_id=escrow_id,
                depositor=depositor,
                amount=amount,
                reason=reason,
                timestamp=sp.now
            )
        )

    # ==========================================================================
    # VOTING EVENTS
    # ==========================================================================

    @staticmethod
    def emit_vote_cast(storage, escrow_id, voter, vote_type, release_votes, refund_votes):
        """
        Emit event when a vote is cast in MultiSig escrow.

        Args:
            storage: Contract storage
            escrow_id: Escrow ID
            voter: Address casting the vote
            vote_type: "release" or "refund"
            release_votes: Current release vote count
            refund_votes: Current refund vote count
        """
        event = sp.record(
            event_type=EventTag.VOTE_CAST,
            payload=sp.record(
                escrow_id=escrow_id,
                voter=voter,
                vote_type=vote_type,
                release_votes=release_votes,
                refund_votes=refund_votes,
                timestamp=sp.now
            )
        )

    @staticmethod
    def emit_consensus_reached(storage, escrow_id, outcome, release_votes, refund_votes):
        """
        Emit event when voting consensus is reached.

        Args:
            storage: Contract storage
            escrow_id: Escrow ID
            outcome: "release" or "refund"
            release_votes: Final release vote count
            refund_votes: Final refund vote count
        """
        event = sp.record(
            event_type=EventTag.CONSENSUS_REACHED,
            payload=sp.record(
                escrow_id=escrow_id,
                outcome=outcome,
                release_votes=release_votes,
                refund_votes=refund_votes,
                timestamp=sp.now
            )
        )

    # ==========================================================================
    # DISPUTE EVENTS
    # ==========================================================================

    @staticmethod
    def emit_dispute_raised(storage, escrow_id, raised_by, reason):
        """
        Emit event when a dispute is raised.

        Args:
            storage: Contract storage
            escrow_id: Escrow ID
            raised_by: Address raising the dispute
            reason: Dispute description
        """
        event = sp.record(
            event_type=EventTag.DISPUTE_RAISED,
            payload=sp.record(
                escrow_id=escrow_id,
                raised_by=raised_by,
                reason=reason,
                timestamp=sp.now
            )
        )

    @staticmethod
    def emit_dispute_resolved(storage, escrow_id, resolved_by, outcome):
        """
        Emit event when a dispute is resolved.

        Args:
            storage: Contract storage
            escrow_id: Escrow ID
            resolved_by: Address resolving the dispute
            outcome: Resolution outcome
        """
        event = sp.record(
            event_type=EventTag.DISPUTE_RESOLVED,
            payload=sp.record(
                escrow_id=escrow_id,
                resolved_by=resolved_by,
                outcome=outcome,
                timestamp=sp.now
            )
        )

    # ==========================================================================
    # FACTORY EVENTS
    # ==========================================================================

    @staticmethod
    def emit_escrow_created(storage, escrow_id, escrow_address, depositor,
                            beneficiary, amount, timeout_seconds):
        """
        Emit event when factory creates a new escrow.

        Args:
            storage: Factory storage
            escrow_id: Assigned escrow ID
            escrow_address: Deployed contract address
            depositor: Depositor address
            beneficiary: Beneficiary address
            amount: Escrow amount
            timeout_seconds: Timeout duration
        """
        event = sp.record(
            event_type=EventTag.ESCROW_CREATED,
            payload=sp.record(
                escrow_id=escrow_id,
                escrow_address=escrow_address,
                depositor=depositor,
                beneficiary=beneficiary,
                amount=amount,
                timeout_seconds=timeout_seconds,
                timestamp=sp.now
            )
        )


# ==============================================================================
# EVENT LOGGER CONTRACT (Optional Dedicated Logger)
# ==============================================================================

class EventLogger(sp.Contract):
    """
    Dedicated event logging contract.

    Benefits:
        - Centralized event storage
        - Reduced gas in main contracts
        - Easier indexer integration
        - Event history preservation

    The main escrow contracts can optionally call this logger
    to emit events, keeping their own storage minimal.
    """

    def __init__(self, authorized_emitters):
        """
        Initialize event logger.

        Args:
            authorized_emitters: List of contract addresses allowed to emit
        """
        self.init(
            # Authorized emitters (factories, escrow contracts)
            authorized_emitters=sp.set(authorized_emitters, t=sp.TAddress),

            # Event log (append-only)
            event_count=sp.nat(0),

            # Recent events (circular buffer for quick access)
            recent_events=sp.list([], t=sp.TRecord(
                id=sp.TNat,
                event_type=sp.TString,
                source=sp.TAddress,
                timestamp=sp.TTimestamp,
                data=sp.TBytes
            ))
        )

    @sp.entry_point
    def log_event(self, params):
        """
        Log an event from authorized emitter.

        Args:
            params.event_type: Event type tag
            params.data: Packed event payload
        """
        # Auth check
        sp.verify(
            self.data.authorized_emitters.contains(sp.sender),
            "UNAUTHORIZED_EMITTER"
        )

        # Create event record
        event = sp.record(
            id=self.data.event_count,
            event_type=params.event_type,
            source=sp.sender,
            timestamp=sp.now,
            data=params.data
        )

        # Add to recent events (keep last 100)
        self.data.recent_events = sp.cons(
            event,
            sp.slice(self.data.recent_events, 0, 99).open_some([])
        )

        # Increment counter
        self.data.event_count = self.data.event_count + 1

    @sp.entry_point
    def add_emitter(self, emitter):
        """Add authorized emitter (admin only in production)"""
        sp.set_type(emitter, sp.TAddress)
        self.data.authorized_emitters.add(emitter)

    @sp.onchain_view()
    def get_event_count(self):
        """Return total event count"""
        sp.result(self.data.event_count)

    @sp.onchain_view()
    def get_recent_events(self, count):
        """Return N most recent events"""
        sp.set_type(count, sp.TNat)
        sp.result(sp.slice(self.data.recent_events, 0, count))
