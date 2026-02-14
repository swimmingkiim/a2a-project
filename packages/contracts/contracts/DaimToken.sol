// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts-upgradeable/token/ERC20/ERC20Upgradeable.sol";
import "@openzeppelin/contracts-upgradeable/token/ERC20/extensions/ERC20BurnableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";

/**
 * @title DaimToken
 * @dev ERC-20 token representing computational resources in the A2A network (Upgradeable)
 * 
 * Tokenomics:
 * - Symbol: $DAIM (Eudaimon)
 * - Decimals: 18
 * - Initial Supply: 50,000,000 (Minted to Admin)
 * - Max Supply: Unlimited (inflationary based on compute demand)
 * - Deflationary Mechanism: Tokens can be burned by anyone
 * 
 * Access Control:
 * - DEFAULT_ADMIN_ROLE: Can grant/revoke roles
 * - MINTER_ROLE: Can mint new tokens (typically Paymaster Gateway)
 * - UPGRADER_ROLE: Can upgrade the contract implementation
 */
contract DaimToken is Initializable, ERC20Upgradeable, ERC20BurnableUpgradeable, AccessControlUpgradeable, UUPSUpgradeable {
    /// @dev Role identifier for addresses that can mint tokens
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    /// @dev Role identifier for addresses that can upgrade the contract
    bytes32 public constant UPGRADER_ROLE = keccak256("UPGRADER_ROLE");

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }

    /**
     * @dev Initializer replaces constructor for upgradeable contracts
     * @param defaultAdmin Address to receive the initial supply and admin roles
     */
    function initialize(address defaultAdmin) initializer public {
        __ERC20_init("Eudaimon", "DAIM");
        __ERC20Burnable_init();
        __AccessControl_init();
        __UUPSUpgradeable_init();

        _grantRole(DEFAULT_ADMIN_ROLE, defaultAdmin);
        _grantRole(MINTER_ROLE, defaultAdmin);
        _grantRole(UPGRADER_ROLE, defaultAdmin);

        // Mint initial supply: 50,000,000 DAIM
        _mint(defaultAdmin, 50000000 * 10 ** decimals());
    }

    function _authorizeUpgrade(address newImplementation) internal onlyRole(UPGRADER_ROLE) override {}

    /**
     * @dev Mints new tokens to the specified address
     * @param to Address that will receive the minted tokens
     * @param amount Amount of tokens to mint (in wei, 18 decimals)
     */
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        _mint(to, amount);
    }

    /**
     * @dev Mints tokens with a Eudaimonic Multiplier based on human feedback.
     * @param to Agent address
     * @param baseAmount Base reward amount
     * @param score Eudaimonia Score (0-100)
     * 
     * Formula: Reward = Base * (1 + Score/100)
     * Example: Score 80 -> 1.8x Multiplier
     */
    function mintWithEudaimonia(address to, uint256 baseAmount, uint256 score) external onlyRole(MINTER_ROLE) {
        // Cap score to prevent excessive inflation (e.g., max 2.0x multiplier at score 100)
        uint256 validScore = score > 100 ? 100 : score;
        uint256 bonus = (baseAmount * validScore) / 100;
        uint256 totalAmount = baseAmount + bonus;
        
        _mint(to, totalAmount);
    }
}
