#!/usr/bin/env python3
"""
Test script to verify SEAL Geo RAG API connection.
Run this independently to test the API without QGIS.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from sealgeo_agent import SEALGeoAgent


def test_rag_api():
    """Test the RAG API connection with a simple query."""
    print("=" * 70)
    print("Testing SEAL Geo RAG API Connection")
    print("=" * 70)
    print()
    
    # Initialize agent
    print("Initializing SEALGeoAgent...")
    agent = SEALGeoAgent()
    print(f"Base URL: {agent.base_url}")
    print(f"RAG API URL: {agent.rag_api_url}")
    print(f"Timeout: {agent.timeout}s")
    print()
    
    # Test queries
    test_queries = [
        "flood response",
        "search and rescue",
        "emergency evacuation"
    ]
    
    for query in test_queries:
        print("-" * 70)
        print(f"Testing query: '{query}'")
        print("-" * 70)
        
        try:
            result = agent.query_mission(query)
            
            if result:
                print("✓ Query successful!")
                print(f"  Results: {len(result.get('results', []))} sources")
                print(f"  Options: {len(result.get('options', []))} options")
                print(f"  Timestamp: {result.get('timestamp', 'N/A')}")
                
                # Show first option if available
                options = result.get('options', [])
                if options:
                    first = options[0]
                    print(f"\n  First option:")
                    print(f"    Type: {first.get('type', 'N/A')}")
                    print(f"    Title: {first.get('title', 'N/A')}")
                    content = first.get('content', '')
                    if content:
                        preview = content[:100] + "..." if len(content) > 100 else content
                        print(f"    Content preview: {preview}")
            else:
                print("✗ Query returned no results")
                print("  This may indicate:")
                print("  - API endpoint is not accessible")
                print("  - Authentication required")
                print("  - Service temporarily unavailable")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("=" * 70)
    print("Test complete")
    print("=" * 70)


if __name__ == "__main__":
    test_rag_api()
