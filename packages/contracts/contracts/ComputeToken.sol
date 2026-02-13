// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title ComputeToken
 * @dev ERC-20 token representing computational resources in the A2A network
 * 
 * Tokenomics:
 * - Symbol: $COMP
 * - Decimals: 18
 * - Initial Supply: 0 (minted on-demand)
 * - Max Supply: Unlimited (inflationary based on compute demand)
 * - Deflationary Mechanism: Tokens can be burned by anyone
 * 
 * Access Control:
 * - DEFAULT_ADMIN_ROLE: Can grant/revoke roles
 * - MINTER_ROLE: Can mint new tokens (typically Paymaster Gateway)
 * 
 * Economic Model (BME - Burn-and-Mint Equilibrium):
 * - Network usage burns $COMP (demand-driven deflation)
 * - Compute work mints $COMP (supply-driven inflation)
 * - If burn > mint → Net deflation → Price appreciates
 *
 * @author A2A Project
 */
contract ComputeToken is ERC20, ERC20Burnable, AccessControl {
    /// @dev Role identifier for addresses that can mint tokens
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    /**
     * @dev Constructor sets up the token and grants initial roles
     * @param name Token Name (e.g. "Compute Token")
     * @param symbol Token Symbol (e.g. "COMP")
     * @param paymasterGateway Address of the Paymaster Gateway that will mint tokens
     */
    constructor(string memory name, string memory symbol, address paymasterGateway) ERC20(name, symbol) {
        require(paymasterGateway != address(0), "ComputeToken: paymaster is zero address");

        // Grant admin role to deployer
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);

        // Grant minter role to Paymaster Gateway
        _grantRole(MINTER_ROLE, paymasterGateway);
    }

    /**
     * @dev Mints new tokens to the specified address
     * @param to Address that will receive the minted tokens
     * @param amount Amount of tokens to mint (in wei, 18 decimals)
     * 
     * Requirements:
     * - Caller must have MINTER_ROLE
     * - `to` cannot be the zero address
     */
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        _mint(to, amount);
    }

    /**
     * @dev Burns tokens from the caller's account
     * Inherited from ERC20Burnable, overridden for documentation
     * @param amount Amount of tokens to burn
     * 
     * This function drives the deflationary mechanism of the BME model.
     * Network usage fees are burned, reducing total supply.
     */
    function burn(uint256 amount) public override {
        super.burn(amount);
    }

    /**
     * @dev Burns tokens from a specified account using allowance
     * Inherited from ERC20Burnable, overridden for documentation
     * @param account Account to burn tokens from
     * @param amount Amount of tokens to burn
     * 
     * Requirements:
     * - Caller must have sufficient allowance
     */
    function burnFrom(address account, uint256 amount) public override {
        super.burnFrom(account, amount);
    }

    /**
     * @dev See {IERC165-supportsInterface}
     * Required override for multiple inheritance
     */
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
