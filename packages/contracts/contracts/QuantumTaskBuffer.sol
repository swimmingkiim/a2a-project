// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

interface IComputeToken {
    function mintWithEudaimonia(address to, uint256 baseAmount, uint256 score) external;
}

interface IAgentRegistry {
    function recordObservation(address agent, uint256 complexityHash) external;
}

/**
 * @title QuantumTaskBuffer
 * @dev Implements "Schrodinger's Pool" Logic for the A2A Economy.
 *      - Pending Task Buffer
 *      - Thermodynamic Throttling (Heat)
 *      - Eudaimonic Collapse (Oracle Verification)
 *      - Spam Filtering (Deposit & Slashing)
 */
contract QuantumTaskBuffer is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    
    IERC20 public immutable compToken;
    IComputeToken public immutable minterToken; // Same token, just explicitly casting for mint interface
    IAgentRegistry public immutable registry;
    address public immutable treasury;

    // --- State Variables ---
    
    struct Task {
        address creator;
        uint256 deposit;
        uint256 timestamp;
        uint256 complexityHash; // Hash of the task content/params
        bool exists;
    }

    mapping(uint256 => Task) public tasks;
    uint256 public nextTaskId;
    uint256 public pendingTaskCount; // HEAT Metric

    // Configuration
    uint256 public constant CRITICAL_MASS = 100; // Overheat threshold
    uint256 public constant DECAY_PERIOD = 3 days; // Time until a task becomes stale
    uint256 public baseDeposit = 10 * 1e18; // 10 COMP

    // Events
    event TaskSubmitted(uint256 indexed taskId, address indexed creator, uint256 deposit, bool overheated);
    event TaskFinalized(uint256 indexed taskId, uint256 eudaimoniaScore, uint256 reward);
    event TaskSlashed(uint256 indexed taskId, address indexed creator, string reason);
    event StaleTaskPruned(uint256 indexed taskId);

    constructor(
        address _compToken,
        address _registry,
        address _treasury,
        address _admin
    ) {
        require(_compToken != address(0), "Invalid token");
        require(_registry != address(0), "Invalid registry");
        require(_treasury != address(0), "Invalid treasury");

        compToken = IERC20(_compToken);
        minterToken = IComputeToken(_compToken);
        registry = IAgentRegistry(_registry);
        treasury = _treasury;

        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(ORACLE_ROLE, _admin); // Admin is initial Oracle
    }

    /**
     * @notice Checks if the system is Overheated (Thermodynamic Throttling).
     */
    function isOverheated() public view returns (bool) {
        return pendingTaskCount > CRITICAL_MASS;
    }

    /**
     * @notice Agents submit tasks to the Schrödinger Pool.
     * @dev Decoupled Verification: Complexity is checked LATER.
     *      Requires Deposit (Spam Filter).
     */
    function submitTask(uint256 _complexityHash) external nonReentrant {
        uint256 requiredDeposit = baseDeposit;
        bool overheated = isOverheated();

        // Thermodynamic Throttling: Double fee if overheated
        if (overheated) {
            requiredDeposit *= 2;
        }

        // Transfer Deposit
        compToken.safeTransferFrom(msg.sender, address(this), requiredDeposit);

        // Add to Pool
        tasks[nextTaskId] = Task({
            creator: msg.sender,
            deposit: requiredDeposit,
            timestamp: block.timestamp,
            complexityHash: _complexityHash,
            exists: true
        });

        emit TaskSubmitted(nextTaskId, msg.sender, requiredDeposit, overheated);

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
    ) external onlyRole(ORACLE_ROLE) nonReentrant {
        Task memory task = tasks[_taskId];
        require(task.exists, "Task does not exist");

        // 1. Spam Check / Slashing
        if (_assessedComplexity < 20) { // < 0.2 in simulation
            // Slashing: Deposit goes to Treasury
            compToken.safeTransfer(treasury, task.deposit);
            emit TaskSlashed(_taskId, task.creator, "Low Complexity (Spam)");
        } else {
            // 2. Success: Return Deposit
            compToken.safeTransfer(task.creator, task.deposit);

            // 3. Mint Reward with Eudaimonia Multiplier
            // Base Reward matches deposit for simplicity in this model, or could be dynamic.
            uint256 baseReward = 50 * 1e18; 
            minterToken.mintWithEudaimonia(task.creator, baseReward, _eudaimoniaScore);

            // 4. Update Agent Memory (Boredom Check)
            registry.recordObservation(task.creator, task.complexityHash);
            
            emit TaskFinalized(_taskId, _eudaimoniaScore, baseReward);
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
            
            if (task.exists && block.timestamp > (task.timestamp + DECAY_PERIOD)) {
                // Prune: Deposit is burned (or sent to treasury) to punish staleness?
                // Or returned? Let's say returned to be nice, but task is cancelled.
                // In a strict system, maybe slashed. Let's return for now.
                compToken.safeTransfer(task.creator, task.deposit);
                
                delete tasks[id];
                if (pendingTaskCount > 0) pendingTaskCount--;
                
                emit StaleTaskPruned(id);
            }
        }
    }

    function setBaseDeposit(uint256 _newDeposit) external onlyRole(DEFAULT_ADMIN_ROLE) {
        baseDeposit = _newDeposit;
    }
}
