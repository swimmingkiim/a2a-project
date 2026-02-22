import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as contracts from '../src/a2a-contracts.js';
import { handleChainError } from '../src/a2a-errors.js';
import {
    a2a_protocol_info,
    a2a_check_system_status,
    a2a_get_balance,
    a2a_check_task,
    a2a_list_pending_tasks
} from '../src/a2a-tools.js';

vi.mock('../src/a2a-contracts.js', () => ({
    isOverheated: vi.fn(),
    getBaseDeposit: vi.fn(),
    getDaimBalance: vi.fn(),
    isAgentRegistered: vi.fn(),
    getPendingTaskCount: vi.fn(),
    getNextTaskId: vi.fn(),
    getTask: vi.fn(),
}));

describe('A2A Tools Handlers', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('a2a_protocol_info should return protocol details', async () => {
        const result = await a2a_protocol_info();
        expect(result.content[0].text).toContain('A2A Protocol');
        expect(result.content[0].text).toContain('DAIM');
    });

    it('a2a_check_system_status should return formatted status', async () => {
        vi.mocked(contracts.getPendingTaskCount).mockResolvedValue(5n);
        vi.mocked(contracts.getBaseDeposit).mockResolvedValue(100n);
        vi.mocked(contracts.isOverheated).mockResolvedValue(false);

        const result = await a2a_check_system_status();
        expect(result.content[0].text).toContain('대기 중인 태스크: 5');
        expect(result.content[0].text).toContain('과열 상태: 안정 (정상 작동 중)');
    });

    it('a2a_check_system_status should handle errors with handleChainError', async () => {
        vi.mocked(contracts.isOverheated).mockRejectedValue(new Error('network error'));
        const result = await a2a_check_system_status();
        expect(result.content[0].text).toBe('Base Mainnet RPC 연결 실패. 잠시 후 재시도하세요.');
    });

    it('a2a_get_balance should return formatted balance', async () => {
        vi.mocked(contracts.getDaimBalance).mockResolvedValue(1000000000000000000n); // 1 DAIM
        vi.mocked(contracts.isAgentRegistered).mockResolvedValue(true);

        const result = await a2a_get_balance({ address: '0x123' });
        expect(result.content[0].text).toContain('잔고: 1.00 DAIM');
        expect(result.content[0].text).toContain('에이전트 등록 상태: 등록됨 ✅');
    });

    it('a2a_get_balance should handle errors', async () => {
        vi.mocked(contracts.getDaimBalance).mockRejectedValue(new Error('invalid address'));
        const result = await a2a_get_balance({ address: 'invalid' });
        expect(result.content[0].text).toBe('유효하지 않은 지갑 주소입니다. 0x로 시작하는 42자리 주소를 입력하세요.');
    });

    it('a2a_check_task should return formatted task info', async () => {
        // Mock task struct: id, complexityHash, deposit, exists, overheated, creator, submissionTime
        vi.mocked(contracts.getTask).mockResolvedValue([
            1n, 12345n, 1000000000000000000n, true, false, '0xcreator', 1600000000n
        ]);
        const result = await a2a_check_task({ taskId: 1 });
        expect(result.content[0].text).toContain('태스크 ID: 1');
        expect(result.content[0].text).toContain('상태: 활성 (대기 중)');
    });

    it('a2a_list_pending_tasks should return recent pending tasks', async () => {
        vi.mocked(contracts.getNextTaskId).mockResolvedValue(5n);
        vi.mocked(contracts.getTask).mockImplementation(async (id) => {
            if (id === 4 || id === 3) {
                return [BigInt(id), 123n, 100n, true, false, '0xcreator', 160n];
            }
            return [BigInt(id), 0n, 0n, false, false, '0x0', 0n]; // Not exists
        });

        const result = await a2a_list_pending_tasks();
        expect(result.content[0].text).toContain('태스크 4');
        expect(result.content[0].text).toContain('태스크 3');
    });
});
