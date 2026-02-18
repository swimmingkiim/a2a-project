import { z } from 'zod';

export const ProjectSchema = z.object({
    name: z.string().min(1),
    description: z.string(),
    apiUrl: z.string().url(),
    ownerDid: z.string()
});

export type AgentProject = z.infer<typeof ProjectSchema>;
