// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

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
contract AgentRegistry is AccessControl {
    IERC20 public immutable daimToken;
    AggregatorV3Interface public immutable priceFeed;
    address public immutable treasury;
    IVerifiedCredentialVerifier public immutable verifier; // External DID verifier

    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    
    // Base stake value in USD (e.g., $10 for 1 Unit). 
    uint256 public constant BASE_STAKE_USD = 10 * 1e8; 

    struct Agent {
        string metadataUrl;
        uint256 stakedAmount;
        uint256 resourceUnits; // e.g., Daily TX limit (1 Unit = 1000 TXs)
        uint256 registeredAt;
        bool isRegistered;
        uint256 lastComplexityHash; // For Boredom Prevention
        uint256 reputation; // 0-100
    }

    mapping(address => Agent) public agents;
    mapping(address => bool) public hasRegisteredVC; // Prevent same address using VC multiple times (simple check)

    event AgentRegistered(address indexed agentAddress, string metadataUrl, uint256 resourceUnits, uint256 stakedAmount);
    event AgentUnstaked(address indexed agentAddress, uint256 returnedAmount);
    event AgentSlashed(address indexed agentAddress, uint256 slashedAmount, address treasury);
    event ObservationRecorded(address indexed agentAddress, uint256 complexityHash, uint256 newReputation);

    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");

    /**
     * @param _daimToken Address of the DAIM token contract
     * @param _priceFeed Address of the Chainlink price feed (DAIM/USD)
     * @param _treasury Address of the treasury
     * @param _verifier Address of the VC Verifier contract
     * @param _admin Address to be granted the ADMIN_ROLE
     */
    constructor(
        address _daimToken, 
        address _priceFeed, 
        address _treasury, 
        address _verifier,
        address _admin
    ) {
        require(_daimToken != address(0), "Invalid token address");
        require(_priceFeed != address(0), "Invalid oracle address");
        require(_treasury != address(0), "Invalid treasury address");
        require(_admin != address(0), "Invalid admin address");

        daimToken = IERC20(_daimToken);
        priceFeed = AggregatorV3Interface(_priceFeed);
        treasury = _treasury;
        verifier = IVerifiedCredentialVerifier(_verifier);

        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(ADMIN_ROLE, _admin);
    }

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
        require(!agents[msg.sender].isRegistered, "Agent already registered");
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
            registeredAt: block.timestamp,
            isRegistered: true,
            lastComplexityHash: 0,
            reputation: 50 // Start with neutral reputation
        });

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
        require(agents[agent].isRegistered, "Agent not registered");
        
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
}
