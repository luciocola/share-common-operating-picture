#!/usr/bin/env python3
"""
Quick diagnostic to check sealgeo.servequake.com API availability.
"""

import urllib.request
import socket

def check_endpoint(url, method='GET', timeout=5):
    """Check if an endpoint is accessible."""
    print(f"Checking: {url}")
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json'
            },
            method=method
        )
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            print(f"  ✓ Status: {response.status}")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
            return True
            
    except urllib.error.HTTPError as e:
        print(f"  ✗ HTTP Error: {e.code} {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"  ✗ URL Error: {e.reason}")
        return False
    except socket.timeout:
        print(f"  ✗ Timeout")
        return False
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False

print("=" * 70)
print("Checking sealgeo.servequake.com endpoints")
print("=" * 70)
print()

# Check base URL
print("Base URLs:")
check_endpoint("https://sealgeo.servequake.com")
check_endpoint("http://sealgeo.servequake.com")
print()

# Check API endpoints
print("API Endpoints:")
endpoints = [
    "https://sealgeo.servequake.com/api",
    "https://sealgeo.servequake.com/api/v1",
    "https://sealgeo.servequake.com/api/rag",
    "https://sealgeo.servequake.com/api/chat",
    "https://sealgeo.servequake.com/rag",
    "https://sealgeo.servequake.com/chat",
]

for endpoint in endpoints:
    check_endpoint(endpoint)
    print()

print("=" * 70)
