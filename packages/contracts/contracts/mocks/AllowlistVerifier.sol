// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// import "./IVerifiedCredentialVerifier.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

interface IVerifiedCredentialVerifier {
    function verifyCredential(address user, bytes calldata proof) external returns (bool isValid);
}

/**
 * @title AllowlistVerifier
 * @notice Simple Verifier that checks if an address is explicitly allowlisted by Admin.
 * @dev Replaces MockVerifier for more realistic testing before full DID integration.
 */
contract AllowlistVerifier is IVerifiedCredentialVerifier, Ownable {
    mapping(address => bool) public allowed;

    constructor() Ownable(msg.sender) {}

    function setAllowed(address user, bool status) external onlyOwner {
        allowed[user] = status;
    }

    // Bulk allow for testing
    function setAllowedBatch(address[] calldata users, bool status) external onlyOwner {
        for (uint256 i = 0; i < users.length; i++) {
            allowed[users[i]] = status;
        }
    }

    function verifyCredential(address user, bytes calldata /* proof */) external view override returns (bool) {
        return allowed[user];
    }
}
