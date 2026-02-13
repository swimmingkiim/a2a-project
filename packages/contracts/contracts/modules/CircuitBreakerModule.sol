// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../interfaces/IERC7579Module.sol";

/**
 * @title CircuitBreakerModule
 * @notice ERC-7579 Hook Module for Gradual Throttling.
 * @dev Tracks outflow and applies Soft Limit (Freeze for X minutes) or Hard Limit (Check Admin).
 */
contract CircuitBreakerModule is IHook {
    struct RateLimit {
        uint256 outflow;      // Cumulative outflow in current window
        uint256 lastReset;    // Timestamp of last window reset
        bool isNativeToken;   // Tracking ETH or specific ERC20
    }

    // Account -> RateLimit
    mapping(address => RateLimit) public limits;
    
    // Configuration
    uint256 public constant WINDOW_SIZE = 1 hours;
    uint256 public constant SOFT_LIMIT = 1 ether; // 1 ETH warning threshold
    uint256 public constant HARD_LIMIT = 5 ether; // 5 ETH freeze threshold

    error HardLimitExceeded(uint256 currentOutflow);
    event SoftLimitReached(address indexed account, uint256 currentOutflow);

    // Type 4 = Hook
    function isModuleType(uint256 typeID) external pure override returns (bool) {
        return typeID == 4;
    }

    function onInstall(bytes calldata data) external override {}
    function onUninstall(bytes calldata data) external override {}

    /**
     * @notice Executed BEFORE the transaction.
     * @dev Checks rate limits.
     */
    function preCheck(
        address msgSender,
        uint256 value,
        bytes calldata func
    ) external override returns (bytes memory hookData) {
        RateLimit storage limit = limits[msgSender];

        // 1. Reset window if expired
        if (block.timestamp > limit.lastReset + WINDOW_SIZE) {
            limit.outflow = 0;
            limit.lastReset = block.timestamp;
        }

        // 2. Accumulate Spend (Native ETH value)
        // Note: For ERC20, we would need to decode `func` calldata (transfer/approve).
        limit.outflow += value;

        // 3. Check Limits
        if (limit.outflow > HARD_LIMIT) {
            revert HardLimitExceeded(limit.outflow);
        }
        
        if (limit.outflow > SOFT_LIMIT) {
            // Soft Limit: Emit warning but allow transaction to proceed.
            // Off-chain agents/Paymaster should observe this event and throttle/slow down requests for this account.
            // Future Upgrade: Implement dynamic fee bumping or on-chain delays here.
            emit SoftLimitReached(msgSender, limit.outflow);
        }

        return "";
    }

    /**
     * @notice Executed AFTER the transaction.
     */
    function postCheck(bytes calldata hookData) external override {}

    function getOutflow(address account) external view returns (uint256) {
        return limits[account].outflow;
    }
}
