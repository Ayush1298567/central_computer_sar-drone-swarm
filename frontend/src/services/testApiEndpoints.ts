// API Endpoints Test Suite
// Tests all API services to ensure they work properly from frontend

import { missionService, Mission } from './missionService';
import { droneService, Drone } from './droneService';
import { chatService, Conversation, ChatMessage } from './chatService';
import { analyticsService } from './analyticsService';
import { api, checkApiHealth } from './api';

// Test configuration
const TEST_CONFIG = {
  timeout: 10000, // 10 seconds per test
  delay: 1000, // 1 second delay between tests
  verbose: true,
};

// Test result interface
interface TestResult {
  test: string;
  passed: boolean;
  duration: number;
  error?: string;
  data?: any;
}

// Logging utility
class TestLogger {
  static log(message: string, data?: any) {
    if (TEST_CONFIG.verbose) {
      console.log(`[TEST] ${message}`, data ? JSON.stringify(data, null, 2) : '');
    }
  }

  static error(message: string, error?: any) {
    console.error(`[TEST ERROR] ${message}`, error);
  }

  static success(message: string, data?: any) {
    console.log(`[TEST SUCCESS] ${message}`, data ? JSON.stringify(data, null, 2) : '');
  }
}

// Test utilities
class TestUtils {
  static async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  static async withTimeout<T>(promise: Promise<T>, timeout: number): Promise<T> {
    const timeoutPromise = new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(`Test timed out after ${timeout}ms`)), timeout)
    );

    return Promise.race([promise, timeoutPromise]);
  }

  static formatDuration(ms: number): string {
    return `${(ms / 1000).toFixed(2)}s`;
  }
}

// API Services Test Suite
export class ApiEndpointsTest {
  private results: TestResult[] = [];

  async runAllTests(): Promise<TestResult[]> {
    TestLogger.log('Starting API endpoints test suite...');

    try {
      // Test API health first
      await this.testApiHealth();

      // Test Mission Service
      await this.testMissionService();

      // Test Drone Service
      await this.testDroneService();

      // Test Chat Service
      await this.testChatService();

      // Test Analytics Service
      await this.testAnalyticsService();

      // Summary
      this.printSummary();

      return this.results;
    } catch (error) {
      TestLogger.error('Test suite failed:', error);
      throw error;
    }
  }

  private async testApiHealth(): Promise<void> {
    const startTime = Date.now();

    try {
      TestLogger.log('Testing API health check...');

      const isHealthy = await TestUtils.withTimeout(checkApiHealth(), TEST_CONFIG.timeout);

      const duration = Date.now() - startTime;
      this.results.push({
        test: 'API Health Check',
        passed: isHealthy,
        duration,
        error: isHealthy ? undefined : 'API is not responding'
      });

      if (isHealthy) {
        TestLogger.success('API health check passed', { duration: TestUtils.formatDuration(duration) });
      } else {
        TestLogger.error('API health check failed');
      }

      await TestUtils.delay(TEST_CONFIG.delay);
    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.push({
        test: 'API Health Check',
        passed: false,
        duration,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      TestLogger.error('API health check failed:', error);
    }
  }

  private async testMissionService(): Promise<void> {
    TestLogger.log('Testing Mission Service...');

    // Test getting missions list
    await this.testMissionList();

    // Test getting single mission (if any exist)
    await this.testSingleMission();

    // Test mission creation (commented out to avoid creating test data)
    // await this.testCreateMission();

    // Test mission analytics
    await this.testMissionAnalytics();
  }

  private async testMissionList(): Promise<void> {
    const startTime = Date.now();

    try {
      TestLogger.log('Testing mission list retrieval...');

      const response = await TestUtils.withTimeout(
        missionService.getMissions(1, 10),
        TEST_CONFIG.timeout
      );

      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Mission List Retrieval',
        passed: true,
        duration,
        data: { count: response.missions.length, total: response.total }
      });

      TestLogger.success('Mission list retrieval passed', {
        count: response.missions.length,
        duration: TestUtils.formatDuration(duration)
      });

      await TestUtils.delay(TEST_CONFIG.delay);
    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Mission List Retrieval',
        passed: false,
        duration,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      TestLogger.error('Mission list retrieval failed:', error);
    }
  }

  private async testSingleMission(): Promise<void> {
    const startTime = Date.now();

    try {
      // First get missions list to get an ID
      const missionsResponse = await missionService.getMissions(1, 1);

      if (missionsResponse.missions.length === 0) {
        TestLogger.log('No missions found, skipping single mission test');
        return;
      }

      const missionId = missionsResponse.missions[0].id;
      TestLogger.log('Testing single mission retrieval...', { missionId });

      const mission = await TestUtils.withTimeout(
        missionService.getMission(missionId),
        TEST_CONFIG.timeout
      );

      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Single Mission Retrieval',
        passed: true,
        duration,
        data: { missionId, missionName: mission.name }
      });

