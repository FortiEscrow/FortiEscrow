"""
FortiEscrow MultiSig Contract
=============================

Multi-signature escrow requiring consensus for fund release.

This variant adds:
    - Arbiter role (neutral third party)
    - 2-of-3 release requirement
    - Dispute resolution mechanism
    - Enhanced security for high-value escrows

Parties:
    - Depositor: Funds the escrow
    - Beneficiary: Receives funds on release
    - Arbiter: Neutral party for dispute resolution

Release Conditions:
    1. Depositor + Beneficiary agree (mutual consent)
    2. Depositor + Arbiter agree (arbiter sides with depositor)
    3. Beneficiary + Arbiter agree (arbiter sides with beneficiary)

Refund Conditions:
    1. Depositor requests + Arbiter approves
    2. Timeout expires (permissionless recovery)

Security:
    - No single party can unilaterally move funds
    - Arbiter cannot access funds alone
    - Timeout ensures no permanent lock
"""

import smartpy as sp

from contracts.core.escrow_base import (
    EscrowError,
    STATE_INIT,
    STATE_FUNDED,
    STATE_RELEASED,
    STATE_REFUNDED,
    MIN_TIMEOUT_SECONDS,
    MAX_TIMEOUT_SECONDS
)


# ==============================================================================
# CONSTANTS
# ==============================================================================

# Dispute states
DISPUTE_NONE = 0          # No dispute active
DISPUTE_PENDING = 1       # Dispute raised, awaiting arbiter
DISPUTE_RESOLVED = 2      # Dispute resolved

# Vote types
VOTE_RELEASE = 0
VOTE_REFUND = 1


# ==============================================================================
# TYPE DEFINITIONS
# ==============================================================================

# Vote record
VoteRecord = sp.TRecord(
    voter=sp.TAddress,
    vote_type=sp.TInt,      # VOTE_RELEASE or VOTE_REFUND
    timestamp=sp.TTimestamp
)


# ==============================================================================
# MULTISIG ESCROW CONTRACT
# ==============================================================================

