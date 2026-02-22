import { describe, it, expect } from 'vitest';
import { handleChainError } from '../src/a2a-errors.js';

describe('Error Handling Middleware', () => {
    it('should translate network errors to Korean', () => {
        const error = new Error('Some network failure occurred');
        const result = handleChainError(error);
        expect(result).toBe('Base Mainnet RPC 연결 실패. 잠시 후 재시도하세요.');
    });

    it('should translate invalid address errors to Korean', () => {
        const error = new Error('invalid address passed to contract');
        const result = handleChainError(error);
        expect(result).toBe('유효하지 않은 지갑 주소입니다. 0x로 시작하는 42자리 주소를 입력하세요.');
    });

    it('should return default error format for unknown errors', () => {
        const error = new Error('reverted with reason: insufficient balance');
        const result = handleChainError(error);
        expect(result).toBe('조회 실패: reverted with reason: insufficient balance');
    });

    it('should handle non-Error objects safely', () => {
        const result = handleChainError('string error');
        expect(result).toBe('조회 실패: string error');
    });
});
