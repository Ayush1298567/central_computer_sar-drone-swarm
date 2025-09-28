/**
 * Simple API Services Test
 *
 * Basic test to verify that all API services exist and have the expected methods.
 */

const fs = require('fs');
const path = require('path');

// Test configuration
const TEST_CONFIG = {
  verbose: true,
  timeout: 5000,
};

// Test result tracking
const testResults = [];

/**
 * Helper function to run a test
 */
function runTest(testName, testFn) {
  const startTime = Date.now();

  if (TEST_CONFIG.verbose) {
    console.log(`🧪 Running test: ${testName}`);
  }

  try {
    const result = testFn();
    const duration = Date.now() - startTime;

    const testResult = {
      name: testName,
      passed: true,
      duration,
      data: result,
    };

    if (TEST_CONFIG.verbose) {
      console.log(`✅ ${testName} passed in ${duration}ms`);
    }

    testResults.push(testResult);
    return testResult;
  } catch (error) {
    const duration = Date.now() - startTime;

    const testResult = {
      name: testName,
      passed: false,
      duration,
      error: error.message,
    };

    if (TEST_CONFIG.verbose) {
      console.log(`❌ ${testName} failed in ${duration}ms: ${testResult.error}`);
    }

    testResults.push(testResult);
    return testResult;
  }
}

/**
 * Check if file exists and can be read
 */
function checkFileExists(filePath) {
  try {
    const fullPath = path.join(__dirname, filePath);
    if (!fs.existsSync(fullPath)) {
      throw new Error(`File not found: ${filePath}`);
    }
    return { exists: true, path: fullPath };
  } catch (error) {
    throw new Error(`Failed to check file ${filePath}: ${error.message}`);
  }
}

/**
 * Check if TypeScript file contains expected exports
 */
function checkTypeScriptExports(filePath, expectedExports) {
  try {
    const fullPath = path.join(__dirname, filePath);
    const content = fs.readFileSync(fullPath, 'utf8');

    const missingExports = [];

  for (const exportName of expectedExports) {
    // Check for export patterns
    const hasNamedExport = content.includes(`export { ${exportName}`) ||
                         content.includes(`export const ${exportName}`) ||
                         content.includes(`export function ${exportName}`) ||
                         content.includes(`export class ${exportName}`) ||
                         content.includes(`, ${exportName}`) || // For exports like { A, B }
                         content.includes(`${exportName},`) || // For exports like { A, B }
                         content.includes(`${exportName} }`); // For exports like { A, B }

    const hasDefaultExport = content.includes('export default') &&
                           (content.includes(`class ${exportName}`) ||
                            content.includes(`function ${exportName}`));

    if (!hasNamedExport && !hasDefaultExport) {
      missingExports.push(exportName);
    }
  }

    if (missingExports.length > 0) {
      throw new Error(`Missing exports: ${missingExports.join(', ')}`);
    }

    return { exports: expectedExports.length, found: true };
  } catch (error) {
    throw new Error(`Failed to check exports in ${filePath}: ${error.message}`);
  }
}

/**
 * Test Mission Service
 */
function testMissionService() {
  const results = [];

  // Check file exists
  results.push(runTest('MissionService file exists', () => {
    return checkFileExists('missionService.ts');
  }));

  // Check expected exports
  results.push(runTest('MissionService exports', () => {
    const expectedExports = [
      'MissionService',
      'MissionServiceError'
    ];
    return checkTypeScriptExports('missionService.ts', expectedExports);
  }));

  return results;
}

/**
 * Test Drone Service
 */
function testDroneService() {
  const results = [];

  // Check file exists
  results.push(runTest('DroneService file exists', () => {
    return checkFileExists('droneService.ts');
  }));

  // Check expected exports
  results.push(runTest('DroneService exports', () => {
    const expectedExports = [
      'DroneService',
      'DroneServiceError',
      'DroneTelemetryManager'
    ];
    return checkTypeScriptExports('droneService.ts', expectedExports);
  }));

  return results;
}

/**
 * Test Chat Service
 */
function testChatService() {
  const results = [];

  // Check file exists
  results.push(runTest('ChatService file exists', () => {
    return checkFileExists('chatService.ts');
  }));

  // Check expected exports
  results.push(runTest('ChatService exports', () => {
    const expectedExports = [
      'ChatService',
      'ChatServiceError',
      'ChatWebSocketManager'
    ];
    return checkTypeScriptExports('chatService.ts', expectedExports);
  }));

  return results;
}

/**
 * Test Analytics Service
 */
function testAnalyticsService() {
  const results = [];

  // Check file exists
  results.push(runTest('AnalyticsService file exists', () => {
    return checkFileExists('analyticsService.ts');
  }));

  // Check expected exports
  results.push(runTest('AnalyticsService exports', () => {
    const expectedExports = [
      'AnalyticsService',
      'AnalyticsServiceError',
      'DataVisualizationHelper'
    ];
    return checkTypeScriptExports('analyticsService.ts', expectedExports);
  }));

  return results;
}

/**
 * Test TypeScript types
 */
function testTypeScriptTypes() {
  const results = [];

  const typeFiles = [
    '../types/api.ts',
    '../types/mission.ts',
    '../types/drone.ts',
    '../types/chat.ts',
    '../types/analytics.ts'
  ];

  for (const typeFile of typeFiles) {
    results.push(runTest(`TypeScript types: ${path.basename(typeFile)}`, () => {
      return checkFileExists(typeFile);
    }));
  }

  return results;
}

/**
 * Run all tests
 */
function runAllTests() {
  console.log('🚀 Starting Simple API Services Test...\n');

  const startTime = Date.now();

  // Run all test suites
  const allResults = [
    ...testMissionService(),
    ...testDroneService(),
    ...testChatService(),
    ...testAnalyticsService(),
    ...testTypeScriptTypes(),
  ];

  const duration = Date.now() - startTime;
  const total = allResults.length;
  const passed = allResults.filter(r => r.passed).length;
  const failed = total - passed;

  // Print summary
  console.log('\n📊 Test Summary:');
  console.log(`Total tests: ${total}`);
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`⏱️  Duration: ${duration}ms`);

  if (failed > 0) {
    console.log('\n❌ Failed Tests:');
    allResults.filter(r => !r.passed).forEach(result => {
      console.log(`  - ${result.name}: ${result.error}`);
    });
  }

  return {
    total,
    passed,
    failed,
    duration,
    results: allResults,
  };
}

// Run tests if this file is executed directly
if (require.main === module) {
  const summary = runAllTests();
  process.exit(summary.failed > 0 ? 1 : 0);
}

module.exports = { runAllTests };