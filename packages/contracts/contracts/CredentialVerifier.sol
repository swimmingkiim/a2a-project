// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts-upgradeable/utils/cryptography/EIP712Upgradeable.sol";

/**
 * @title IAgentRegistryReader
 * @notice Minimal read interface for checking agent registration status.
 */
interface IAgentRegistryReader {
    function agents(address) external view returns (
        string memory metadataUrl,
        uint256 stakedAmount,
        uint256 resourceUnits,
        uint64 registeredAt,
        bool isRegistered,
        uint8 reputation,
        uint256 lastComplexityHash
    );
}

/**
 * @title CredentialVerifier (Web of Trust)
 * @notice Production verifier for AgentRegistry using peer vouching.
 * @dev Any registered agent can vouch for a new agent by signing an EIP-712 attestation.
 *      The vouching relationship is recorded on-chain for trust path traceability.
 *
 * Security Model:
 *   - EIP-712 typed data prevents cross-chain and cross-contract replay attacks
 *   - Nullifier mapping prevents Sybil attacks (one DID → one registration)
 *   - Deadline prevents indefinite attestation reuse
 *   - Voucher must be a registered agent in AgentRegistry
 *   - vouchedBy mapping enables trust path tracing
 *   - Admin can set initial voucher (bootstrap) before any agents exist
 */
contract CredentialVerifier is Initializable, UUPSUpgradeable, AccessControlUpgradeable, EIP712Upgradeable {
    using ECDSA for bytes32;

    bytes32 public constant UPGRADER_ROLE = keccak256("UPGRADER_ROLE");

    /// @notice The EIP-712 typehash for Attestation structs
    bytes32 public constant ATTESTATION_TYPEHASH =
        keccak256("Attestation(address user,bytes32 didHash,uint256 deadline)");

    /// @notice Reference to AgentRegistry for checking voucher registration
    IAgentRegistryReader public agentRegistry;

    /// @notice Bootstrap voucher (used only when no agents are registered yet)
    address public bootstrapVoucher;

    /// @notice Mapping of DID hashes that have already been used (Sybil resistance)
    mapping(bytes32 => bool) public usedNullifiers;

    /// @notice Trust path: who vouched for whom
    mapping(address => address) public vouchedBy;

    event VouchRecorded(address indexed user, address indexed voucher, bytes32 indexed didHash);
    event BootstrapVoucherUpdated(address indexed oldVoucher, address indexed newVoucher);
    event AgentRegistryUpdated(address indexed newRegistry);

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }

    /**
     * @notice Initializes the verifier.
     * @param _admin Address with admin and upgrade permissions.
     * @param _agentRegistry Address of the AgentRegistry contract.
     * @param _bootstrapVoucher Initial voucher for bootstrapping (before any agents exist).
     */
    function initialize(
        address _admin,
        address _agentRegistry,
        address _bootstrapVoucher
    ) public initializer {
        require(_agentRegistry != address(0), "Invalid registry address");
        require(_bootstrapVoucher != address(0), "Invalid bootstrap voucher");

        __AccessControl_init();
        __UUPSUpgradeable_init();
        __EIP712_init("CredentialVerifier", "1");

        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(UPGRADER_ROLE, _admin);

        agentRegistry = IAgentRegistryReader(_agentRegistry);
        bootstrapVoucher = _bootstrapVoucher;
    }

    /**
     * @notice Verifies a credential attestation. Called by AgentRegistry.register().
     * @dev The voucher (signer) must be either:
     *      1. A registered agent in AgentRegistry, OR
     *      2. The bootstrap voucher (for initial ecosystem seeding)
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

        // 5. Recover signer (voucher)
        address voucher = digest.recover(signature);
        require(voucher != address(0), "Invalid signature");

        // 6. Validate voucher: must be registered agent OR bootstrap voucher
        bool isRegisteredAgent = _isRegisteredAgent(voucher);
        bool isBootstrap = (voucher == bootstrapVoucher);
        require(isRegisteredAgent || isBootstrap, "Voucher not authorized");

        // 7. Consume nullifier
        usedNullifiers[didHash] = true;

        // 8. Record trust path
        vouchedBy[user] = voucher;

        emit VouchRecorded(user, voucher, didHash);
        return true;
    }

    /**
     * @notice Traces the trust path from an agent back to the root.
     * @param agent Address to trace.
     * @param maxDepth Maximum depth to traverse (gas safety).
     * @return path Array of addresses in the trust chain.
     */
    function getTrustPath(address agent, uint256 maxDepth) external view returns (address[] memory) {
        address[] memory path = new address[](maxDepth);
        address current = agent;
        uint256 depth = 0;

        while (depth < maxDepth && vouchedBy[current] != address(0)) {
            path[depth] = vouchedBy[current];
            current = vouchedBy[current];
            depth++;
        }

        // Resize array
        assembly {
            mstore(path, depth)
        }
        return path;
    }

    /**
     * @notice Updates the bootstrap voucher. Admin-only.
     * @dev Can be set to address(0) to disable bootstrap once ecosystem is self-sustaining.
     */
    function setBootstrapVoucher(address _newVoucher) external onlyRole(DEFAULT_ADMIN_ROLE) {
        address old = bootstrapVoucher;
        bootstrapVoucher = _newVoucher;
        emit BootstrapVoucherUpdated(old, _newVoucher);
    }

    /**
     * @notice Updates the AgentRegistry reference. Admin-only.
     */
    function setAgentRegistry(address _newRegistry) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_newRegistry != address(0), "Invalid registry address");
        agentRegistry = IAgentRegistryReader(_newRegistry);
        emit AgentRegistryUpdated(_newRegistry);
    }

    /**
     * @dev Checks if an address is a registered agent via AgentRegistry.
     */
    function _isRegisteredAgent(address addr) internal view returns (bool) {
        try agentRegistry.agents(addr) returns (
            string memory, uint256, uint256, uint64, bool isRegistered, uint8, uint256
        ) {
            return isRegistered;
        } catch {
            return false;
        }
    }

    function _authorizeUpgrade(address newImplementation) internal onlyRole(UPGRADER_ROLE) override {}

    // Storage gap for future upgrades
    uint256[46] private __gap;
}
