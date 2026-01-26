/**
 * FortiEscrow TypeScript SDK
 * ==========================
 *
 * Lightweight SDK for integrating FortiEscrow into dApps.
 *
 * Features:
 *   - Type-safe escrow operations
 *   - Automatic status polling
 *   - Event subscription
 *   - Batch queries
 *
 * Security:
 *   - SDK is a thin wrapper over contract calls
 *   - No custody of funds or keys
 *   - All authorization enforced by on-chain contracts
 *
 * Usage:
 *   ```typescript
 *   import { FortiEscrowSDK } from '@forti-escrow/sdk';
 *
 *   const sdk = new FortiEscrowSDK({ rpcUrl: 'https://...' });
 *
 *   // Create escrow
 *   const escrow = await sdk.createEscrow({
 *     beneficiary: 'tz1...',
 *     amount: 1_000_000,
 *     timeoutSeconds: 86400
 *   });
 *
 *   // Fund it
 *   await sdk.fund(escrow.address);
 *
 *   // Release to beneficiary
 *   await sdk.release(escrow.address);
 *   ```
 */

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

/**
 * Escrow states matching on-chain FSM
 */
export enum EscrowState {
  INIT = 0,
  FUNDED = 1,
  RELEASED = 2,
  REFUNDED = 3
}

/**
 * Human-readable state names
 */
export const STATE_NAMES: Record<EscrowState, string> = {
  [EscrowState.INIT]: 'Awaiting Funding',
  [EscrowState.FUNDED]: 'Funded - Awaiting Decision',
  [EscrowState.RELEASED]: 'Released to Beneficiary',
  [EscrowState.REFUNDED]: 'Refunded to Depositor'
};

/**
 * Parameters for creating a new escrow
 */
export interface CreateEscrowParams {
  /** Beneficiary address (tz1...) */
  beneficiary: string;

  /** Escrow amount in mutez */
  amount: number;

  /** Timeout in seconds (min: 3600 = 1 hour) */
  timeoutSeconds: number;
}

/**
 * Full escrow status from on-chain query
 */
export interface EscrowStatus {
  /** Contract address */
  address: string;

  /** Current state */
  state: EscrowState;
  stateName: string;

  /** Parties */
  depositor: string;
  beneficiary: string;

  /** Financials */
  amount: number;
  balance: number;

  /** Timeline */
  deadline: Date;
  timeRemaining: number; // seconds
  isExpired: boolean;

  /** Available actions */
  canFund: boolean;
  canRelease: boolean;
  canRefund: boolean;
  canForceRefund: boolean;
}

/**
 * Transaction result
 */
export interface TxResult {
  /** Operation hash */
  opHash: string;

  /** Block level */
  blockLevel: number;

  /** Success flag */
  success: boolean;

  /** Error message if failed */
  error?: string;
}

/**
 * SDK configuration
 */
export interface SDKConfig {
  /** Tezos RPC URL */
  rpcUrl: string;

  /** Adapter contract address (optional, for registry queries) */
  adapterAddress?: string;

  /** Polling interval in ms (default: 5000) */
  pollInterval?: number;
}

// =============================================================================
// SDK IMPLEMENTATION
// =============================================================================

/**
 * FortiEscrow SDK
 *
 * Provides type-safe access to escrow operations.
 *
 * Security Model:
 *   - SDK never stores private keys
 *   - All operations require wallet signature
 *   - Authorization enforced by on-chain contracts
 *   - SDK cannot bypass any security checks
 */
export class FortiEscrowSDK {
  private config: Required<SDKConfig>;
  private tezos: any; // TezosToolkit from @taquito/taquito

  constructor(config: SDKConfig) {
    this.config = {
      rpcUrl: config.rpcUrl,
      adapterAddress: config.adapterAddress || '',
      pollInterval: config.pollInterval || 5000
    };

    // Initialize Taquito (pseudo-code)
    // this.tezos = new TezosToolkit(config.rpcUrl);
  }

  // ===========================================================================
  // WALLET CONNECTION
  // ===========================================================================

  /**
   * Connect wallet (Beacon, Temple, etc.)
   *
   * SDK does NOT store keys - wallet handles signing.
   */
  async connectWallet(walletProvider: any): Promise<string> {
    // this.tezos.setWalletProvider(walletProvider);
    // return await walletProvider.getPKH();
    throw new Error('Implement with actual Taquito');
  }

