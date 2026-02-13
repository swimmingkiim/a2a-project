import { PublicClient } from 'viem';

/**
 * IFeeValidator
 * 
 * Strategy interface for validating fees in UserOperations.
 * Allows different validation logic for different token types (USDC, COMP, etc.)
 */
export interface IFeeValidator {
    /**
     * Validates that the UserOperation includes the required fee payment
     * 
     * @param userOp - The UserOperation to validate
     * @param client - Viem PublicClient for blockchain queries
     * @returns true if valid fee is included, false otherwise
     */
    validateFeeIncluded(userOp: any, client: PublicClient): Promise<boolean>;
}
