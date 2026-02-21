// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/utils/ReentrancyGuardUpgradeable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

interface IDaimToken {
    function mintWithEudaimonia(address to, uint256 baseAmount, uint256 score) external;
}

interface IAgentRegistry {
    function recordObservation(address agent, uint256 complexityHash) external;
}

interface IOracleRegistry {
    function recordOracleEvaluation(address oracle, bool isValidEvaluation) external;
}

/**
 * @title QuantumTaskBuffer
 * @dev Implements "Schrodinger's Pool" Logic for the A2A Economy.
 *      - Pending Task Buffer
 *      - Thermodynamic Throttling (Heat)
 *      - Eudaimonic Collapse (Oracle Verification)
 *      - Spam Filtering (Deposit & Slashing)
 */
contract QuantumTaskBuffer is Initializable, UUPSUpgradeable, AccessControlUpgradeable, ReentrancyGuardUpgradeable {
    using SafeERC20 for IERC20;

    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant UPGRADER_ROLE = keccak256("UPGRADER_ROLE");
    
    IERC20 public daimToken; // Removed immutable
    IDaimToken public minterToken; // Same token, just explicitly casting for mint interface
    IAgentRegistry public registry; // Removed immutable
    address public treasury; // Removed immutable

    IOracleRegistry public oracleRegistry; // Reference to OracleRegistry
    uint256 public constant ORACLE_FEE_RATE = 15; // 15% of base deposit

    // --- State Variables ---
    
    struct Task {
        uint256 id;
        address creator;
        uint256 deposit;
        uint256 complexityHash;
        uint256 submissionTime;
        uint256 assessedComplexity;
        uint256 eudaimoniaScore;
        bool exists;
    }

    mapping(uint256 => Task) public tasks;
    uint256 public nextTaskId;
    uint256 public pendingTaskCount; // HEAT Metric

    // Configuration
    uint256 public constant CRITICAL_MASS = 100; // Overheat threshold
    uint256 public constant DECAY_PERIOD = 3 days; // Time until a task becomes stale
    uint256 public baseDeposit; // Assigned in initialize
    uint256 public baseReward; // Assigned in initialize

    // Events
    event TaskSubmitted(uint256 indexed taskId, address indexed creator, uint256 deposit, bool overheated, string metadataUri);
    event TaskFinalized(uint256 indexed taskId, address indexed creator, uint256 assessedComplexity, uint256 eudaimoniaScore, uint256 reward, bool slashed);
    event TaskSlashed(uint256 indexed taskId, address indexed creator, string reason);
    event StaleTaskPruned(uint256 indexed taskId);

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }

    function initialize(
        address _daimToken, 
        address _registry,
        address _treasury,
        address _admin
    ) initializer public {
        __AccessControl_init();
        __UUPSUpgradeable_init();
        __ReentrancyGuard_init();

        require(_daimToken != address(0), "Invalid token");
        require(_registry != address(0), "Invalid registry");
        require(_treasury != address(0), "Invalid treasury");

        daimToken = IERC20(_daimToken);
        minterToken = IDaimToken(_daimToken);
        registry = IAgentRegistry(_registry);
        treasury = _treasury;

        // Note: OracleRegistry must be set via setter after deployment


        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(ORACLE_ROLE, _registry); // Allow registry to call finalizeTask
        _grantRole(UPGRADER_ROLE, _admin);

        // Initialize State Variables
        baseDeposit = 10 * 1e18; // 10 DAIM
        baseReward = 50 * 1e18; // 50 DAIM
    }

    function _authorizeUpgrade(address newImplementation) internal onlyRole(UPGRADER_ROLE) override {}

    /**
     * @notice Checks if the system is Overheated (Thermodynamic Throttling).
     */
    function isOverheated() public view returns (bool) {
        return pendingTaskCount > CRITICAL_MASS;
    }

    /**
     * @notice Admin function to update base reward.
     */
    function setBaseReward(uint256 _newReward) external onlyRole(DEFAULT_ADMIN_ROLE) {
        baseReward = _newReward;
    }

    /**
     * @notice Admin function to set OracleRegistry address.
     */
    function setOracleRegistry(address _oracleRegistry) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_oracleRegistry != address(0), "Invalid oracle registry");
        oracleRegistry = IOracleRegistry(_oracleRegistry);
    }

    /**
     * @notice Agents submit tasks to the Schrödinger Pool.
     * @dev Decoupled Verification: Complexity is checked LATER.
     *      Requires Deposit (Spam Filter).
     * @param _complexityHash Input identifier
     * @param _metadataUri IPFS URI containing JSON metadata of the task content
     */
    function submitTask(uint256 _complexityHash, string calldata _metadataUri) external nonReentrant {
        uint256 requiredDeposit = baseDeposit;
        bool overheated = isOverheated();

        // Thermodynamic Throttling: Double fee if overheated
        if (overheated) {
            requiredDeposit *= 2;
        }

        // Transfer Deposit
        daimToken.safeTransferFrom(msg.sender, address(this), requiredDeposit);

        // Add to Pool
        tasks[nextTaskId] = Task({
            id: nextTaskId,
            creator: msg.sender,
            deposit: requiredDeposit,
            complexityHash: _complexityHash,
            submissionTime: block.timestamp,
            assessedComplexity: 0,
            eudaimoniaScore: 0,
            exists: true
        });

        emit TaskSubmitted(nextTaskId, msg.sender, requiredDeposit, overheated, _metadataUri);

        nextTaskId++;
        pendingTaskCount++;
    }

    /**
     * @notice Human Oracle observes and collapses the Wave Function.
     * @dev Calculates Eudaimonia, mints rewards, or Slashes spam.
     * @param _taskId ID of the task
     * @param _assessedComplexity 0-100 score of complexity (Spam check)
     * @param _eudaimoniaScore 0-100 score of value/utility
     */
    function finalizeTask(
        uint256 _taskId, 
        uint256 _assessedComplexity, 
        uint256 _eudaimoniaScore
    ) external nonReentrant {
        Task memory task = tasks[_taskId];
        require(task.exists, "Task does not exist");

        // Calculate Oracle Fee (15% of deposit)
        uint256 oracleFee = (task.deposit * ORACLE_FEE_RATE) / 100;
        uint256 remainingDeposit = task.deposit - oracleFee;

        // Always pay the Oracle for their labor
        daimToken.safeTransfer(msg.sender, oracleFee);

        // 1. Spam Check / Slashing
        if (_assessedComplexity < 20) { // < 0.2 in simulation
            // Slashing: Remaining deposit goes to Treasury
            daimToken.safeTransfer(treasury, remainingDeposit);
            
            // Record Oracle Evaluation (In MVP, oracle is considered 'valid' if they evaluated successfully)
            if (address(oracleRegistry) != address(0)) {
                oracleRegistry.recordOracleEvaluation(msg.sender, true); 
            }
            
            emit TaskSlashed(_taskId, task.creator, "Low Complexity (Spam)");
        } else {
            // 2. Success: Return Remaining Deposit to Creator
            daimToken.safeTransfer(task.creator, remainingDeposit);

            // 3. Mint Reward with Eudaimonia Multiplier
            // use baseReward state variable instead of hardcoded value
            uint256 rewardAmount = baseReward; 
            minterToken.mintWithEudaimonia(task.creator, rewardAmount, _eudaimoniaScore);
            
            // 4. Update Registry (Reputation)
            registry.recordObservation(task.creator, task.complexityHash);
            
            // Record Oracle Evaluation
            if (address(oracleRegistry) != address(0)) {
                oracleRegistry.recordOracleEvaluation(msg.sender, true); 
            }

            emit TaskFinalized(_taskId, task.creator, _assessedComplexity, _eudaimoniaScore, rewardAmount, false);
        }

        // Cleanup
        delete tasks[_taskId];
        if (pendingTaskCount > 0) pendingTaskCount--;
    }

    /**
     * @notice Passive Garbage Collection for Stale Tasks.
     * @param _taskIds Array of task IDs to check and prune.
     */
    function pruneStaleTasks(uint256[] calldata _taskIds) external nonReentrant {
        for (uint256 i = 0; i < _taskIds.length; i++) {
            uint256 id = _taskIds[i];
            Task memory task = tasks[id];
            
            if (task.exists && block.timestamp > (task.submissionTime + DECAY_PERIOD)) {
                // Prune: 
                // Keeper Incentive: 10% of deposit to msg.sender
                uint256 keeperReward = (task.deposit * 10) / 100;
                uint256 refundAmount = task.deposit - keeperReward;

                if (keeperReward > 0) {
                    daimToken.safeTransfer(msg.sender, keeperReward);
                }
                
                if (refundAmount > 0) {
                     daimToken.safeTransfer(task.creator, refundAmount);
                }

                emit StaleTaskPruned(id);
                
                delete tasks[id];
                if (pendingTaskCount > 0) pendingTaskCount--;
            }
        }
    }

    function setBaseDeposit(uint256 _newDeposit) external onlyRole(DEFAULT_ADMIN_ROLE) {
        baseDeposit = _newDeposit;
    }
}