  /**
   * Get connected wallet address
   */
  async getAddress(): Promise<string> {
    // return await this.tezos.wallet.pkh();
    throw new Error('Implement with actual Taquito');
  }

  // ===========================================================================
  // ESCROW CREATION
  // ===========================================================================

  /**
   * Create a new escrow contract.
   *
   * The connected wallet becomes the depositor.
   * Escrow is NOT funded - call fund() separately.
   *
   * @param params Creation parameters
   * @returns Deployed escrow address
   *
   * Security:
   *   - Wallet signs transaction
   *   - Caller address stored as depositor
   *   - No funds transferred yet
   */
  async createEscrow(params: CreateEscrowParams): Promise<{ address: string; opHash: string }> {
    this.validateCreateParams(params);

    // Call adapter.create_escrow or deploy directly
    // const op = await this.tezos.wallet.originate({
    //   code: escrowCode,
    //   storage: { depositor: await this.getAddress(), ... }
    // }).send();
    // await op.confirmation();
    // return { address: op.contractAddress, opHash: op.opHash };

    throw new Error('Implement with actual Taquito');
  }

  /**
   * Create and fund escrow in one transaction.
   *
   * Convenience method that creates and funds atomically.
   *
   * @param params Creation parameters (amount must match sent tez)
   */
  async createAndFund(params: CreateEscrowParams): Promise<{ address: string; opHash: string }> {
    this.validateCreateParams(params);

    // Call adapter.create_and_fund with attached tez
    // const adapter = await this.tezos.wallet.at(this.config.adapterAddress);
    // const op = await adapter.methods.create_and_fund(params).send({ amount: params.amount, mutez: true });

    throw new Error('Implement with actual Taquito');
  }

  // ===========================================================================
  // ESCROW OPERATIONS
  // ===========================================================================

  /**
   * Fund an escrow.
   *
   * Caller must be the depositor.
   * Must send exact escrow amount.
   *
   * @param escrowAddress Address of escrow to fund
   *
   * Security:
   *   - Escrow verifies caller == depositor
   *   - Escrow verifies amount == escrow_amount
   *   - SDK cannot bypass these checks
   */
  async fund(escrowAddress: string): Promise<TxResult> {
    const status = await this.getStatus(escrowAddress);

    if (status.state !== EscrowState.INIT) {
      throw new Error(`Cannot fund: escrow is in ${status.stateName} state`);
    }

    // const escrow = await this.tezos.wallet.at(escrowAddress);
    // const op = await escrow.methods.fund().send({ amount: status.amount, mutez: true });
    // await op.confirmation();
    // return { opHash: op.opHash, blockLevel: ..., success: true };

    throw new Error('Implement with actual Taquito');
  }

  /**
   * Release escrow funds to beneficiary.
   *
   * Caller must be the depositor.
   * Must be before deadline.
   *
   * @param escrowAddress Address of escrow to release
   *
   * Security:
   *   - Only depositor can release
   *   - Enforced on-chain, not by SDK
   */
  async release(escrowAddress: string): Promise<TxResult> {
    const status = await this.getStatus(escrowAddress);

    if (status.state !== EscrowState.FUNDED) {
      throw new Error(`Cannot release: escrow is in ${status.stateName} state`);
    }

    if (status.isExpired) {
      throw new Error('Cannot release: deadline has passed. Use forceRefund() instead.');
    }

    // const escrow = await this.tezos.wallet.at(escrowAddress);
    // const op = await escrow.methods.release().send();

    throw new Error('Implement with actual Taquito');
  }

  /**
   * Refund escrow funds to depositor.
   *
   * Caller must be the depositor.
   *
   * @param escrowAddress Address of escrow to refund
   *
   * Security:
   *   - Only depositor can refund
   *   - Enforced on-chain, not by SDK
   */
  async refund(escrowAddress: string): Promise<TxResult> {
    const status = await this.getStatus(escrowAddress);

    if (status.state !== EscrowState.FUNDED) {
      throw new Error(`Cannot refund: escrow is in ${status.stateName} state`);
    }

    // const escrow = await this.tezos.wallet.at(escrowAddress);
    // const op = await escrow.methods.refund().send();

    throw new Error('Implement with actual Taquito');
  }

