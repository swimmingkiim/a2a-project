// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
import "@openzeppelin/contracts/access/IAccessControl.sol";

interface IEmergencyCouncil {
    function formCouncil(uint256 randomness) external;
}

/**
 * @title DeadMansSwitch
 * @notice Automated admin rights transfer system upon inactivity.
 */
contract DeadMansSwitch is Initializable, UUPSUpgradeable, AccessControlUpgradeable {
    bytes32 public constant UPGRADER_ROLE = keccak256("UPGRADER_ROLE");

    uint256 public constant HEARTBEAT_PERIOD = 90 days;
    uint256 public lastHeartbeat;
    
    address public emergencyCouncil;
    address public humanAdmin;
    
    // Contracts to transfer admin rights for
    address[] public targetContracts;

    event HeartbeatPinged(address indexed admin, uint256 timestamp);
    event SuccessionTriggered(address indexed caller, uint256 timestamp);
    event TargetContractAdded(address indexed target);

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }

    function initialize(address _admin, address _emergencyCouncil) public initializer {
        __AccessControl_init();
        __UUPSUpgradeable_init();

        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(UPGRADER_ROLE, _admin);
        
        lastHeartbeat = block.timestamp;
        emergencyCouncil = _emergencyCouncil;
        humanAdmin = _admin;
    }

    function _authorizeUpgrade(address newImplementation) internal onlyRole(UPGRADER_ROLE) override {}

    /**
     * @notice Admin stays alive. Updates heartbeat.
     */
    function ping() external onlyRole(DEFAULT_ADMIN_ROLE) {
        lastHeartbeat = block.timestamp;
        emit HeartbeatPinged(msg.sender, lastHeartbeat);
    }

    /**
     * @notice Adds a contract where this Switch holds Admin rights and will transfer them.
     */
    function addTargetContract(address target) external onlyRole(DEFAULT_ADMIN_ROLE) {
        targetContracts.push(target);
        emit TargetContractAdded(target);
    }

    /**
     * @notice Triggers the succession if heartbeat is missing.
     * 1. Forms the Emergency Council.
     * 2. Transfers Admin rights of Target Contracts to the Council.
     * 3. Revokes Admin rights ("Iron Rule") from the previous human admin.
     * 4. Renounces its own rights (or keeps them? Better renounce to enforce full transition).
     */
    function triggerSuccession() external {
        require(block.timestamp > lastHeartbeat + HEARTBEAT_PERIOD, "Heartbeat is active");

        // 1. Form Council
        // Use prevrandao as source of randomness
        IEmergencyCouncil(emergencyCouncil).formCouncil(block.prevrandao);

        // 2. Transfer Admin Rights on Targets
        for (uint256 i = 0; i < targetContracts.length; i++) {
            IAccessControl target = IAccessControl(targetContracts[i]);
            
            // Grant to Council
            target.grantRole(0x00, emergencyCouncil); // 0x00 is DEFAULT_ADMIN_ROLE
            
            // Revoke from Human (The Dead Man)
            try target.revokeRole(0x00, humanAdmin) {
                // Success
            } catch {
                // Ignore if already revoked or failed, proceed
            }
            
            // Renounce from DeadMansSwitch (This contract)
            // Ideally we check if we still need to hold it?
            // "System transfer" implies we clear ourselves too.
            target.renounceRole(0x00, address(this)); 
        }

        emit SuccessionTriggered(msg.sender, block.timestamp);
    }

    // Storage gap
    uint256[50] private __gap;
}
