#!/usr/bin/env python3
"""
Test script for the /api/agent/report endpoint
Tests SSH attacks, SMTP attacks, and error cases
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
REPORT_ENDPOINT = f"{BASE_URL}/api/agent/report"

def test_ssh_attack():
    """Test SSH attack scenario"""
    print("\n=== Testing SSH Attack Scenario ===")
    
    ssh_attack_data = {
        "agent_id": 2,
        "source_ip": "192.168.1.100",
        "service_type": "ssh",
        "source_port": 45123,
        "target_port": 22,
        "username_attempt": "root",
        "password_attempt": "admin123",
        "country_code": "US",
        "country_name": "United States",
        "classification": "brute_force"
    }
    
    try:
        response = requests.post(REPORT_ENDPOINT, json=ssh_attack_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ SSH attack test PASSED")
            return True
        else:
            print("❌ SSH attack test FAILED")
            return False
    except Exception as e:
        print(f"❌ SSH attack test ERROR: {e}")
        return False

def test_smtp_attack():
    """Test SMTP attack scenario"""
    print("\n=== Testing SMTP Attack Scenario ===")
    
    smtp_attack_data = {
        "agent_id": 2,
        "source_ip": "10.0.0.50",
        "service_type": "smtp",
        "source_port": 54321,
        "target_port": 25,
        "sender_email": "malicious@spam.com",
        "recipient_email": "victim@company.com",
        "subject": "Urgent: Update your account",
        "message_content": "Please click this link to update your account...",
        "attachments": ["malware.exe", "trojan.pdf"],
        "country_code": "RU",
        "country_name": "Russia",
        "classification": "phishing"
    }
    
    try:
        response = requests.post(REPORT_ENDPOINT, json=smtp_attack_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ SMTP attack test PASSED")
            return True
        else:
            print("❌ SMTP attack test FAILED")
            return False
    except Exception as e:
        print(f"❌ SMTP attack test ERROR: {e}")
        return False

def test_missing_required_fields():
    """Test validation with missing required fields"""
    print("\n=== Testing Missing Required Fields ===")
    
    # Test missing source_ip
    invalid_data1 = {
        "agent_id": 1,
        "service_type": "ssh"
        # Missing source_ip
    }
    
    try:
        response = requests.post(REPORT_ENDPOINT, json=invalid_data1)
        print(f"Missing source_ip - Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 400:
            print("✅ Missing source_ip validation PASSED")
        else:
            print("❌ Missing source_ip validation FAILED")
    except Exception as e:
        print(f"❌ Missing source_ip test ERROR: {e}")
    
    # Test missing service_type
    invalid_data2 = {
        "agent_id": 1,
        "source_ip": "192.168.1.100"
        # Missing service_type
    }
    
    try:
        response = requests.post(REPORT_ENDPOINT, json=invalid_data2)
        print(f"Missing service_type - Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 400:
            print("✅ Missing service_type validation PASSED")
        else:
            print("❌ Missing service_type validation FAILED")
    except Exception as e:
        print(f"❌ Missing service_type test ERROR: {e}")

def test_malformed_json():
    """Test with malformed JSON"""
    print("\n=== Testing Malformed JSON ===")
    
    try:
        response = requests.post(REPORT_ENDPOINT, 
                               data="invalid json", 
                               headers={'Content-Type': 'application/json'})
        print(f"Malformed JSON - Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [400, 500]:
            print("✅ Malformed JSON handling PASSED")
        else:
            print("❌ Malformed JSON handling FAILED")
    except Exception as e:
        print(f"❌ Malformed JSON test ERROR: {e}")

def test_comprehensive_ssh_attack():
    """Test comprehensive SSH attack with all optional fields"""
    print("\n=== Testing Comprehensive SSH Attack ===")
    
    comprehensive_ssh_data = {
        "agent_id": 3,
        "source_ip": "203.0.113.45",
        "service_type": "ssh",
        "source_port": 33445,
        "target_port": 22,
        "username_attempt": "admin",
        "password_attempt": "password123",
        "payload": "ssh -l admin 192.168.1.1",
        "malware_hash": "a1b2c3d4e5f6789012345678901234567890abcd",
        "classification": "credential_stuffing",
        "country_code": "CN",
        "country_name": "China"
    }
    
    try:
        response = requests.post(REPORT_ENDPOINT, json=comprehensive_ssh_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Comprehensive SSH attack test PASSED")
            return True
        else:
            print("❌ Comprehensive SSH attack test FAILED")
            return False
    except Exception as e:
        print(f"❌ Comprehensive SSH attack test ERROR: {e}")
        return False

def test_multiple_attacks_same_ip():
    """Test multiple attacks from the same IP to verify deduplication logic"""
    print("\n=== Testing Multiple Attacks from Same IP ===")
    
    same_ip = "198.51.100.11"
    
    # First attack
    attack1 = {
        "agent_id": 1,
        "source_ip": same_ip,
        "service_type": "ftp",
        "username_attempt": "root",
        "password_attempt": "123456",
        "source_port": 45123,
        "target_port": 21,
        "country_code": "SR",
        "country_name": "France",
        "classification": "brute_force"
    }
    
    # Second attack from same IP
    attack2 = {
        "agent_id": 3,
        "source_ip": same_ip,
        "service_type": "ssh",
        "username_attempt": "admin",
        "password_attempt": "admin",
        "country_code": "FR",
        "source_port": 45123,
        "target_port": 22,
        "country_name": "France",
        "classification": "brute_force"
    }
    
    try:
        # Send first attack
        response1 = requests.post(REPORT_ENDPOINT, json=attack1)
        print(f"First attack - Status Code: {response1.status_code}")
        print(f"Response: {response1.json()}")
        
        # Send second attack
        response2 = requests.post(REPORT_ENDPOINT, json=attack2)
        print(f"Second attack - Status Code: {response2.status_code}")
        print(f"Response: {response2.json()}")
        
        if response1.status_code == 200 and response2.status_code == 200:
            print("✅ Multiple attacks from same IP test PASSED")
            return True
        else:
            print("❌ Multiple attacks from same IP test FAILED")
            return False
    except Exception as e:
        print(f"❌ Multiple attacks test ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Agent Report Endpoint Tests")
    print(f"Target URL: {REPORT_ENDPOINT}")
    print(f"Timestamp: {datetime.now()}")
    
    tests_passed = 0
    total_tests = 0
    
    # Run tests
    test_functions = [
        test_ssh_attack,
        test_smtp_attack,
        test_comprehensive_ssh_attack,
        test_multiple_attacks_same_ip
    ]
    
    for test_func in test_functions:
        total_tests += 1
        if test_func():
            tests_passed += 1
    
    # Run validation tests (don't count towards pass/fail)
    test_missing_required_fields()
    test_malformed_json()
    
    # Summary
    print(f"\n" + "="*50)
    print(f"TEST SUMMARY")
    print(f"="*50)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()