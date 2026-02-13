export interface JsonRpcRequest {
    jsonrpc: string;
    method: string;
    params: any[];
    id: number | string;
}

export interface JsonRpcResponse {
    jsonrpc: string;
    result?: any;
    error?: {
        code: number;
        message: string;
        data?: any;
    };
    id: number | string | null;
}

export interface PaymasterContext {
    apiKey?: string;
    clientIp?: string;
    origin?: string;
}