      TestLogger.success('Single mission retrieval passed', {
        missionId,
        missionName: mission.name,
        duration: TestUtils.formatDuration(duration)
      });

      await TestUtils.delay(TEST_CONFIG.delay);
    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Single Mission Retrieval',
        passed: false,
        duration,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      TestLogger.error('Single mission retrieval failed:', error);
    }
  }

  private async testMissionAnalytics(): Promise<void> {
    const startTime = Date.now();

    try {
      TestLogger.log('Testing mission analytics retrieval...');

      const analytics = await TestUtils.withTimeout(
        missionService.getMissionAnalytics('7d'),
        TEST_CONFIG.timeout
      );

      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Mission Analytics',
        passed: true,
        duration,
        data: {
          totalMissions: analytics.total_missions,
          successRate: analytics.success_rate
        }
      });

      TestLogger.success('Mission analytics retrieval passed', {
        totalMissions: analytics.total_missions,
        successRate: analytics.success_rate,
        duration: TestUtils.formatDuration(duration)
      });

      await TestUtils.delay(TEST_CONFIG.delay);
    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Mission Analytics',
        passed: false,
        duration,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      TestLogger.error('Mission analytics retrieval failed:', error);
    }
  }

  private async testDroneService(): Promise<void> {
    TestLogger.log('Testing Drone Service...');

    // Test drone list
    await this.testDroneList();

    // Test drone fleet analytics
    await this.testDroneFleet();
  }

  private async testDroneList(): Promise<void> {
    const startTime = Date.now();

    try {
      TestLogger.log('Testing drone list retrieval...');

      const drones = await TestUtils.withTimeout(
        droneService.getDrones(),
        TEST_CONFIG.timeout
      );

      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Drone List Retrieval',
        passed: true,
        duration,
        data: { count: drones.length }
      });

      TestLogger.success('Drone list retrieval passed', {
        count: drones.length,
        duration: TestUtils.formatDuration(duration)
      });

      await TestUtils.delay(TEST_CONFIG.delay);
    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Drone List Retrieval',
        passed: false,
        duration,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      TestLogger.error('Drone list retrieval failed:', error);
    }
  }

  private async testDroneFleet(): Promise<void> {
    const startTime = Date.now();

    try {
      TestLogger.log('Testing drone fleet analytics...');

      const fleet = await TestUtils.withTimeout(
        droneService.getDroneFleet(),
        TEST_CONFIG.timeout
      );

      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Drone Fleet Analytics',
        passed: true,
        duration,
        data: {
          totalDrones: fleet.total_drones,
          onlineDrones: fleet.online_drones,
          fleetEfficiency: fleet.fleet_efficiency
        }
      });

      TestLogger.success('Drone fleet analytics passed', {
        totalDrones: fleet.total_drones,
        onlineDrones: fleet.online_drones,
        fleetEfficiency: fleet.fleet_efficiency,
        duration: TestUtils.formatDuration(duration)
      });

      await TestUtils.delay(TEST_CONFIG.delay);
    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Drone Fleet Analytics',
        passed: false,
        duration,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      TestLogger.error('Drone fleet analytics failed:', error);
    }
  }

  private async testChatService(): Promise<void> {
    TestLogger.log('Testing Chat Service...');

    // Test conversations list
    await this.testConversationsList();

    // Test chat analytics
    await this.testChatAnalytics();
  }

  private async testConversationsList(): Promise<void> {
    const startTime = Date.now();

    try {
      TestLogger.log('Testing conversations list retrieval...');

      const response = await TestUtils.withTimeout(
        chatService.getConversations(1, 10),
        TEST_CONFIG.timeout
      );

      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Conversations List Retrieval',
        passed: true,
        duration,
        data: { count: response.conversations.length, total: response.total }
      });

      TestLogger.success('Conversations list retrieval passed', {
        count: response.conversations.length,
        duration: TestUtils.formatDuration(duration)
      });

      await TestUtils.delay(TEST_CONFIG.delay);
    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Conversations List Retrieval',
        passed: false,
        duration,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      TestLogger.error('Conversations list retrieval failed:', error);
    }
  }

  private async testChatAnalytics(): Promise<void> {
    const startTime = Date.now();

    try {
      TestLogger.log('Testing chat analytics retrieval...');

      const analytics = await TestUtils.withTimeout(
        chatService.getChatAnalytics('7d'),
        TEST_CONFIG.timeout
      );

      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Chat Analytics',
        passed: true,
        duration,
        data: {
          totalMessages: analytics.total_messages,
          activeConversations: analytics.active_conversations
        }
      });

      TestLogger.success('Chat analytics retrieval passed', {
        totalMessages: analytics.total_messages,
        activeConversations: analytics.active_conversations,
        duration: TestUtils.formatDuration(duration)
      });

      await TestUtils.delay(TEST_CONFIG.delay);
    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Chat Analytics',
        passed: false,
        duration,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      TestLogger.error('Chat analytics retrieval failed:', error);
    }
  }

  private async testAnalyticsService(): Promise<void> {
    TestLogger.log('Testing Analytics Service...');

    // Test mission analytics
    await this.testAnalyticsMission();

    // Test drone analytics
    await this.testAnalyticsDrone();

    // Test system analytics
    await this.testAnalyticsSystem();
  }

  private async testAnalyticsMission(): Promise<void> {
    const startTime = Date.now();

    try {
      TestLogger.log('Testing analytics mission data...');

      const analytics = await TestUtils.withTimeout(
        analyticsService.getMissionAnalytics('30d'),
        TEST_CONFIG.timeout
      );

      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Analytics Mission Data',
        passed: true,
        duration,
        data: {
          totalMissions: analytics.total_missions,
          successRate: analytics.success_rate
        }
      });

      TestLogger.success('Analytics mission data passed', {
        totalMissions: analytics.total_missions,
        successRate: analytics.success_rate,
        duration: TestUtils.formatDuration(duration)
      });

      await TestUtils.delay(TEST_CONFIG.delay);
    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Analytics Mission Data',
        passed: false,
        duration,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      TestLogger.error('Analytics mission data failed:', error);
    }
  }

  private async testAnalyticsDrone(): Promise<void> {
    const startTime = Date.now();

    try {
      TestLogger.log('Testing analytics drone data...');

      const analytics = await TestUtils.withTimeout(
        analyticsService.getDroneAnalytics('30d'),
        TEST_CONFIG.timeout
      );

      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Analytics Drone Data',
        passed: true,
        duration,
        data: {
          totalDrones: analytics.fleet_overview.total_drones,
          onlineDrones: analytics.fleet_overview.online_drones
        }
      });

      TestLogger.success('Analytics drone data passed', {
        totalDrones: analytics.fleet_overview.total_drones,
        onlineDrones: analytics.fleet_overview.online_drones,
        duration: TestUtils.formatDuration(duration)
      });

      await TestUtils.delay(TEST_CONFIG.delay);
    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Analytics Drone Data',
        passed: false,
        duration,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      TestLogger.error('Analytics drone data failed:', error);
    }
  }

  private async testAnalyticsSystem(): Promise<void> {
    const startTime = Date.now();

    try {
      TestLogger.log('Testing analytics system data...');

      const analytics = await TestUtils.withTimeout(
        analyticsService.getSystemAnalytics('24h'),
        TEST_CONFIG.timeout
      );

      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Analytics System Data',
        passed: true,
        duration,
        data: {
          uptimePercentage: analytics.uptime_percentage,
          totalRequests: analytics.total_requests,
          errorRate: analytics.error_rate
        }
      });

      TestLogger.success('Analytics system data passed', {
        uptimePercentage: analytics.uptime_percentage,
        totalRequests: analytics.total_requests,
        errorRate: analytics.error_rate,
        duration: TestUtils.formatDuration(duration)
      });

      await TestUtils.delay(TEST_CONFIG.delay);
    } catch (error) {
      const duration = Date.now() - startTime;
      this.results.push({
        test: 'Analytics System Data',
        passed: false,
        duration,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      TestLogger.error('Analytics system data failed:', error);
    }
  }

  private printSummary(): void {
    const totalTests = this.results.length;
    const passedTests = this.results.filter(r => r.passed).length;
    const failedTests = totalTests - passedTests;
    const totalDuration = this.results.reduce((sum, r) => sum + r.duration, 0);

    TestLogger.log('=== TEST SUMMARY ===');
    TestLogger.log(`Total Tests: ${totalTests}`);
    TestLogger.log(`Passed: ${passedTests}`);
    TestLogger.log(`Failed: ${failedTests}`);
    TestLogger.log(`Success Rate: ${((passedTests / totalTests) * 100).toFixed(1)}%`);
    TestLogger.log(`Total Duration: ${TestUtils.formatDuration(totalDuration)}`);

    if (failedTests > 0) {
      TestLogger.log('Failed Tests:');
      this.results.filter(r => !r.passed).forEach(result => {
        TestLogger.error(`- ${result.test}: ${result.error}`);
      });
    }

    if (passedTests === totalTests) {
      TestLogger.success('All tests passed! API services are working correctly.');
    } else {
      TestLogger.error(`${failedTests} test(s) failed. Please check the API services.`);
    }
  }
}

// Export test runner function
export const runApiTests = async (): Promise<TestResult[]> => {
  const testSuite = new ApiEndpointsTest();
  return await testSuite.runAllTests();
};

// Export individual test functions for manual testing
export const testApiHealth = () => new ApiEndpointsTest().testApiHealth();
export const testMissionService = () => new ApiEndpointsTest().testMissionService();
export const testDroneService = () => new ApiEndpointsTest().testDroneService();
export const testChatService = () => new ApiEndpointsTest().testChatService();
export const testAnalyticsService = () => new ApiEndpointsTest().testAnalyticsService();