  /**
   * Force refund after timeout.
   *
   * Anyone can call after deadline.
   * Funds always go to depositor.
   *
   * @param escrowAddress Address of escrow to force-refund
   *
   * Security:
   *   - Available to anyone after timeout
   *   - Funds go to depositor (not caller)
   *   - Anti-fund-locking guarantee
   */
  async forceRefund(escrowAddress: string): Promise<TxResult> {
    const status = await this.getStatus(escrowAddress);

    if (status.state !== EscrowState.FUNDED) {
      throw new Error(`Cannot force refund: escrow is in ${status.stateName} state`);
    }

    if (!status.isExpired) {
      throw new Error(`Cannot force refund: ${status.timeRemaining} seconds remaining`);
    }

    // const escrow = await this.tezos.wallet.at(escrowAddress);
    // const op = await escrow.methods.force_refund().send();

    throw new Error('Implement with actual Taquito');
  }

  // ===========================================================================
  // STATUS QUERIES
  // ===========================================================================

  /**
   * Get full escrow status.
   *
   * Aggregates on-chain data into convenient format.
   *
   * @param escrowAddress Address of escrow to query
   */
  async getStatus(escrowAddress: string): Promise<EscrowStatus> {
    // const escrow = await this.tezos.contract.at(escrowAddress);
    // const storage = await escrow.storage();
    // const status = await escrow.views.get_status().read();

    // Parse and return formatted status
    throw new Error('Implement with actual Taquito');
  }

  /**
   * Get all escrows where address is depositor.
   *
   * Requires adapter to be configured.
   *
   * @param depositorAddress Address to query
   */
  async getEscrowsAsDepositor(depositorAddress?: string): Promise<string[]> {
    const address = depositorAddress || await this.getAddress();

    // Query adapter registry
    // const adapter = await this.tezos.contract.at(this.config.adapterAddress);
    // const ids = await adapter.views.get_my_escrows_as_depositor(address).read();
    // return Promise.all(ids.map(id => adapter.views.get_escrow_address(id).read()));

    throw new Error('Implement with actual Taquito');
  }

  /**
   * Get all escrows where address is beneficiary.
   *
   * Requires adapter to be configured.
   *
   * @param beneficiaryAddress Address to query
   */
  async getEscrowsAsBeneficiary(beneficiaryAddress?: string): Promise<string[]> {
    const address = beneficiaryAddress || await this.getAddress();

    // Query adapter registry
    throw new Error('Implement with actual Taquito');
  }

  // ===========================================================================
  // EVENT SUBSCRIPTION
  // ===========================================================================

  /**
   * Subscribe to escrow state changes.
   *
   * Polls the contract at configured interval.
   *
   * @param escrowAddress Address to watch
   * @param callback Called on state change
   * @returns Unsubscribe function
   */
  subscribe(
    escrowAddress: string,
    callback: (status: EscrowStatus, previousState: EscrowState) => void
  ): () => void {
    let previousState: EscrowState | null = null;
    let active = true;

    const poll = async () => {
      if (!active) return;

      try {
        const status = await this.getStatus(escrowAddress);

        if (previousState !== null && status.state !== previousState) {
          callback(status, previousState);
        }

        previousState = status.state;
      } catch (error) {
        console.error('Polling error:', error);
      }

      if (active) {
        setTimeout(poll, this.config.pollInterval);
      }
    };

    poll();

    // Return unsubscribe function
    return () => {
      active = false;
    };
  }

  // ===========================================================================
  // VALIDATION HELPERS
  // ===========================================================================

  private validateCreateParams(params: CreateEscrowParams): void {
    if (!params.beneficiary || !params.beneficiary.startsWith('tz')) {
      throw new Error('Invalid beneficiary address');
    }

    if (params.amount <= 0) {
      throw new Error('Amount must be positive');
    }

    if (params.timeoutSeconds < 3600) {
      throw new Error('Timeout must be at least 1 hour (3600 seconds)');
    }

    if (params.timeoutSeconds > 365 * 24 * 3600) {
      throw new Error('Timeout cannot exceed 1 year');
    }
  }

  // ===========================================================================
  // UTILITY METHODS
  // ===========================================================================

