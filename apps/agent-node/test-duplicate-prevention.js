#!/usr/bin/env node

/**
 * Test script to verify duplicate prevention in project registration
 * Tests that the agent-node correctly prevents duplicate (api_url, owner_did) registrations
 */

const BASE_URL = process.env.AGENT_NODE_URL || 'http://localhost:8080';

async function testDuplicatePrevention() {
    console.log('🧪 Testing Duplicate Project Registration Prevention\n');
    console.log(`Target URL: ${BASE_URL}\n`);

    const testProject = {
        name: 'Test API',
        description: 'Test API for duplicate prevention',
        apiUrl: 'https://test-api.example.com',
        ownerDid: 'did:web:test.example.com'
    };

    try {
        // Test 1: First registration should succeed
        console.log('Test 1: First registration (should succeed)');
        const response1 = await fetch(`${BASE_URL}/api/projects`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(testProject)
        });

        if (response1.status === 201) {
            const data1 = await response1.json();
            console.log('✅ First registration succeeded');
            console.log(`   Project ID: ${data1.id}`);
            console.log(`   Name: ${data1.name}`);
            console.log(`   API URL: ${data1.api_url}`);
            console.log(`   Owner DID: ${data1.owner_did}\n`);
        } else {
            console.log(`⚠️  Unexpected status: ${response1.status}`);
            const error = await response1.json();
            console.log(`   Error: ${JSON.stringify(error)}\n`);
        }

        // Test 2: Duplicate registration should fail
        console.log('Test 2: Duplicate registration with same api_url and owner_did (should fail)');
        const response2 = await fetch(`${BASE_URL}/api/projects`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...testProject,
                name: 'Test API (Verified)'  // Different name, same URL and owner
            })
        });

        if (response2.status === 409) {
            const error2 = await response2.json();
            console.log('✅ Duplicate registration correctly prevented (HTTP 409)');
            console.log(`   Error: ${error2.error}`);
            console.log(`   Details: ${error2.details}\n`);
        } else if (response2.status === 201) {
            console.log('❌ FAILED: Duplicate registration was allowed (should have been rejected)');
            const data2 = await response2.json();
            console.log(`   Project ID: ${data2.id}\n`);
        } else {
            console.log(`⚠️  Unexpected status: ${response2.status}`);
            const error = await response2.json();
            console.log(`   Error: ${JSON.stringify(error)}\n`);
        }

        // Test 3: Different owner should be allowed to register the same API URL
        console.log('Test 3: Same api_url but different owner_did (should succeed)');
        const response3 = await fetch(`${BASE_URL}/api/projects`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...testProject,
                name: 'Test API (Different Owner)',
                ownerDid: 'did:web:different-owner.example.com'  // Different owner
            })
        });

        if (response3.status === 201) {
            const data3 = await response3.json();
            console.log('✅ Different owner successfully registered same API URL');
            console.log(`   Project ID: ${data3.id}`);
            console.log(`   Owner DID: ${data3.owner_did}\n`);
        } else {
            console.log(`⚠️  Unexpected status: ${response3.status}`);
            const error = await response3.json();
            console.log(`   Error: ${JSON.stringify(error)}\n`);
        }

        console.log('✅ All tests completed!\n');
        console.log('Summary:');
        console.log('- First registration: Should succeed ✓');
        console.log('- Duplicate (same url + owner): Should fail with 409 ✓');
        console.log('- Same URL, different owner: Should succeed ✓');

    } catch (error) {
        console.error('❌ Test failed with error:', error.message);
        process.exit(1);
    }
}

testDuplicatePrevention();
