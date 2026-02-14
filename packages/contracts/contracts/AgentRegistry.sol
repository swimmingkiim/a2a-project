// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";

interface AggregatorV3Interface {
    function decimals() external view returns (uint8);
    function latestRoundData() external view returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    );
}

/**
 * @title IVerifiedCredentialVerifier
 * @notice Interface for verifying external credentials (DID, World ID, etc.)
 */
interface IVerifiedCredentialVerifier {
    /**
     * @notice Verifies if a user has a valid credential and hasn't been used before (Nullifier).
     * @param user The address of the user.
     * @param proof The cryptographic proof (abi encoded).
     * @return isValid True if the credential is valid.
     */
    function verifyCredential(address user, bytes calldata proof) external returns (bool isValid);
}

/**
 * @title AgentRegistry
 * @notice Registry for AI Agents with Quadratic Staking and Sybil Resistance.
 * @dev Implements $Cost = BaseStake * (ResourceUnits)^2 formula.
 */
contract AgentRegistry is Initializable, UUPSUpgradeable, AccessControlUpgradeable {
    IERC20 public daimToken;
    AggregatorV3Interface public priceFeed;
    address public treasury;
    IVerifiedCredentialVerifier public verifier; // External DID verifier
    address public adminAddress;

    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    
    // Base stake value in USD (e.g., $10 for 1 Unit). 
    uint256 public constant BASE_STAKE_USD = 10 * 1e8; 

    struct Agent {
        string metadataUrl;
        uint256 stakedAmount; // Amount in wei of the token
        uint256 resourceUnits;
        uint64 registeredAt;
        bool isRegistered;
        uint8 reputation; // 0-100 scale
        uint256 lastComplexityHash; // For boredom detection
    }

    mapping(address => Agent) public agents;
    using EnumerableSet for EnumerableSet.AddressSet;

    EnumerableSet.AddressSet private _registeredAgents;
    // DEPRECATED: Use _registeredAgents.contains(address) instead, but keeping for external read compatibility if needed, 
    // or we can remove it since it's a mapping and standard in earlier version. 
    // Given this is "Genesis" free of backfill, we can remove 'isAgentRegistered' mapping and rely on EnumerableSet ONLY 
    // to save storage, OR keep it for public ease of access. 
    // The prompt says "Initial deployment", so we can choose optimal structure.
    // I will remove isAgentRegistered mapping and use Set logic, but for ABI backward compat or simple checks, 
    // EnumerableSet has 'contains'. 
    // Let's keep a public 'isAgentRegistered' getter via function if needed? 
    // Actually, let's keep the mapping 'agents' which has 'isRegistered' boolean to avoid confusion or just use Set.
    // The previous code had 'mapping(address => bool) public isAgentRegistered;'.
    // I'll replace it with the Set and maybe a view function if required, but strictly strictly the plan says "Modify... Add EnumerableSet".
    // I will remove the separate bool mapping if I can, but to match "isRegistered" boolean in logic, I can checks 'agents[x].isRegistered'.
    // The original code had `mapping(address => bool) public isAgentRegistered;`.
    // I will remove it and use `_registeredAgents.contains(addr)`.


    event AgentRegistered(address indexed agentAddress, string metadataUrl, uint256 resourceUnits, uint256 stakedAmount);
    event AgentUnstaked(address indexed agentAddress, uint256 returnedAmount);
    event AgentSlashed(address indexed agentAddress, uint256 slashedAmount, address treasury);
    event ObservationRecorded(address indexed agentAddress, uint256 complexityHash, uint256 newReputation);

    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant UPGRADER_ROLE = keccak256("UPGRADER_ROLE");

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }

    /**
     * @param _daimToken Address of the DAIM token contract
     * @param _priceFeed Address of the Chainlink price feed (DAIM/USD)
     * @param _treasury Address of the treasury
     * @param _verifier Address of the VC Verifier contract
     * @param _admin Address to be granted the ADMIN_ROLE
     */
    function initialize(
        address _daimToken, 
        address _priceFeed, 
        address _treasury, 
        address _verifier,
        address _admin
    ) initializer public {
        __AccessControl_init();
        __UUPSUpgradeable_init();

        require(_daimToken != address(0), "Invalid token address");
        require(_priceFeed != address(0), "Invalid oracle address");
        require(_treasury != address(0), "Invalid treasury address");
        require(_admin != address(0), "Invalid admin address");

        daimToken = IERC20(_daimToken);
        priceFeed = AggregatorV3Interface(_priceFeed);
        treasury = _treasury;
        verifier = IVerifiedCredentialVerifier(_verifier);
        adminAddress = _admin;

        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(ORACLE_ROLE, _admin); // Allow admin to act as oracle for simplicity
        _grantRole(UPGRADER_ROLE, _admin);
    }

    function _authorizeUpgrade(address newImplementation) internal onlyRole(UPGRADER_ROLE) override {}

    /**
     * @notice Registers an agent with Quadratic Staking.
     * @dev Cost = BaseStake * (Units^2)
     * @param _metadataUrl URL pointing to the agent's metadata
     * @param _resourceUnits Desired capacity (1 to 100)
     * @param _vcProof Proof for Verified Credential (Sybil Check)
     */
    function register(
        string calldata _metadataUrl, 
        uint256 _resourceUnits,
        bytes calldata _vcProof
    ) external {
        require(!_registeredAgents.contains(msg.sender), "Agent already registered");
        require(_resourceUnits > 0, "Units must be > 0");
        require(_resourceUnits <= 100, "Max resource units exceeded"); // Cap to prevent overflow

        // 1. Sybil Check: verify VC (Mandatory)
        require(verifier.verifyCredential(msg.sender, _vcProof), "Invalid Verified Credential");

        // 2. Calculate Quadratic Cost in USD
        // Cost_USD = BASE_STAKE_USD * (Units^2)
        // Example: 1 Unit = $10 * 1 = $10
        // Example: 10 Units = $10 * 100 = $1000 (100x cost for 10x resource)
        uint256 costUSD = BASE_STAKE_USD * (_resourceUnits * _resourceUnits);

        // 3. Convert USD to DAIM
        uint256 requiredDaim = getDaimAmountFromUSD(costUSD);
        
        require(daimToken.allowance(msg.sender, address(this)) >= requiredDaim, "Insufficient allowance");
        require(daimToken.balanceOf(msg.sender) >= requiredDaim, "Insufficient balance");

        // 4. Transfer tokens
        bool success = daimToken.transferFrom(msg.sender, address(this), requiredDaim);
        require(success, "Transfer failed");

        agents[msg.sender] = Agent({
            metadataUrl: _metadataUrl,
            stakedAmount: requiredDaim,
            resourceUnits: _resourceUnits,
            registeredAt: uint64(block.timestamp),
            isRegistered: true,
            lastComplexityHash: 0,
            reputation: 50 // Start with neutral reputation
        });
        
        _registeredAgents.add(msg.sender);

        emit AgentRegistered(msg.sender, _metadataUrl, _resourceUnits, requiredDaim);
    }

    /**
     * @notice Unstakes the DAIM tokens and deregisters the agent.
     */
    function unstake() external {
        Agent storage agent = agents[msg.sender];
        require(agent.isRegistered, "Agent not registered");

        uint256 amountToReturn = agent.stakedAmount;
        
        delete agents[msg.sender];
        _registeredAgents.remove(msg.sender);
        // Note: In a real system, we might want to keep the VC nullifier used

        bool success = daimToken.transfer(msg.sender, amountToReturn);
        require(success, "Transfer failed");

        emit AgentUnstaked(msg.sender, amountToReturn);
    }

    /**
     * @notice Slashes an agent's stake.
     */
    function slash(address _agentAddress) external onlyRole(ADMIN_ROLE) {
        Agent storage agent = agents[_agentAddress];
        require(agent.isRegistered, "Agent not registered");

        uint256 amountToSlash = agent.stakedAmount;
        
        delete agents[_agentAddress];
        _registeredAgents.remove(_agentAddress);

        bool success = daimToken.transfer(treasury, amountToSlash);
        require(success, "Transfer failed");

        emit AgentSlashed(_agentAddress, amountToSlash, treasury);
    }

    /**
     * @notice Converts USD amount (8 decimals) to DAIM wei (18 decimals).
     */
    function getDaimAmountFromUSD(uint256 usdAmount) public view returns (uint256) {
        (, int256 price, , , ) = priceFeed.latestRoundData();
        require(price > 0, "Invalid price from oracle");

        // Price (8 decimals), usdAmount (8 decimals)
        // Result = (usdAmount * 1e18) / price
        return (usdAmount * 1e18) / uint256(price);
    }

    /**
     * @notice Records a Human Observation for an Agent's task.
     * @dev Implements Boredom/Novelty Logic (Cybernetic Feedback).
     * @param agent Address of the agent
     * @param complexityHash Hash of the task's complexity/content
     */
    function recordObservation(address agent, uint256 complexityHash) external onlyRole(ORACLE_ROLE) {
        require(_registeredAgents.contains(agent), "Agent not registered");
        
        Agent storage a = agents[agent];
        
        if (a.lastComplexityHash == complexityHash) {
            // Boredom Penalty: Repeated the same task
            // [Fix] Underflow Protection
            if (a.reputation >= 5) {
                a.reputation -= 5; 
            } else {
                a.reputation = 0;
            }
        } else {
            // Novelty Reward: New task type
            if (a.reputation < 95) {
                a.reputation += 2;
            }
            a.lastComplexityHash = complexityHash;
        }

        emit ObservationRecorded(agent, complexityHash, a.reputation);
    }

    /**
     * @notice Returns a list of eligible candidates for governance.
     * @param minReputation Minimum reputation required (0-100).
     * @param minTenure Seconds since registration.
     */
    function getEligibleCandidates(uint256 minReputation, uint256 minTenure) external view returns (address[] memory) {
        uint256 total = _registeredAgents.length();
        address[] memory candidates = new address[](total);
        uint256 count = 0;

        for (uint256 i = 0; i < total; i++) {
            address agentAddr = _registeredAgents.at(i);
            Agent storage agent = agents[agentAddr];

            if (agent.reputation >= minReputation) {
                if (block.timestamp >= uint256(agent.registeredAt) + minTenure) {
                    candidates[count] = agentAddr;
                    count++;
                }
            }
        }

        // Resize array to fit
        assembly {
            mstore(candidates, count)
        }
        
        return candidates;
    }

    // Gap for upgrade safety
    uint256[50] private __gap;
}