class MultiSigEscrow(sp.Contract):
    """
    Multi-signature escrow requiring 2-of-3 approval for releases.

    State Machine:
        INIT ──► FUNDED ──► RELEASED (if 2+ vote release)
                    │
                    └──────► REFUNDED (if 2+ vote refund OR timeout)

    Voting Rules:
        - Each party can cast one vote
        - Votes are for either RELEASE or REFUND
        - 2 matching votes triggers the action
        - Votes can be changed until action is triggered
        - Timeout bypasses voting (emergency recovery)
    """

    def __init__(self, depositor, beneficiary, arbiter, amount, timeout_seconds):
        """
        Initialize multi-sig escrow.

        Args:
            depositor: Address funding the escrow
            beneficiary: Address receiving funds on release
            arbiter: Neutral third party for dispute resolution
            amount: Escrow amount in mutez
            timeout_seconds: Timeout for emergency recovery

        Security Validations:
            - All three addresses must be different
            - Amount > 0
            - Timeout within bounds
        """

        # ===== INPUT VALIDATION =====

        # All parties must be different
        sp.verify(
            (depositor != beneficiary) &
            (depositor != arbiter) &
            (beneficiary != arbiter),
            EscrowError.SAME_PARTY
        )

        # Amount must be positive
        sp.verify(amount > sp.nat(0), EscrowError.ZERO_AMOUNT)

        # Timeout bounds
        sp.verify(
            timeout_seconds >= sp.nat(MIN_TIMEOUT_SECONDS),
            EscrowError.TIMEOUT_TOO_SHORT
        )
        sp.verify(
            timeout_seconds <= sp.nat(MAX_TIMEOUT_SECONDS),
            EscrowError.TIMEOUT_TOO_LONG
        )

        # ===== STATE INITIALIZATION =====

        self.init(
            # Parties (immutable)
            depositor=depositor,
            beneficiary=beneficiary,
            arbiter=arbiter,

            # Escrow terms (immutable)
            escrow_amount=amount,
            timeout_seconds=timeout_seconds,

            # State machine
            state=STATE_INIT,

            # Timeline
            funded_at=sp.timestamp(0),
            deadline=sp.timestamp(0),

            # Voting state
            # Maps address -> vote_type (VOTE_RELEASE or VOTE_REFUND)
            votes=sp.map(
                tkey=sp.TAddress,
                tvalue=sp.TInt
            ),

            # Vote counts
            release_votes=sp.nat(0),
            refund_votes=sp.nat(0),

            # Dispute tracking
            dispute_state=DISPUTE_NONE,
            dispute_reason=sp.string("")
        )

    # ==========================================================================
    # INTERNAL HELPERS
    # ==========================================================================

    def _require_party(self):
        """Verify sender is one of the three parties"""
        sp.verify(
            (sp.sender == self.data.depositor) |
            (sp.sender == self.data.beneficiary) |
            (sp.sender == self.data.arbiter),
            EscrowError.UNAUTHORIZED
        )

    def _is_party(self, addr):
        """Check if address is a party"""
        return (addr == self.data.depositor) | \
               (addr == self.data.beneficiary) | \
               (addr == self.data.arbiter)

    def _is_timeout_expired(self):
        """Check if timeout has passed"""
        return sp.now > self.data.deadline

    def _calculate_deadline(self):
        """Calculate deadline from current time"""
        return sp.add_seconds(sp.now, sp.to_int(self.data.timeout_seconds))

    def _check_consensus(self):
        """Check if consensus reached and execute action"""

        # 2+ votes for release
        with sp.if_(self.data.release_votes >= sp.nat(2)):
            self._execute_release()

        # 2+ votes for refund
        with sp.if_(self.data.refund_votes >= sp.nat(2)):
            self._execute_refund()

    def _execute_release(self):
        """Execute release to beneficiary"""
        self.data.state = STATE_RELEASED
        sp.send(
            self.data.beneficiary,
            sp.utils.nat_to_mutez(self.data.escrow_amount)
        )

    def _execute_refund(self):
        """Execute refund to depositor"""
        self.data.state = STATE_REFUNDED
        sp.send(
            self.data.depositor,
            sp.utils.nat_to_mutez(self.data.escrow_amount)
        )

    # ==========================================================================
    # ENTRY POINT: fund()
    # ==========================================================================

    @sp.entry_point
    def fund(self):
        """
        INIT → FUNDED: Deposit escrow amount.

        Authorization: Only depositor
        """

        # State check
        sp.verify(self.data.state == STATE_INIT, EscrowError.ALREADY_FUNDED)

        # Auth check
        sp.verify(sp.sender == self.data.depositor, EscrowError.NOT_DEPOSITOR)

        # Amount check
        sp.verify(
            sp.amount == sp.utils.nat_to_mutez(self.data.escrow_amount),
            EscrowError.AMOUNT_MISMATCH
        )

        # State transition
        self.data.state = STATE_FUNDED
        self.data.funded_at = sp.now
        self.data.deadline = self._calculate_deadline()

    # ==========================================================================
    # ENTRY POINT: vote_release()
    # ==========================================================================

    @sp.entry_point
    def vote_release(self):
        """
        Cast vote to release funds to beneficiary.

        Authorization: Any of the three parties
        Effect: If 2+ votes for release, funds are released

        A party can change their vote by calling vote_refund() instead.
        """

        # State check
        sp.verify(self.data.state == STATE_FUNDED, EscrowError.NOT_FUNDED)

        # Auth check - must be a party
        self._require_party()

        # Record/update vote
        voter = sp.sender

        # If already voted, update counts
        with sp.if_(self.data.votes.contains(voter)):
            previous_vote = self.data.votes[voter]

            # Only update if changing vote
            with sp.if_(previous_vote != VOTE_RELEASE):
                # Remove from refund count
                with sp.if_(previous_vote == VOTE_REFUND):
                    self.data.refund_votes = sp.as_nat(self.data.refund_votes - 1)

                # Add to release count
                self.data.release_votes = self.data.release_votes + 1
                self.data.votes[voter] = VOTE_RELEASE

        with sp.else_():
            # First vote
            self.data.votes[voter] = VOTE_RELEASE
            self.data.release_votes = self.data.release_votes + 1

        # Check for consensus
        self._check_consensus()

    # ==========================================================================
    # ENTRY POINT: vote_refund()
    # ==========================================================================

    @sp.entry_point
    def vote_refund(self):
        """
        Cast vote to refund funds to depositor.

        Authorization: Any of the three parties
        Effect: If 2+ votes for refund, funds are refunded

        A party can change their vote by calling vote_release() instead.
        """

        # State check
        sp.verify(self.data.state == STATE_FUNDED, EscrowError.NOT_FUNDED)

        # Auth check
        self._require_party()

        # Record/update vote
        voter = sp.sender

        with sp.if_(self.data.votes.contains(voter)):
            previous_vote = self.data.votes[voter]

            with sp.if_(previous_vote != VOTE_REFUND):
                # Remove from release count
                with sp.if_(previous_vote == VOTE_RELEASE):
                    self.data.release_votes = sp.as_nat(self.data.release_votes - 1)

                # Add to refund count
                self.data.refund_votes = self.data.refund_votes + 1
                self.data.votes[voter] = VOTE_REFUND

        with sp.else_():
            self.data.votes[voter] = VOTE_REFUND
            self.data.refund_votes = self.data.refund_votes + 1

        # Check for consensus
        self._check_consensus()

    # ==========================================================================
    # ENTRY POINT: raise_dispute()
    # ==========================================================================

    @sp.entry_point
    def raise_dispute(self, reason):
        """
        Raise a dispute for arbiter attention.

        Authorization: Depositor or Beneficiary (not arbiter)

        This is informational - it doesn't change voting mechanics,
        but signals to the arbiter that intervention is needed.
        """

        sp.set_type(reason, sp.TString)

        # State check
        sp.verify(self.data.state == STATE_FUNDED, EscrowError.NOT_FUNDED)

        # Auth check - only depositor or beneficiary can raise dispute
        sp.verify(
            (sp.sender == self.data.depositor) |
            (sp.sender == self.data.beneficiary),
            EscrowError.UNAUTHORIZED
        )

        # Set dispute state
        self.data.dispute_state = DISPUTE_PENDING
        self.data.dispute_reason = reason

    # ==========================================================================
    # ENTRY POINT: force_refund()
    # ==========================================================================

    @sp.entry_point
    def force_refund(self):
        """
        Emergency recovery after timeout.

        Authorization: Anyone (permissionless)
        Condition: Timeout must have expired

        Anti-fund-locking guarantee: funds are always recoverable.
        """

        # State check
        sp.verify(self.data.state == STATE_FUNDED, EscrowError.NOT_FUNDED)

        # Timeout check
        sp.verify(self._is_timeout_expired(), EscrowError.TIMEOUT_NOT_EXPIRED)

        # Execute refund
        self._execute_refund()

    # ==========================================================================
    # VIEW: get_status()
    # ==========================================================================

    @sp.onchain_view()
    def get_status(self):
        """Query comprehensive escrow status"""

        is_funded = self.data.state == STATE_FUNDED
        is_terminal = (self.data.state == STATE_RELEASED) | \
                      (self.data.state == STATE_REFUNDED)

        # Map state to name
        state_name = sp.local("state_name", "UNKNOWN")
        with sp.if_(self.data.state == STATE_INIT):
            state_name.value = "INIT"
        with sp.if_(self.data.state == STATE_FUNDED):
            state_name.value = "FUNDED"
        with sp.if_(self.data.state == STATE_RELEASED):
            state_name.value = "RELEASED"
        with sp.if_(self.data.state == STATE_REFUNDED):
            state_name.value = "REFUNDED"

        sp.result(
            sp.record(
                state=self.data.state,
                state_name=state_name.value,
                depositor=self.data.depositor,
                beneficiary=self.data.beneficiary,
                arbiter=self.data.arbiter,
                amount=self.data.escrow_amount,
                deadline=self.data.deadline,
                is_funded=is_funded,
                is_terminal=is_terminal,
                release_votes=self.data.release_votes,
                refund_votes=self.data.refund_votes,
                dispute_state=self.data.dispute_state,
                is_timeout_expired=self._is_timeout_expired()
            )
        )

    # ==========================================================================
    # VIEW: get_votes()
    # ==========================================================================

    @sp.onchain_view()
    def get_votes(self):
        """Get current voting status"""

        # Get individual votes (default to -1 if not voted)
        depositor_vote = sp.local("dv", sp.int(-1))
        beneficiary_vote = sp.local("bv", sp.int(-1))
        arbiter_vote = sp.local("av", sp.int(-1))

        with sp.if_(self.data.votes.contains(self.data.depositor)):
            depositor_vote.value = self.data.votes[self.data.depositor]

        with sp.if_(self.data.votes.contains(self.data.beneficiary)):
            beneficiary_vote.value = self.data.votes[self.data.beneficiary]

        with sp.if_(self.data.votes.contains(self.data.arbiter)):
            arbiter_vote.value = self.data.votes[self.data.arbiter]

        sp.result(
            sp.record(
                depositor_vote=depositor_vote.value,
                beneficiary_vote=beneficiary_vote.value,
                arbiter_vote=arbiter_vote.value,
                release_votes=self.data.release_votes,
                refund_votes=self.data.refund_votes,
                votes_needed=sp.nat(2)
            )
        )

    # ==========================================================================
    # VIEW: get_parties()
    # ==========================================================================

    @sp.onchain_view()
    def get_parties(self):
        """Return all party addresses"""
        sp.result(
            sp.record(
                depositor=self.data.depositor,
                beneficiary=self.data.beneficiary,
                arbiter=self.data.arbiter
            )
        )


# ==============================================================================
# COMPILATION TARGET
# ==============================================================================

@sp.add_compilation_target("MultiSigEscrow")
def compile_multisig_escrow():
    """Compile MultiSigEscrow for deployment"""
    return MultiSigEscrow(
        depositor=sp.address("tz1Depositor"),
        beneficiary=sp.address("tz1Beneficiary"),
        arbiter=sp.address("tz1Arbiter"),
        amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
