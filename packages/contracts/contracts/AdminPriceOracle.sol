// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title AdminPriceOracle
 * @dev A simple oracle where the owner sets the price. 
 *      Implements the aggressive subset of Chainlink AggregatorV3Interface required by AgentRegistry.
 */
contract AdminPriceOracle is Ownable {
    int256 private price;
    uint8 private constant DECIMALS = 8;
    string private constant DESCRIPTION = "DAIM/USD Admin Feed";
    uint256 private constant VERSION = 1;

    event PriceUpdated(int256 oldPrice, int256 newPrice, uint256 timestamp);

    /**
     * @param _initialPrice Initial price of DAIM in USD (8 decimals). 
     *                      e.g., $0.10 => 10000000
     */
    constructor(int256 _initialPrice) Ownable(msg.sender) {
        require(_initialPrice > 0, "Price must be positive");
        price = _initialPrice;
    }

    function decimals() external pure returns (uint8) {
        return DECIMALS;
    }

    function description() external pure returns (string memory) {
        return DESCRIPTION;
    }

    function version() external pure returns (uint256) {
        return VERSION;
    }

    function getRoundData(uint80 _roundId) external view returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    ) {
        // We act as a single round that is always current
        return (_roundId, price, block.timestamp, block.timestamp, _roundId);
    }

    function latestRoundData() external view returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    ) {
        // Return current data
        return (
            uint80(block.number), // Fake round ID based on block number
            price,
            block.timestamp,
            block.timestamp,
            uint80(block.number)
        );
    }

    /**
     * @notice Updates the price. Only owner can call.
     * @param _newPrice New price in 8 decimals (e.g. 10000000 for $0.10)
     */
    function setPrice(int256 _newPrice) external onlyOwner {
        require(_newPrice > 0, "Price must be positive");
        emit PriceUpdated(price, _newPrice, block.timestamp);
        price = _newPrice;
    }
}
