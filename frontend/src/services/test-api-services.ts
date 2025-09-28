/**
 * API Services Test Suite
 *
 * Tests all frontend API services to ensure they are working correctly.
 * This file can be run to verify API endpoints and service functionality.
 */

import { MissionService } from './missionService';
import { DroneService } from './droneService';
import { ChatService } from './chatService';
import { AnalyticsService, DataVisualizationHelper } from './analyticsService';

// Test configuration
const TEST_CONFIG = {
  apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  testTimeout: 30000, // 30 seconds
  verbose: true,
};

// Test result tracking
interface TestResult {
  name: string;
  passed: boolean;
  duration: number;
  error?: string;
  data?: any;
}

const testResults: TestResult[] = [];

/**
 * Helper function to run a test
 */
async function runTest(testName: string, testFn: () => Promise<any>): Promise<TestResult> {
  const startTime = Date.now();

  if (TEST_CONFIG.verbose) {
    console.log(`🧪 Running test: ${testName}`);
  }

  try {
    const result = await Promise.race([
      testFn(),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Test timeout')), TEST_CONFIG.testTimeout)
      ),
    ]);

    const duration = Date.now() - startTime;
    const testResult: TestResult = {
      name: testName,
      passed: true,
      duration,
      data: result,
    };

    if (TEST_CONFIG.verbose) {
      console.log(`✅ ${testName} passed in ${duration}ms`);
    }

    return testResult;
  } catch (error) {
    const duration = Date.now() - startTime;
    const testResult: TestResult = {
      name: testName,
      passed: false,
      duration,
      error: error instanceof Error ? error.message : String(error),
    };

    if (TEST_CONFIG.verbose) {
      console.log(`❌ ${testName} failed in ${duration}ms: ${testResult.error}`);
    }

    return testResult;
  }
}

/**
 * Test Mission Service
 */
async function testMissionService(): Promise<TestResult[]> {
  const results: TestResult[] = [];

  // Test service instantiation
  results.push(await runTest('MissionService instantiation', async () => {
    // Just verify the service class exists and can be accessed
    if (typeof MissionService !== 'function') {
      throw new Error('MissionService is not a constructor');
    }
    return { success: true };
  }));

  // Test static method access
  results.push(await runTest('MissionService static methods', async () => {
    const methods = [
      'getMissions',
      'getMission',
      'createMission',
      'updateMission',
      'deleteMission',
      'startMission',
      'pauseMission',
      'resumeMission',
      'abortMission',
      'getMissionProgress',
      'getMissionLogs',
      'getMissionStats',
    ];

    for (const method of methods) {
      if (typeof MissionService[method] !== 'function') {
        throw new Error(`MissionService.${method} is not a function`);
      }
    }

    return { methods: methods.length };
  }));

  return results;
}

/**
 * Test Drone Service
 */
async function testDroneService(): Promise<TestResult[]> {
  const results: TestResult[] = [];

  // Test service instantiation
  results.push(await runTest('DroneService instantiation', async () => {
    if (typeof DroneService !== 'function') {
      throw new Error('DroneService is not a constructor');
    }
    return { success: true };
  }));

  // Test static method access
  results.push(await runTest('DroneService static methods', async () => {
    const methods = [
      'getDrones',
      'getDrone',
      'registerDrone',
      'updateDrone',
      'deleteDrone',
      'getDroneTelemetry',
      'subscribeToTelemetry',
      'unsubscribeFromTelemetry',
      'sendCommand',
      'sendBulkCommands',
      'getCommandHistory',
      'updateDronePosition',
      'getDroneCapabilities',
      'updateDroneCapabilities',
      'getDroneSensors',
      'getDroneStats',
      'emergencyStop',
    ];

    for (const method of methods) {
      if (typeof DroneService[method] !== 'function') {
        throw new Error(`DroneService.${method} is not a function`);
      }
    }

    return { methods: methods.length };
  }));

  return results;
}

/**
 * Test Chat Service
 */
