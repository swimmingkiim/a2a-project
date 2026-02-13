
import { defineConfig } from 'vitest/config'

export default defineConfig({
    test: {
        include: ['test/**/*.test.ts', 'test/**/*.ts'],
        exclude: ['test/session-flow.ts']
    },
})
