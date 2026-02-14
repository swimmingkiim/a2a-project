// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MockVerifier {
    bool public shouldPass = true;

    function setShouldPass(bool _shouldPass) external {
        shouldPass = _shouldPass;
    }

    function verifyCredential(address user, bytes calldata proof) external view returns (bool) {
        return shouldPass;
    }
}
