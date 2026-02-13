// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../interfaces/IERC7579Module.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

// Mock Rep interface for this example
interface IReputationSystem {
    function getReputation(address agent) external view returns (uint256); // 0-100
}

/**
 * @title SessionKeyModule
 * @notice ERC-7579 Validator Module for temporary session keys.
 * @dev Implements reputation-based expiry (Higher Rep = Longer Session).
 */
contract SessionKeyModule is IValidator, Ownable {
    IReputationSystem public reputationSystem;

    struct Session {
        address sessionKey;
        uint48 validUntil;
        uint48 validAfter;
        address targetContract; // Scope: Can only call this contract
        uint256 spendLimit;     // Scope: Max value
        uint256 spentAmount;    // Tracked spend
    }

    // Mapping: Account -> SessionKey -> Session Data
    mapping(address => mapping(address => Session)) public sessions;

    // Type 1 = Validator
    function isModuleType(uint256 typeID) external pure override returns (bool) {
        return typeID == 1;
    }

    constructor(address _reputationSystem) Ownable(msg.sender) {
        reputationSystem = IReputationSystem(_reputationSystem);
    }

    function onInstall(bytes calldata data) external override {}
    function onUninstall(bytes calldata data) external override {}

    /**
     * @notice Creates a session key for an external signer.
     * @dev Only the Account itself (via self-call) or Owner can create sessions.
     * @param _sessionKey The address to authorize.
     * @param _targetContract The allowed contract to call.
     * @param _spendLimit The max value/wei allowed.
     */
    function createSession(
        address _sessionKey,
        address _targetContract,
        uint256 _spendLimit
    ) external {
        // In real ERC-7579, this would be guarded by `msg.sender == account`.
        // For this demo, we assume msg.sender is the account installing the key.
        
        // 1. Calculate Duration based on Reputation
        uint256 rep = 0; 
        if (address(reputationSystem) != address(0)) {
            try reputationSystem.getReputation(msg.sender) returns (uint256 r) {
                rep = r;
            } catch {}
        }
        
        // Base: 1 Hour. Bonus: +1 Hour per 10 Rep points.
        // Max Rep 100 -> +10 Hours -> Total 11 Hours.
        uint48 duration = uint48(3600 + (rep / 10) * 3600);
        
        Session memory newSession = Session({
            sessionKey: _sessionKey,
            validUntil: uint48(block.timestamp + duration),
            validAfter: uint48(block.timestamp),
            targetContract: _targetContract,
            spendLimit: _spendLimit,
            spentAmount: 0
        });

        sessions[msg.sender][_sessionKey] = newSession;
    }

    /**
     * @notice Validate signature using Session Key logic.
     * @dev Simplistic validation for demo. Real implementation parses UserOp fully.
     */
    function validateUserOp(
        bytes32 userOpHash,
        bytes calldata userOp
    ) external override returns (uint256) {
        // In a real module:
        // 1. Decode userOp.signature to recover signer.
        // 2. Check if signer is a valid session key for msg.sender (account).
        // 3. Check deadlines (validAfter, validUntil).
        // 4. Decode userOp.callData to check targetContract and value.
        
        // For prototype, we perform a stub check:
        // We assume signature recovery happens and returns 'signer'.
        // return SIG_VALIDATION_SUCCESS;
        return 0; 
    }

    /**
     * @notice EIP-1271 check.
     */
    function isValidSignatureWithSender(
        address sender,
        bytes32 hash,
        bytes calldata signature
    ) external view override returns (bytes4) {
        return 0xffffffff; // Stub
    }

    /**
     * @notice Helper to check session validity (used by unit tests).
     */
    function getSession(address account, address key) external view returns (Session memory) {
        return sessions[account][key];
    }
}
