// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "../contracts/AgentRegistry.sol";

contract MockV3Aggregator is AggregatorV3Interface {
    int256 public price;
    uint8 public _decimals;

    constructor(uint8 decimals_, int256 initialPrice) {
        _decimals = decimals_;
        price = initialPrice;
    }

    function updatePrice(int256 newPrice) external {
        price = newPrice;
    }

    function decimals() external view returns (uint8) {
        return _decimals;
    }
    
    function latestRoundData() external view returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    ) {
        return (0, price, 0, 0, 0);
    }

    function description() external pure returns (string memory) {
        return "Mock Aggregator";
    }

    function version() external pure returns (uint256) {
        return 1;
    }

    function getRoundData(uint80) external pure returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    ) {
        return (0, 0, 0, 0, 0);
    }
}

contract MockVerifier is IVerifiedCredentialVerifier {
    bool public shouldPass;

    constructor() {
        shouldPass = true;
    }

    function setShouldPass(bool _shouldPass) external {
        shouldPass = _shouldPass;
    }

    function verifyCredential(address, bytes calldata) external view returns (bool) {
        return shouldPass;
    }
}
