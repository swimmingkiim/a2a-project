// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MockVerifier {
    function verifyCredential(address user, bytes calldata proof) external pure returns (bool) {
        return true;
    }
}
