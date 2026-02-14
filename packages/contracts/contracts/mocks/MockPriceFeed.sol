// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

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

contract MockPriceFeed is AggregatorV3Interface, Ownable {
    int256 public price;
    uint8 public _decimals;

    constructor(int256 _initialPrice, uint8 __decimals) Ownable(msg.sender) {
        price = _initialPrice;
        _decimals = __decimals;
    }

    function setPrice(int256 _price) external onlyOwner {
        price = _price;
    }

    function decimals() external view override returns (uint8) {
        return _decimals;
    }

    function latestRoundData() external view override returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    ) {
        return (
            1,
            price,
            block.timestamp,
            block.timestamp,
            1
        );
    }
}
