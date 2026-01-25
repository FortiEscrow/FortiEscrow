"""
FortiEscrow Base Contract
=========================

Abstract base contract defining the escrow state machine and core logic.
All escrow variants (simple, multisig, conditional) inherit from this.

State Machine:
    INIT (0) ──► FUNDED (1) ──► RELEASED (2) [terminal]
                     │
                     └────────► REFUNDED (3) [terminal]

Security Invariants:
    1. State can only move forward (no regression)
    2. Terminal states (RELEASED, REFUNDED) are permanent
    3. Funds transfer only on terminal state entry
    4. Balance always equals escrow_amount when FUNDED
"""

import smartpy as sp


# ==============================================================================
# CONSTANTS
# ==============================================================================

# State machine states (integers for gas efficiency)
STATE_INIT = 0
STATE_FUNDED = 1
STATE_RELEASED = 2
STATE_REFUNDED = 3

# State names for human readability
STATE_NAMES = {
    0: "INIT",
    1: "FUNDED",
    2: "RELEASED",
    3: "REFUNDED"
}

# Minimum timeout: 1 hour (prevents flash-loan timing attacks)
MIN_TIMEOUT_SECONDS = 3600

# Maximum timeout: 1 year (prevents indefinite locking)
MAX_TIMEOUT_SECONDS = 365 * 24 * 3600


# ==============================================================================
# ERROR CODES
# ==============================================================================

class EscrowError:
    """Centralized error codes for all escrow contracts"""

    # State errors
    INVALID_STATE = "ESCROW_INVALID_STATE"
    ALREADY_FUNDED = "ESCROW_ALREADY_FUNDED"
    NOT_FUNDED = "ESCROW_NOT_FUNDED"
    TERMINAL_STATE = "ESCROW_TERMINAL_STATE"

    # Authorization errors
    UNAUTHORIZED = "ESCROW_UNAUTHORIZED"
    NOT_DEPOSITOR = "ESCROW_NOT_DEPOSITOR"
    NOT_BENEFICIARY = "ESCROW_NOT_BENEFICIARY"

    # Amount errors
    ZERO_AMOUNT = "ESCROW_ZERO_AMOUNT"
    AMOUNT_MISMATCH = "ESCROW_AMOUNT_MISMATCH"
    INSUFFICIENT_BALANCE = "ESCROW_INSUFFICIENT_BALANCE"

    # Timeout errors
    TIMEOUT_TOO_SHORT = "ESCROW_TIMEOUT_TOO_SHORT"
    TIMEOUT_TOO_LONG = "ESCROW_TIMEOUT_TOO_LONG"
    TIMEOUT_NOT_EXPIRED = "ESCROW_TIMEOUT_NOT_EXPIRED"
    DEADLINE_PASSED = "ESCROW_DEADLINE_PASSED"

    # Parameter errors
    INVALID_PARAMS = "ESCROW_INVALID_PARAMS"
    SAME_PARTY = "ESCROW_SAME_PARTY"
    INVALID_ADDRESS = "ESCROW_INVALID_ADDRESS"


# ==============================================================================
# TYPE DEFINITIONS
# ==============================================================================

# Escrow configuration passed to factory
EscrowConfig = sp.TRecord(
    depositor=sp.TAddress,
    beneficiary=sp.TAddress,
    amount=sp.TNat,
    timeout_seconds=sp.TNat
)

# Escrow status for views
EscrowStatus = sp.TRecord(
    state=sp.TInt,
    state_name=sp.TString,
    depositor=sp.TAddress,
    beneficiary=sp.TAddress,
    amount=sp.TNat,
    deadline=sp.TTimestamp,
    is_funded=sp.TBool,
    is_terminal=sp.TBool,
    can_release=sp.TBool,
    can_refund=sp.TBool,
    can_force_refund=sp.TBool
)


# ==============================================================================
# BASE CONTRACT
# ==============================================================================

