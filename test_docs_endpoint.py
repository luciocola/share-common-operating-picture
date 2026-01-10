#!/usr/bin/env python3
"""
Test /docs and other common API endpoints.
"""

import urllib.request
import urllib.error

def test_endpoint(url, method='GET', timeout=10):
    """Test an endpoint and show response."""
    print(f"\n{'='*70}")
    print(f"Testing: {url}")
    print(f"{'='*70}")
    
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Accept': '*/*'
            },
            method=method
        )
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            content_type = response.headers.get('Content-Type', 'unknown')
            body = response.read().decode('utf-8')
            
            print(f"✓ Status: {status}")
            print(f"  Content-Type: {content_type}")
            print(f"  Body length: {len(body)} bytes")
            
            # Show first 500 chars of body
            if body:
                print(f"\n  Response preview:")
                print("  " + "-" * 68)
                preview = body[:500]
                for line in preview.split('\n')[:20]:
                    print(f"  {line}")
                if len(body) > 500:
                    print(f"  ... ({len(body) - 500} more bytes)")
            
            return True
            
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP Error: {e.code} {e.reason}")
        try:
            body = e.read().decode('utf-8')
            if body:
                print(f"  Error body: {body[:200]}")
        except:
            pass
        return False
    except urllib.error.URLError as e:
        print(f"✗ URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

# Test various endpoints
base_url = "https://sealgeo.servequake.com"

endpoints = [
    f"{base_url}/docs",
    f"{base_url}/api/docs",
    f"{base_url}/swagger",
    f"{base_url}/api/swagger",
    f"{base_url}/openapi.json",
    f"{base_url}/api/openapi.json",
    f"{base_url}/redoc",
    f"{base_url}/api",
    f"{base_url}/api/v1",
    f"{base_url}",
]

print("Testing sealgeo.servequake.com API endpoints...")
print("This will check for documentation and API info.")

for endpoint in endpoints:
    test_endpoint(endpoint)

print("\n" + "="*70)
print("Test complete")
print("="*70)
