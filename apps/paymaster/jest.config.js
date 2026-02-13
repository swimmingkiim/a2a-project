/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
    // preset: 'ts-jest', // Removed to avoid resolution issues
    testEnvironment: 'node',
    testMatch: ['**/*.test.ts'],
    verbose: true,
    forceExit: true,
    clearMocks: true,
    resetMocks: true,
    restoreMocks: true,
    transformIgnorePatterns: [
        'node_modules/(?!(viem)/)'
    ],
    transform: {
        '^.+\\.tsx?$': [require.resolve('ts-jest'), {
            tsconfig: 'tsconfig.json',
            isolatedModules: true
        }]
    }
};
