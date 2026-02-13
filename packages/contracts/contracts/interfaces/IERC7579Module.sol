// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IERC7579Module
 * @notice Simplified interface for ERC-7579 Modules (Validators/Executors/Hooks).
 * @dev Full spec: https://erc7579.com/
 */
interface IERC7579Module {
    /**
     * @notice Checks if the module is of a specific type.
     * @param typeID The module type ID (1=Validator, 2=Executor, 3=Fallback, 4=Hook).
     * @return true if the module is of the given type.
     */
    function isModuleType(uint256 typeID) external view returns (bool);

    /**
     * @notice Initializes the module with data.
     * @param data Initialization data.
     */
    function onInstall(bytes calldata data) external;

    /**
     * @notice De-initializes the module.
     * @param data De-initialization data.
     */
    function onUninstall(bytes calldata data) external;
}

/**
 * @title IValidator
 * @notice Interface for a Validator module (Type 1).
 */
interface IValidator is IERC7579Module {
    /**
     * @notice Validates a UserOperation.
     * @param userOp The UserOperation struct (packed).
     * @param userOpHash The hash of the UserOperation.
     * @return validationData Packed validation data (authorizer + validUntil + validAfter).
     */
    function validateUserOp(
        bytes32 userOpHash,
        bytes calldata userOp
    ) external returns (uint256 validationData);

    /**
     * @notice Validates a signature for a message.
     * @param hash The hash of the message.
     * @param signature The signature to validate.
     * @return magicValue EIP-1271 magic value if valid.
     */
    function isValidSignatureWithSender(
        address sender,
        bytes32 hash,
        bytes calldata signature
    ) external view returns (bytes4 magicValue);
}

/**
 * @title IHook
 * @notice Interface for a Hook module (Type 4).
 */
interface IHook is IERC7579Module {
    /**
     * @notice Called before execution.
     * @param msgSender The sender of the execution.
     * @param value The value sent.
     * @param func The function selector + data.
     * @return hookData Data to pass to postCheck.
     */
    function preCheck(
        address msgSender,
        uint256 value,
        bytes calldata func
    ) external returns (bytes memory hookData);

    /**
     * @notice Called after execution.
     * @param hookData Data returned from preCheck.
     */
    function postCheck(bytes calldata hookData) external;
}
