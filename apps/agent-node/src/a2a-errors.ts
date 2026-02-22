/**
 * Wraps on-chain queries to provide structured, Korean error messages.
 */
export function handleChainError(error: unknown): string {
    const message = error instanceof Error ? error.message : String(error);

    if (message.includes('network')) {
        return "Base Mainnet RPC 연결 실패. 잠시 후 재시도하세요.";
    }

    if (message.includes('invalid address')) {
        return "유효하지 않은 지갑 주소입니다. 0x로 시작하는 42자리 주소를 입력하세요.";
    }

    return `조회 실패: ${message}`;
}
