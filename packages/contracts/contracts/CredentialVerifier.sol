// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts-upgradeable/utils/cryptography/EIP712Upgradeable.sol";

/**
 * @title CredentialVerifier
 * @notice Production verifier for AgentRegistry using EIP-712 signed attestations.
 * @dev An off-chain trusted signer verifies VC JWTs (Ed25519, did:key) from trust-sdk,
 *      then issues a secp256k1 ECDSA attestation that this contract can verify on-chain.
 *
 * Security Model:
 *   - EIP-712 typed data prevents cross-chain and cross-contract replay attacks
 *   - Nullifier mapping prevents Sybil attacks (one DID → one registration)
 *   - Deadline prevents indefinite attestation reuse
 *   - Trusted signer can be rotated by admin
 */
contract CredentialVerifier is Initializable, UUPSUpgradeable, AccessControlUpgradeable, EIP712Upgradeable {
    using ECDSA for bytes32;

    bytes32 public constant UPGRADER_ROLE = keccak256("UPGRADER_ROLE");

    /// @notice The EIP-712 typehash for Attestation structs
    bytes32 public constant ATTESTATION_TYPEHASH =
        keccak256("Attestation(address user,bytes32 didHash,uint256 deadline)");

    /// @notice The trusted off-chain signer that issues attestations
    address public trustedSigner;

    /// @notice Mapping of DID hashes that have already been used (Sybil resistance)
    mapping(bytes32 => bool) public usedNullifiers;

    event TrustedSignerUpdated(address indexed oldSigner, address indexed newSigner);
    event AttestationVerified(address indexed user, bytes32 indexed didHash);

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }

    /**
     * @notice Initializes the verifier with admin and trusted signer.
     * @param _admin Address with admin and upgrade permissions.
     * @param _trustedSigner Address of the off-chain attestation signer.
     */
    function initialize(address _admin, address _trustedSigner) public initializer {
        require(_trustedSigner != address(0), "Invalid signer address");

        __AccessControl_init();
        __UUPSUpgradeable_init();
        __EIP712_init("CredentialVerifier", "1");

        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(UPGRADER_ROLE, _admin);

        trustedSigner = _trustedSigner;
    }

    /**
     * @notice Verifies a credential attestation. Called by AgentRegistry.register().
     * @dev Proof encoding: abi.encode(bytes32 didHash, uint256 deadline, bytes signature)
     * @param user The address of the registering agent.
     * @param proof ABI-encoded attestation (didHash, deadline, signature).
     * @return isValid True if the attestation is valid.
     */
    function verifyCredential(address user, bytes calldata proof) external returns (bool isValid) {
        // 1. Decode proof
        (bytes32 didHash, uint256 deadline, bytes memory signature) =
            abi.decode(proof, (bytes32, uint256, bytes));

        // 2. Check deadline
        require(block.timestamp <= deadline, "Attestation expired");

        // 3. Check nullifier (Sybil resistance)
        require(!usedNullifiers[didHash], "Nullifier already used");

        // 4. Reconstruct EIP-712 digest
        bytes32 structHash = keccak256(
            abi.encode(ATTESTATION_TYPEHASH, user, didHash, deadline)
        );
        bytes32 digest = _hashTypedDataV4(structHash);

        // 5. Recover signer and validate
        address recoveredSigner = digest.recover(signature);
        require(recoveredSigner != address(0), "Invalid signature");
        require(recoveredSigner == trustedSigner, "Invalid signer");

        // 6. Consume nullifier
        usedNullifiers[didHash] = true;

        emit AttestationVerified(user, didHash);
        return true;
    }

    /**
     * @notice Rotates the trusted signer. Admin-only.
     * @param _newSigner New trusted signer address.
     */
    function setTrustedSigner(address _newSigner) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_newSigner != address(0), "Invalid signer address");

        address oldSigner = trustedSigner;
        trustedSigner = _newSigner;

        emit TrustedSignerUpdated(oldSigner, _newSigner);
    }

    function _authorizeUpgrade(address newImplementation) internal onlyRole(UPGRADER_ROLE) override {}

    // Storage gap for future upgrades
    uint256[48] private __gap;
}
