import { defineConfig } from 'vitest/config'

export default defineConfig({
    test: {
        environment: 'node',
        include: ['packages/**/*.test.ts'],
        pool: 'forks',
        fileParallelism: false,
        server: {
            deps: {
                inline: [
                    /@veramo\/.*/,
                    /did-jwt-vc/,
                    /did-resolver/,
                    /ethr-did-resolver/,
                    /key-did-resolver/
                ]
            }
        }
    },
})