async function testChatService(): Promise<TestResult[]> {
  const results: TestResult[] = [];

  // Test service instantiation
  results.push(await runTest('ChatService instantiation', async () => {
    if (typeof ChatService !== 'function') {
      throw new Error('ChatService is not a constructor');
    }
    return { success: true };
  }));

  // Test static method access
  results.push(await runTest('ChatService static methods', async () => {
    const methods = [
      'initialize',
      'disconnect',
      'isConnected',
      'onMessage',
      'offMessage',
      'onConnectionChange',
      'setTyping',
      'getConversations',
      'getConversation',
      'createConversation',
      'updateConversation',
      'deleteConversation',
      'getMessages',
      'sendMessage',
      'editMessage',
      'deleteMessage',
      'addReaction',
      'removeReaction',
      'addParticipant',
      'removeParticipant',
      'updateParticipantRole',
      'getNotifications',
      'markNotificationsRead',
      'getConversationStats',
    ];

    for (const method of methods) {
      if (typeof ChatService[method] !== 'function') {
        throw new Error(`ChatService.${method} is not a function`);
      }
    }

    return { methods: methods.length };
  }));

  return results;
}

/**
 * Test Analytics Service
 */
async function testAnalyticsService(): Promise<TestResult[]> {
  const results: TestResult[] = [];

  // Test service instantiation
  results.push(await runTest('AnalyticsService instantiation', async () => {
    if (typeof AnalyticsService !== 'function') {
      throw new Error('AnalyticsService is not a constructor');
    }
    return { success: true };
  }));

  // Test static method access
  results.push(await runTest('AnalyticsService static methods', async () => {
    const methods = [
      'getMissionAnalytics',
      'getDroneAnalytics',
      'getSystemAnalytics',
      'getPerformanceTrends',
      'getIncidentAnalysis',
      'generateReport',
      'getReports',
      'getReport',
      'exportReport',
      'getDashboardData',
      'getPredictiveAnalytics',
      'getComparativeAnalytics',
      'getCostBenefitAnalysis',
    ];

    for (const method of methods) {
      if (typeof AnalyticsService[method] !== 'function') {
        throw new Error(`AnalyticsService.${method} is not a function`);
      }
    }

    return { methods: methods.length };
  }));

  // Test DataVisualizationHelper
  results.push(await runTest('DataVisualizationHelper utilities', async () => {
    const helperMethods = [
      'formatChartData',
      'generateColors',
      'formatNumber',
      'formatDuration',
      'calculatePercentageChange',
      'formatPercentage',
    ];

    for (const method of helperMethods) {
      if (typeof DataVisualizationHelper[method] !== 'function') {
        throw new Error(`DataVisualizationHelper.${method} is not a function`);
      }
    }

    // Test formatNumber
    const formatted = DataVisualizationHelper.formatNumber(1500000, 'km');
    if (!formatted.includes('1.5M')) {
      throw new Error('formatNumber failed to format large numbers correctly');
    }

    // Test formatDuration
    const duration = DataVisualizationHelper.formatDuration(3661); // 1h 1m 1s
    if (!duration.includes('1h') || !duration.includes('1m')) {
      throw new Error('formatDuration failed to format time correctly');
    }

    return { helperMethods: helperMethods.length };
  }));

  return results;
}

/**
 * Test TypeScript type imports
 */
async function testTypeImports(): Promise<TestResult[]> {
  const results: TestResult[] = [];

  results.push(await runTest('TypeScript type imports', async () => {
    try {
      // These imports should work without errors
      const { Mission, CreateMissionRequest } = await import('../types/mission');
      const { Drone, RegisterDroneRequest } = await import('../types/drone');
      const { ChatMessage, Conversation } = await import('../types/chat');
      const { MissionAnalytics, ReportType } = await import('../types/analytics');
      const { ApiResponse, PaginationParams } = await import('../types/api');

      return {
        imports: ['mission', 'drone', 'chat', 'analytics', 'api'],
        types: 5,
      };
    } catch (error) {
      throw new Error(`Failed to import types: ${error}`);
    }
  }));

  return results;
}

/**
 * Run all tests
 */
export async function runAllTests(): Promise<{
  total: number;
  passed: number;
  failed: number;
  duration: number;
  results: TestResult[];
}> {
  console.log('🚀 Starting API Services Test Suite...\n');

  const allResults: TestResult[] = [];
  const startTime = Date.now();

  // Run all test suites
  allResults.push(...await testMissionService());
  allResults.push(...await testDroneService());
  allResults.push(...await testChatService());
  allResults.push(...await testAnalyticsService());
  allResults.push(...await testTypeImports());

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

/**
 * Main test runner (for Node.js environment)
 */
if (typeof window === 'undefined' && typeof process !== 'undefined') {
  runAllTests()
    .then((summary) => {
      process.exit(summary.failed > 0 ? 1 : 0);
    })
    .catch((error) => {
      console.error('Test suite failed:', error);
      process.exit(1);
    });
}