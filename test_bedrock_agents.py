#!/usr/bin/env python3
"""
Quick test script for AWS Bedrock AI Agents in FlexDeploy
Tests all three agent implementations
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.bedrock_agents import (
    get_bedrock_service,
    RingCategorizationAgent,
    DeploymentFailureAgent,
    GatingFactorAgent
)

def test_bedrock_connection():
    """Test basic AWS Bedrock connection"""
    print("=" * 60)
    print("TEST 1: AWS Bedrock Connection")
    print("=" * 60)
    
    try:
        bedrock = get_bedrock_service()
        response = bedrock.invoke_model(
            prompt="Say 'Connection successful' in 3 words or less.",
            max_tokens=10,
            temperature=0.1
        )
        print(f"✓ Connection successful!")
        print(f"✓ Response: {response.strip()}")
        return bedrock
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nPlease check:")
        print("  1. AWS credentials in ~/.aws/credentials")
        print("  2. Bedrock model access enabled")
        print("  3. IAM permissions for bedrock:InvokeModel")
        return None


def test_ring_categorization(bedrock):
    """Test ring categorization agent"""
    print("\n" + "=" * 60)
    print("TEST 2: Ring Categorization Agent")
    print("=" * 60)
    
    # Mock device data
    device = {
        "deviceId": "DEV-TEST-001",
        "deviceName": "Test Laptop",
        "manufacturer": "Dell",
        "model": "Latitude 5520",
        "osName": "Windows 11",
        "site": "HQ",
        "department": "Engineering",
        "ring": 0,
        "totalMemory": "16 GB",
        "totalStorage": "512 GB",
        "networkSpeed": "1 Gbps",
        "avgCpuUsage": 45.0,
        "avgMemoryUsage": 60.0,
        "avgDiskSpace": 40.0,
        "riskScore": 75
    }
    
    rings = [
        {
            "ringId": 0,
            "ringName": "Ring 0 - Canary (Test Bed)",
            "categorizationPrompt": "Devices used for testing and validation in controlled environments"
        },
        {
            "ringId": 1,
            "ringName": "Ring 1 - Low Risk Devices",
            "categorizationPrompt": "Stable devices with good metrics that can tolerate minor issues"
        },
        {
            "ringId": 2,
            "ringName": "Ring 2 - High Risk Devices",
            "categorizationPrompt": "Devices with concerning metrics or in critical but not VIP roles"
        },
        {
            "ringId": 3,
            "ringName": "Ring 3 - VIP Devices",
            "categorizationPrompt": "Critical business devices requiring highest stability and uptime"
        }
    ]
    
    try:
        # Mock DB connection (None for testing)
        agent = RingCategorizationAgent(bedrock, None)
        
        print(f"\nCategorizing device: {device['deviceId']}")
        print(f"  CPU: {device['avgCpuUsage']}%")
        print(f"  Memory: {device['avgMemoryUsage']}%")
        print(f"  Disk Free: {device['avgDiskSpace']}%")
        print(f"  Risk Score: {device['riskScore']}")
        
        ring_id, reasoning = agent.categorize_device(device, rings)
        
        print(f"\n✓ Categorization complete!")
        print(f"✓ Assigned Ring: {ring_id} ({rings[ring_id]['ringName']})")
        print(f"✓ Reasoning: {reasoning}")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_failure_analysis(bedrock):
    """Test deployment failure analysis agent"""
    print("\n" + "=" * 60)
    print("TEST 3: Deployment Failure Analysis Agent")
    print("=" * 60)
    
    # Mock deployment data
    device_metrics = [
        {
            "deviceId": "DEV-001",
            "deviceName": "Server-01",
            "avgCpuUsage": 85.0,
            "avgMemoryUsage": 90.0,
            "avgDiskSpace": 15.0,
            "riskScore": 45
        },
        {
            "deviceId": "DEV-002",
            "deviceName": "Server-02",
            "avgCpuUsage": 92.0,
            "avgMemoryUsage": 88.0,
            "avgDiskSpace": 18.0,
            "riskScore": 40
        },
        {
            "deviceId": "DEV-003",
            "deviceName": "Workstation-01",
            "avgCpuUsage": 75.0,
            "avgMemoryUsage": 70.0,
            "avgDiskSpace": 25.0,
            "riskScore": 65
        }
    ]
    
    gating_factors = {
        "avgCpuUsageMax": 80.0,
        "avgMemoryUsageMax": 85.0,
        "avgDiskFreeSpaceMin": 20.0,
        "riskScoreMin": 50,
        "riskScoreMax": 100
    }
    
    try:
        agent = DeploymentFailureAgent(bedrock)
        
        print(f"\nAnalyzing failed deployment...")
        print(f"  Ring: Ring 1 - Low Risk")
        print(f"  Devices: {len(device_metrics)}")
        print(f"  Gating - Max CPU: {gating_factors['avgCpuUsageMax']}%")
        print(f"  Gating - Max Memory: {gating_factors['avgMemoryUsageMax']}%")
        print(f"  Gating - Min Disk: {gating_factors['avgDiskFreeSpaceMin']}%")
        
        analysis = agent.analyze_failure(
            ring_name="Ring 1 - Low Risk Devices",
            device_metrics=device_metrics,
            gating_factors=gating_factors,
            deployment_name="Q4-2025 Security Update"
        )
        
        print(f"\n✓ Analysis complete!")
        print(f"✓ AI Analysis:")
        print(f"  {analysis}")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_gating_factor_parsing(bedrock):
    """Test gating factor natural language parsing"""
    print("\n" + "=" * 60)
    print("TEST 4: Gating Factor Parsing Agent")
    print("=" * 60)
    
    test_inputs = [
        "I want to be very conservative - only deploy to the most stable devices",
        "Deploy aggressively to all devices except those completely broken",
        "Only deploy to devices with CPU under 70% and at least 25% free disk space"
    ]
    
    try:
        agent = GatingFactorAgent(bedrock)
        
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\n--- Test Input {i} ---")
            print(f"User: \"{user_input}\"")
            
            result = agent.parse_natural_language(user_input)
            
            print(f"\n✓ Parsed Gating Factors:")
            print(f"  Max CPU Usage: {result['avgCpuUsageMax']}%")
            print(f"  Max Memory Usage: {result['avgMemoryUsageMax']}%")
            print(f"  Min Disk Free: {result['avgDiskFreeSpaceMin']}%")
            print(f"  Risk Score Range: {result['riskScoreMin']}-{result['riskScoreMax']}")
            print(f"  Explanation: {result['explanation']}")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_gating_factor_validation(bedrock):
    """Test gating factor validation"""
    print("\n" + "=" * 60)
    print("TEST 5: Gating Factor Validation Agent")
    print("=" * 60)
    
    test_factors = {
        "avgCpuUsageMax": 95.0,
        "avgMemoryUsageMax": 95.0,
        "avgDiskFreeSpaceMin": 5.0,
        "riskScoreMin": 0,
        "riskScoreMax": 100
    }
    
    try:
        agent = GatingFactorAgent(bedrock)
        
        print(f"\nValidating gating factors:")
        print(f"  Max CPU: {test_factors['avgCpuUsageMax']}%")
        print(f"  Max Memory: {test_factors['avgMemoryUsageMax']}%")
        print(f"  Min Disk: {test_factors['avgDiskFreeSpaceMin']}%")
        
        result = agent.validate_and_suggest(test_factors)
        
        print(f"\n✓ Validation complete!")
        print(f"  Valid: {result['is_valid']}")
        print(f"  Risk Level: {result['risk_level']}")
        print(f"  Suggestions:")
        for suggestion in result['suggestions']:
            print(f"    - {suggestion}")
        
        if result.get('recommended_adjustments'):
            print(f"  Recommended Adjustments:")
            for key, value in result['recommended_adjustments'].items():
                print(f"    - {key}: {value}")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("AWS BEDROCK AI AGENTS - TEST SUITE")
    print("=" * 60)
    print()
    
    # Test 1: Connection
    bedrock = test_bedrock_connection()
    if not bedrock:
        print("\n" + "=" * 60)
        print("TESTS ABORTED - Cannot connect to AWS Bedrock")
        print("=" * 60)
        sys.exit(1)
    
    # Run all tests
    results = []
    results.append(("Ring Categorization", test_ring_categorization(bedrock)))
    results.append(("Failure Analysis", test_failure_analysis(bedrock)))
    results.append(("Gating Factor Parsing", test_gating_factor_parsing(bedrock)))
    results.append(("Gating Factor Validation", test_gating_factor_validation(bedrock)))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! AWS Bedrock agents are working correctly.")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
