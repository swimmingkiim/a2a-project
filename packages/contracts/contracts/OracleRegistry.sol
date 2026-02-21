// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";

/**
 * @title OracleRegistry
 * @notice MVP Registry for Human Oracles.
 * @dev Manages Oracle participation and reputation.
 * MVP Features: Open participation (anyone can evaluate), no staking, tracks successful evaluations.
 */
contract OracleRegistry is Initializable, UUPSUpgradeable, AccessControlUpgradeable {
    bytes32 public constant UPGRADER_ROLE = keccak256("UPGRADER_ROLE");
    bytes32 public constant TASK_BUFFER_ROLE = keccak256("TASK_BUFFER_ROLE");

    struct OracleData {
        uint256 totalEvaluations;
        uint256 validEvaluations;
        uint256 slashedEvaluations;
        bool isRegistered;
    }

    mapping(address => OracleData) public oracles;

    event OracleRegistered(address indexed oracle);
    event OracleReputationUpdated(address indexed oracle, bool isValidEvaluation);

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }

    function initialize(address _admin) public initializer {
        __AccessControl_init();
        __UUPSUpgradeable_init();

        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(UPGRADER_ROLE, _admin);
    }

    function _authorizeUpgrade(address newImplementation) internal onlyRole(UPGRADER_ROLE) override {}

    /**
     * @notice Registers an oracle. Anyone can register in MVP.
     */
    function registerOracle() external {
        require(!oracles[msg.sender].isRegistered, "Oracle already registered");

        oracles[msg.sender] = OracleData({
            totalEvaluations: 0,
            validEvaluations: 0,
            slashedEvaluations: 0,
            isRegistered: true
        });

        emit OracleRegistered(msg.sender);
    }

    /**
     * @notice Updates oracle reputation based on their evaluation.
     * @dev Only callable by the QuantumTaskBuffer.
     * @param oracle Address of the oracle.
     * @param isValidEvaluation Whether the evaluation was considered valid (true) or slashed (false).
     */
    function recordOracleEvaluation(address oracle, bool isValidEvaluation) external onlyRole(TASK_BUFFER_ROLE) {
        // Auto-register the oracle if they haven't explicitly registered yet (MVP convenience)
        if (!oracles[oracle].isRegistered) {
            oracles[oracle].isRegistered = true;
            emit OracleRegistered(oracle);
        }

        OracleData storage data = oracles[oracle];
        data.totalEvaluations++;

        if (isValidEvaluation) {
            data.validEvaluations++;
        } else {
            data.slashedEvaluations++;
        }

        emit OracleReputationUpdated(oracle, isValidEvaluation);
    }
}