class EscrowBase(sp.Contract):
    """
    Abstract base class for all FortiEscrow variants.

    Implements:
        - State machine enforcement
        - Fund validation
        - Timeout calculations
        - Event emission

    Subclasses must implement:
        - Authorization logic for release/refund
        - Any additional entry points
    """

    def __init__(self, depositor, beneficiary, amount, timeout_seconds):
        """
        Initialize escrow base contract.

        Args:
            depositor: Address that funds the escrow
            beneficiary: Address that receives funds on release
            amount: Escrow amount in mutez
            timeout_seconds: Seconds until force-refund becomes available

        Security Validations:
            - depositor != beneficiary (prevents self-escrow exploit)
            - amount > 0 (prevents empty escrow)
            - MIN_TIMEOUT <= timeout <= MAX_TIMEOUT
        """

        # ===== INPUT VALIDATION =====

        # Prevent self-escrow (depositor paying themselves)
        sp.verify(
            depositor != beneficiary,
            EscrowError.SAME_PARTY
        )

        # Prevent zero-amount escrows
        sp.verify(
            amount > sp.nat(0),
            EscrowError.ZERO_AMOUNT
        )

        # Enforce minimum timeout (1 hour)
        sp.verify(
            timeout_seconds >= sp.nat(MIN_TIMEOUT_SECONDS),
            EscrowError.TIMEOUT_TOO_SHORT
        )

        # Enforce maximum timeout (1 year)
        sp.verify(
            timeout_seconds <= sp.nat(MAX_TIMEOUT_SECONDS),
            EscrowError.TIMEOUT_TOO_LONG
        )

        # ===== STATE INITIALIZATION =====

        self.init(
            # Parties (immutable)
            depositor=depositor,
            beneficiary=beneficiary,

            # Escrow terms (immutable)
            escrow_amount=amount,

            # Deadline calculated as: deployment_time + timeout
            # This is set during __init__, but actual deadline should be
            # calculated from funding time for security
            timeout_seconds=timeout_seconds,

            # State machine
            state=STATE_INIT,

            # Funding timestamp (set when funded)
            funded_at=sp.timestamp(0),

            # Deadline (calculated when funded)
            deadline=sp.timestamp(0)
        )

    # ==========================================================================
    # INTERNAL HELPERS
    # ==========================================================================

    def _require_state(self, expected_state, error_msg):
        """Verify contract is in expected state"""
        sp.verify(self.data.state == expected_state, error_msg)

    def _require_not_terminal(self):
        """Verify contract is not in terminal state"""
        sp.verify(
            (self.data.state != STATE_RELEASED) &
            (self.data.state != STATE_REFUNDED),
            EscrowError.TERMINAL_STATE
        )

    def _require_funded(self):
        """Verify contract is funded"""
        sp.verify(self.data.state == STATE_FUNDED, EscrowError.NOT_FUNDED)

    def _require_sender(self, expected, error_msg):
        """Verify sender is expected address"""
        sp.verify(sp.sender == expected, error_msg)

    def _is_timeout_expired(self):
        """Check if timeout has passed"""
        return sp.now > self.data.deadline

    def _calculate_deadline(self):
        """Calculate deadline from current time + timeout"""
        return sp.add_seconds(sp.now, sp.to_int(self.data.timeout_seconds))

    def _transfer_to_beneficiary(self):
        """Transfer escrow funds to beneficiary"""
        sp.send(
            self.data.beneficiary,
            sp.utils.nat_to_mutez(self.data.escrow_amount)
        )

    def _transfer_to_depositor(self):
        """Transfer escrow funds back to depositor"""
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
        INIT → FUNDED: Deposit exact escrow amount.

        Authorization: Only depositor can fund

        Security Checks:
            1. State must be INIT
            2. Sender must be depositor
            3. Amount must match exactly
            4. Deadline not yet calculated (first funding)

        Effects:
            - State changes to FUNDED
            - funded_at timestamp recorded
            - deadline calculated from now + timeout
        """

        # [STATE CHECK] Must be in INIT state
        self._require_state(STATE_INIT, EscrowError.ALREADY_FUNDED)

        # [AUTH CHECK] Only depositor can fund
        self._require_sender(self.data.depositor, EscrowError.NOT_DEPOSITOR)

        # [AMOUNT CHECK] Exact amount required
        sp.verify(
            sp.amount == sp.utils.nat_to_mutez(self.data.escrow_amount),
            EscrowError.AMOUNT_MISMATCH
        )

        # [STATE TRANSITION] INIT → FUNDED
        self.data.state = STATE_FUNDED
        self.data.funded_at = sp.now
        self.data.deadline = self._calculate_deadline()

    # ==========================================================================
    # ENTRY POINT: release()
    # ==========================================================================

    @sp.entry_point
    def release(self):
        """
        FUNDED → RELEASED: Transfer funds to beneficiary.

        Authorization: Only depositor can release (owns the funds)

        Security Checks:
            1. State must be FUNDED
            2. Sender must be depositor
            3. Deadline must not have passed

        Effects:
            - State changes to RELEASED (terminal)
            - Funds transferred to beneficiary

        Rationale:
            Depositor has sole release authority because:
            - They own the funds
            - Prevents disputes over release
            - Timeout provides recovery if depositor unresponsive
        """

        # [STATE CHECK] Must be funded
        self._require_funded()

        # [AUTH CHECK] Only depositor can release
        self._require_sender(self.data.depositor, EscrowError.NOT_DEPOSITOR)

        # [TIMEOUT CHECK] Cannot release after deadline
        sp.verify(
            sp.now <= self.data.deadline,
            EscrowError.DEADLINE_PASSED
        )

        # [STATE TRANSITION] FUNDED → RELEASED (before transfer!)
        self.data.state = STATE_RELEASED

        # [TRANSFER] Send funds to beneficiary
        self._transfer_to_beneficiary()

    # ==========================================================================
    # ENTRY POINT: refund()
    # ==========================================================================

    @sp.entry_point
    def refund(self):
        """
        FUNDED → REFUNDED: Return funds to depositor.

        Authorization: Only depositor can refund before deadline

        Security Checks:
            1. State must be FUNDED
            2. Sender must be depositor

        Effects:
            - State changes to REFUNDED (terminal)
            - Funds returned to depositor

        Note:
            For force-refund after deadline, use force_refund() which
            is permissionless (anyone can trigger recovery).
        """

        # [STATE CHECK] Must be funded
        self._require_funded()

        # [AUTH CHECK] Only depositor can refund
        self._require_sender(self.data.depositor, EscrowError.NOT_DEPOSITOR)

        # [STATE TRANSITION] FUNDED → REFUNDED (before transfer!)
        self.data.state = STATE_REFUNDED

        # [TRANSFER] Return funds to depositor
        self._transfer_to_depositor()

    # ==========================================================================
    # ENTRY POINT: force_refund()
    # ==========================================================================

    @sp.entry_point
    def force_refund(self):
        """
        FUNDED → REFUNDED: Emergency recovery after timeout.

        Authorization: ANYONE can call (permissionless recovery)

        Security Checks:
            1. State must be FUNDED
            2. Deadline must have passed

        Effects:
            - State changes to REFUNDED (terminal)
            - Funds returned to depositor (always)

        Anti-Fund-Locking Guarantee:
            This ensures funds are NEVER permanently locked.
            After timeout expires, any party can trigger recovery.
            Funds always go to depositor (immutable destination).
        """

        # [STATE CHECK] Must be funded
        self._require_funded()

        # [TIMEOUT CHECK] Must be after deadline
        sp.verify(
            self._is_timeout_expired(),
            EscrowError.TIMEOUT_NOT_EXPIRED
        )

        # [STATE TRANSITION] FUNDED → REFUNDED (before transfer!)
        self.data.state = STATE_REFUNDED

        # [TRANSFER] Return funds to depositor
        self._transfer_to_depositor()

    # ==========================================================================
    # VIEW: get_status()
    # ==========================================================================

    @sp.onchain_view()
    def get_status(self):
        """
        Query comprehensive escrow status.

        Returns all relevant information for UI/automation:
            - Current state and human-readable name
            - Party addresses
            - Amount and deadline
            - Boolean flags for available actions
        """

        is_funded = self.data.state == STATE_FUNDED
        is_terminal = (self.data.state == STATE_RELEASED) | (self.data.state == STATE_REFUNDED)
        timeout_expired = sp.now > self.data.deadline

        # Determine available actions
        can_release = is_funded & (sp.now <= self.data.deadline)
        can_refund = is_funded
        can_force_refund = is_funded & timeout_expired

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
                amount=self.data.escrow_amount,
                deadline=self.data.deadline,
                is_funded=is_funded,
                is_terminal=is_terminal,
                can_release=can_release,
                can_refund=can_refund,
                can_force_refund=can_force_refund
            )
        )

    # ==========================================================================
    # VIEW: get_parties()
    # ==========================================================================

    @sp.onchain_view()
    def get_parties(self):
        """Return escrow party addresses"""
        sp.result(
            sp.record(
                depositor=self.data.depositor,
                beneficiary=self.data.beneficiary
            )
        )

    # ==========================================================================
    # VIEW: get_timeline()
    # ==========================================================================

    @sp.onchain_view()
    def get_timeline(self):
        """Return escrow timeline information"""
        sp.result(
            sp.record(
                funded_at=self.data.funded_at,
                deadline=self.data.deadline,
                timeout_seconds=self.data.timeout_seconds,
                is_expired=self._is_timeout_expired()
            )
        )


# ==============================================================================
# SIMPLE ESCROW (Concrete Implementation)
# ==============================================================================

class SimpleEscrow(EscrowBase):
    """
    Basic two-party escrow contract.

    This is the simplest escrow variant:
        - Depositor funds the escrow
        - Depositor can release to beneficiary
        - Depositor can refund to themselves
        - Anyone can force-refund after timeout

    Use Cases:
        - Simple buyer-seller transactions
        - Service payment holding
        - Deposit/collateral management
    """

    def __init__(self, depositor, beneficiary, amount, timeout_seconds):
        EscrowBase.__init__(self, depositor, beneficiary, amount, timeout_seconds)


# ==============================================================================
# COMPILATION TARGET
# ==============================================================================

@sp.add_compilation_target("SimpleEscrow")
def compile_simple_escrow():
    """Compile SimpleEscrow for deployment"""
    return SimpleEscrow(
        depositor=sp.address("tz1Depositor"),
        beneficiary=sp.address("tz1Beneficiary"),
        amount=sp.nat(1_000_000),
        timeout_seconds=sp.nat(7 * 24 * 3600)
    )