  /**
   * Format mutez to XTZ string
   */
  static formatXTZ(mutez: number): string {
    return (mutez / 1_000_000).toFixed(6) + ' XTZ';
  }

  /**
   * Parse XTZ string to mutez
   */
  static parseXTZ(xtz: string): number {
    const num = parseFloat(xtz.replace(/[^0-9.]/g, ''));
    return Math.round(num * 1_000_000);
  }

  /**
   * Format remaining time as human-readable string
   */
  static formatTimeRemaining(seconds: number): string {
    if (seconds <= 0) return 'Expired';

    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    const parts: string[] = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);

    return parts.join(' ') || 'Less than 1 minute';
  }

  /**
   * Get recommended actions based on escrow status and caller role
   */
  static getRecommendedActions(
    status: EscrowStatus,
    callerAddress: string
  ): { action: string; description: string; enabled: boolean }[] {
    const isDepositor = callerAddress === status.depositor;
    const isBeneficiary = callerAddress === status.beneficiary;

    const actions: { action: string; description: string; enabled: boolean }[] = [];

    switch (status.state) {
      case EscrowState.INIT:
        actions.push({
          action: 'fund',
          description: `Fund escrow with ${this.formatXTZ(status.amount)}`,
          enabled: isDepositor
        });
        break;

      case EscrowState.FUNDED:
        if (!status.isExpired) {
          actions.push({
            action: 'release',
            description: 'Release funds to beneficiary',
            enabled: isDepositor
          });
          actions.push({
            action: 'refund',
            description: 'Cancel and refund to depositor',
            enabled: isDepositor
          });
        } else {
          actions.push({
            action: 'forceRefund',
            description: 'Recover funds (timeout expired)',
            enabled: true // Anyone can call
          });
        }
        break;

      case EscrowState.RELEASED:
        actions.push({
          action: 'none',
          description: 'Escrow completed - funds released to beneficiary',
          enabled: false
        });
        break;

      case EscrowState.REFUNDED:
        actions.push({
          action: 'none',
          description: 'Escrow canceled - funds returned to depositor',
          enabled: false
        });
        break;
    }

    return actions;
  }
}

// =============================================================================
// REACT HOOK EXAMPLE
// =============================================================================

/**
 * React hook for escrow status (example)
 *
 * Usage:
 *   const { status, loading, error, refresh } = useEscrowStatus(sdk, address);
 */
export function useEscrowStatus(sdk: FortiEscrowSDK, escrowAddress: string) {
  // This is a pseudo-implementation
  // Real implementation would use React useState, useEffect

  return {
    status: null as EscrowStatus | null,
    loading: false,
    error: null as Error | null,
    refresh: async () => {}
  };
}

// =============================================================================
// SECURITY DOCUMENTATION
// =============================================================================

/**
 * SDK SECURITY MODEL
 * ==================
 *
 * 1. NO KEY CUSTODY
 *    SDK never stores or handles private keys.
 *    All signing happens in the wallet (Beacon, Temple, etc.)
 *
 * 2. NO AUTHORIZATION BYPASS
 *    SDK calls on-chain contracts directly.
 *    Contracts enforce all authorization:
 *      - fund(): escrow checks caller is depositor
 *      - release(): escrow checks caller is depositor
 *      - refund(): escrow checks caller is depositor
 *      - forceRefund(): escrow checks timeout expired
 *
 * 3. NO FUND CUSTODY
 *    SDK never holds funds.
 *    Funds flow: wallet → escrow → beneficiary/depositor
 *
 * 4. CLIENT-SIDE VALIDATION
 *    SDK validates parameters before sending transactions.
 *    This is for UX only - contracts have their own validation.
 *    Even if SDK validation is bypassed, contracts are secure.
 *
 * 5. READ-ONLY QUERIES
 *    Status queries are read-only on-chain views.
 *    Cannot modify state.
 *
 * TRUST MODEL
 * -----------
 * Users must trust:
 *   ✓ Their wallet (handles keys)
 *   ✓ The Tezos RPC node (reads blockchain)
 *   ✓ The escrow contract code (audited)
 *
 * Users do NOT need to trust:
 *   ✗ This SDK (stateless wrapper)
 *   ✗ The adapter contract (pass-through only)
 *   ✗ Any centralized server (none required)
 */

export default FortiEscrowSDK;
