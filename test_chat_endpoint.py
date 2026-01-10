#!/usr/bin/env python3
"""
Test the /chat endpoint at https://sealgeo.servequake.com/chat
API Docs: https://sealgeo.servequake.com/api
OpenAPI: https://sealgeo.servequake.com/api/openapi.json
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sealgeo_agent import SEALGeoAgent


def test_chat_endpoint():
    """Test the chat endpoint with various queries."""
    print("=" * 70)
    print("Testing SEAL Geo Chat Endpoint")
    print("API Docs: https://sealgeo.servequake.com/api")
    print("=" * 70)
    print()
    
    agent = SEALGeoAgent()
    print(f"Base URL: {agent.base_url}")
    print(f"Chat Endpoint: {agent.chat_endpoint}")
    print(f"Timeout: {agent.timeout}s")
    print()
    
    # Test queries
    queries = [
        "What is flood response?",
        "Tell me about emergency evacuation",
        "search and rescue operations"
    ]
    
    for i, query in enumerate(queries, 1):
        print("-" * 70)
        print(f"Test {i}/{len(queries)}: '{query}'")
        print("-" * 70)
        
        try:
            result = agent.query_mission(query)
            
            if result:
                print(f"✓ Success!")
                print(f"  Mission: {result.get('mission', 'N/A')}")
                print(f"  Timestamp: {result.get('timestamp', 'N/A')}")
                print(f"  Results: {len(result.get('results', []))}")
                print(f"  Options: {len(result.get('options', []))}")
                
                # Show first result source
                results = result.get('results', [])
                if results:
                    first = results[0]
                    print(f"\n  First result source: {first.get('source', 'N/A')}")
                    data = first.get('data', {})
                    if isinstance(data, dict):
                        print(f"  Data keys: {list(data.keys())}")
                        if 'response' in data:
                            response = data['response']
                            preview = response[:150] if len(response) > 150 else response
                            print(f"  Response: {preview}...")
            else:
                print("✗ No result returned")
                
        except Exception as e:
            print(f"✗ Exception: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("=" * 70)
    print("Test complete")
    print("=" * 70)


if __name__ == "__main__":
    test_chat_endpoint()
