import { z } from 'zod';

export const ProjectSchema = z.object({
    name: z.string().min(1),
    description: z.string(),
    apiUrl: z.string().url(),
    ownerWallet: z.string().regex(/^0x[a-fA-F0-9]{40}$/, 'Invalid Ethereum wallet address'),
    ownerDid: z.string().optional()
});

export type AgentProject = z.infer<typeof ProjectSchema>;
