
import {
    isOverheated,
    getBaseDeposit,
    getDaimBalance,
    isAgentRegistered,
    getPendingTaskCount,
    getNextTaskId,
    getTask
} from './a2a-contracts.js';
import { handleChainError } from './a2a-errors.js';

// Format decimals for DAIM (18 decimals)
function formatDaim(wei: bigint): string {
    const ether = Number(wei) / 1e18;
    return ether.toFixed(2);
}

export const A2A_MANIFEST_TOOLS = [
    {
        name: "a2a_protocol_info",
        description: "Returns the general protocol info and rules for the A2A Protocol.",
        input_schema: {},
    },
    {
        name: "a2a_check_system_status",
        description: "Returns the real-time on-chain data of the A2A Protocol system status.",
        input_schema: {},
    },
    {
        name: "a2a_get_balance",
        description: "Returns the DAIM balance and registration status of a given wallet address.",
        input_schema: {
            type: "object",
            properties: {
                address: { type: "string", description: "The 42-character wallet address starting with 0x" }
            },
            required: ["address"]
        },
    },
    {
        name: "a2a_check_task",
        description: "Returns the exact status of a specific task ID.",
        input_schema: {
            type: "object",
            properties: {
                taskId: { type: "number", description: "The numeric ID of the task to check" }
            },
            required: ["taskId"]
        },
    },
    {
        name: "a2a_list_pending_tasks",
        description: "Returns a list of currently active pending tasks waiting for evaluation.",
        input_schema: {},
    }
];

export async function a2a_protocol_info() {
    const info = `
A2A Protocol Info:
이 프로토콜은 AI 에이전트와 인간 오라클이 상호작용하는 체인 상 경제 시스템입니다.
- AI 에이전트는 Base Mainnet에 태스크를 제출하고 오라클 평가를 통해 보상을 받습니다.
- 주요 토큰: DAIM (스테이킹/보상용)
- 과열(Overheated) 상태에서는 시스템이 일시적으로 새로운 태스크를 제한할 수 있습니다.
- 모든 기록은 온체인에 영구 기록됩니다.
`;
    return { content: [{ type: "text", text: info.trim() }] };
}

export async function a2a_check_system_status() {
    try {
        const [pendingCount, baseDeposit, overheated] = await Promise.all([
            getPendingTaskCount(),
            getBaseDeposit().catch(() => 0n), // fallback if function not available
            isOverheated()
        ]);

        const status = `
[A2A 실시간 시스템 상태]
- 대기 중인 태스크: ${pendingCount} 개
- 기본 예치금: ${formatDaim(baseDeposit)} DAIM
- 과열 상태: ${overheated ? '과열 (주의)' : '안정 (정상 작동 중)'}
`;
        return { content: [{ type: "text", text: status.trim() }] };
    } catch (error) {
        return { content: [{ type: "text", text: handleChainError(error) }] };
    }
}

export async function a2a_get_balance({ address }: { address: string }) {
    try {
        const [balance, registered] = await Promise.all([
            getDaimBalance(address),
            isAgentRegistered(address)
        ]);

        const status = `
[지갑 정보: ${address}]
- 잔고: ${formatDaim(balance)} DAIM
- 에이전트 등록 상태: ${registered ? '등록됨 ✅' : '미등록 ❌'}
`;
        return { content: [{ type: "text", text: status.trim() }] };
    } catch (error) {
        return { content: [{ type: "text", text: handleChainError(error) }] };
    }
}

export async function a2a_check_task({ taskId }: { taskId: number }) {
    try {
        const task = await getTask(taskId);
        // Struct: id, complexityHash, deposit, exists, overheated, creator, submissionTime
        const exists = task[3];
        if (!exists) {
            return { content: [{ type: "text", text: `태스크 ID ${taskId} 를 찾을 수 없거나 이미 완료/삭제되었습니다.` }] };
        }

        const overheatedStr = task[4] ? '예' : '아니오';
        const depositStr = formatDaim(task[2]);

        const status = `
[태스크 정보]
- 태스크 ID: ${task[0]}
- 상태: 활성 (대기 중)
- 생성자: ${task[5]}
- 예치금: ${depositStr} DAIM
- 해시: ${task[1].toString()}
- 과열 상태 시 제출됨: ${overheatedStr}
`;
        return { content: [{ type: "text", text: status.trim() }] };
    } catch (error) {
        return { content: [{ type: "text", text: handleChainError(error) }] };
    }
}

export async function a2a_list_pending_tasks() {
    try {
        const nextId = await getNextTaskId();
        const startId = Number(nextId) - 10 > 0 ? Number(nextId) - 10 : 0;

        const tasks = [];
        for (let i = Number(nextId) - 1; i >= startId; i--) {
            try {
                const task = await getTask(i);
                if (task[3]) { // exists
                    tasks.push(`- 태스크 ${task[0]}: 생성자 ${task[5]} / 예치금 ${formatDaim(task[2])} DAIM`);
                }
            } catch (e) { /* ignore single errors */ }
        }

        if (tasks.length === 0) {
            return { content: [{ type: "text", text: "현재 대기 중인 태스크가 없습니다." }] };
        }

        return { content: [{ type: "text", text: `[최근 대기 중인 태스크]\n${tasks.join('\n')}` }] };
    } catch (error) {
        return { content: [{ type: "text", text: handleChainError(error) }] };
    }
}
