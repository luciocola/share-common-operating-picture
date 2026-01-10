"""
SEAL Geo Query Agent - Queries https://sealgeo.servequake.com/chat for RAG-based mission data
API Documentation: https://sealgeo.servequake.com/api (Swagger UI)
OpenAPI Spec: https://sealgeo.servequake.com/api/openapi.json
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from typing import List, Dict, Optional


class SEALGeoAgent:
    """Agent for querying SEAL Geo RAG API with mission text."""
    
    def __init__(self, base_url="https://sealgeo.servequake.com"):
        """
        Initialize SEAL Geo agent.
        
        Args:
            base_url: Base URL for SEAL Geo RAG service
        """
        self.base_url = base_url
        self.chat_endpoint = f"{base_url}/chat"  # Chat endpoint: /chat (not /api/chat)
        self.api_url = f"{base_url}/api"  # API docs/spec: /api
        self.timeout = 30  # Increased timeout for RAG processing
        
    def query_mission(self, mission_text: str) -> Optional[Dict]:
        """
        Query SEAL Geo for mission-related data.
        
        Args:
            mission_text: Mission description or identifier
            
        Returns:
            Dictionary with query results or None if failed
        """
        if not mission_text or not mission_text.strip():
            return None
        
        print(f"\n[SEAL Geo Agent] Starting query for mission: '{mission_text}'")
        
        try:
            # Try multiple potential API endpoints
            results = []
            
            # Try chatbot endpoint
            print("[SEAL Geo Agent] Trying chatbot endpoint...")
            chatbot_result = self._query_chatbot(mission_text)
            if chatbot_result:
                print(f"[SEAL Geo Agent] Chatbot returned: {chatbot_result}")
                results.append({
                    "source": "chatbot",
                    "data": chatbot_result
                })
            
            # Try search endpoint
            print("[SEAL Geo Agent] Trying search endpoint...")
            search_result = self._query_search(mission_text)
            if search_result:
                print(f"[SEAL Geo Agent] Search returned: {search_result}")
                results.append({
                    "source": "search",
                    "data": search_result
                })
            
            # Try STAC catalog endpoint
            print("[SEAL Geo Agent] Trying STAC catalog endpoint...")
            stac_result = self._query_stac_catalog(mission_text)
            if stac_result:
                print(f"[SEAL Geo Agent] STAC returned: {stac_result}")
                results.append({
                    "source": "stac_catalog",
                    "data": stac_result
                })
            
            # If no real results, create a mock result for testing
            if not results:
                print("[SEAL Geo Agent] No API results, creating mock data for testing")
                results = self._create_mock_results(mission_text)
            
            if results:
                final_result = {
                    "mission": mission_text,
                    "timestamp": self._get_timestamp(),
                    "results": results,
                    "options": self._extract_options(results)
                }
                print(f"[SEAL Geo Agent] Final result has {len(final_result['options'])} options")
                return final_result
            
            print("[SEAL Geo Agent] No results available")
            return None
            
        except Exception as e:
            print(f"[SEAL Geo Agent] Error querying SEAL Geo: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _query_chatbot(self, query: str) -> Optional[Dict]:
        """Query the RAG chatbot endpoint at sealgeo.servequake.com/chat."""
        try:
            # Use the documented /chat endpoint
            endpoint = self.chat_endpoint
            
            print(f"[SEAL Geo RAG] Querying chat endpoint: {endpoint}")
            print(f"[SEAL Geo RAG] Query: {query}")
            
            # Prepare request data - the API expects 'question' parameter (not 'query')
            request_data = {
                "question": query
            }
            
            data = json.dumps(request_data).encode('utf-8')
            print(f"[SEAL Geo RAG] Request payload: {request_data}")
            
            try:
                    
                req = urllib.request.Request(
                    endpoint,
                    data=data,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'QGIS ShareCOP Plugin/1.0',
                        'Accept': 'application/json'
                    },
                    method='POST'
                )
                
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    if response.status == 200:
                        result = json.loads(response.read().decode('utf-8'))
                        print(f"[SEAL Geo RAG] ✓ Success! Got response")
                        print(f"[SEAL Geo RAG] Response keys: {list(result.keys())}")
                        return result
                    else:
                        print(f"[SEAL Geo RAG] Unexpected status: {response.status}")
                        return None
                        
            except urllib.error.HTTPError as e:
                print(f"[SEAL Geo RAG] ✗ HTTP Error {e.code}: {e.reason}")
                try:
                    error_body = e.read().decode('utf-8')
                    print(f"[SEAL Geo RAG] Error details: {error_body[:500]}")
                except:
                    pass
            except urllib.error.URLError as e:
                print(f"[SEAL Geo RAG] ✗ URL Error: {e.reason}")
            except Exception as e:
                print(f"[SEAL Geo RAG] ✗ Error: {str(e)}")
                import traceback
                traceback.print_exc()
                    
        except Exception as e:
            print(f"[SEAL Geo] Chatbot query failed: {e}")
        
        return None
    
    def _query_search(self, query: str) -> Optional[Dict]:
        """Query search endpoint."""
        try:
            # Encode query for URL
            encoded_query = urllib.parse.quote(query)
            
            # Try common search patterns
            endpoints = [
                f"{self.api_url}/search?q={encoded_query}",
                f"{self.api_url}/missions?search={encoded_query}",
                f"{self.base_url}/api/search?query={encoded_query}"
            ]
            
            print(f"[SEAL Geo] Trying search endpoints for: {query}")
            
            for endpoint in endpoints:
                try:
                    print(f"[SEAL Geo] Search trying: {endpoint}")
                    req = urllib.request.Request(
                        endpoint,
                        headers={
                            'User-Agent': 'QGIS ShareCOP Plugin/1.0',
                            'Accept': 'application/json'
                        }
                    )
                    
                    with urllib.request.urlopen(req, timeout=self.timeout) as response:
                        if response.status == 200:
                            result = json.loads(response.read().decode('utf-8'))
                            print(f"[SEAL Geo] Search success at: {endpoint}")
                            return result
                            
                except urllib.error.HTTPError as e:
                    print(f"[SEAL Geo] Search HTTP Error {e.code} at {endpoint}")
                    continue
                except urllib.error.URLError as e:
                    print(f"[SEAL Geo] Search URL Error at {endpoint}: {e.reason}")
                    continue
                except Exception as e:
                    print(f"[SEAL Geo] Search error at {endpoint}: {str(e)}")
                    continue
            
            print("[SEAL Geo] All search endpoints failed")
                    
        except Exception as e:
            print(f"Search query failed: {e}")
        
        return None
    
    def _query_stac_catalog(self, query: str) -> Optional[Dict]:
        """Query STAC catalog endpoint."""
        try:
            # STAC API search patterns
            endpoints = [
                f"{self.api_url}/stac/search",
                f"{self.base_url}/stac/search"
            ]
            
            # STAC search query
            search_query = {
                "query": {
                    "cop:mission": {"eq": query}
                },
                "limit": 10
            }
            
            print(f"[SEAL Geo] Trying STAC endpoints for: {query}")
            
            for endpoint in endpoints:
                try:
                    print(f"[SEAL Geo] STAC trying: {endpoint}")
                    data = json.dumps(search_query).encode('utf-8')
                    
                    req = urllib.request.Request(
                        endpoint,
                        data=data,
                        headers={
                            'Content-Type': 'application/json',
                            'User-Agent': 'QGIS ShareCOP Plugin/1.0',
                            'Accept': 'application/json'
                        },
                        method='POST'
                    )
                    
                    with urllib.request.urlopen(req, timeout=self.timeout) as response:
                        if response.status == 200:
                            result = json.loads(response.read().decode('utf-8'))
                            print(f"[SEAL Geo] STAC success at: {endpoint}")
                            return result
                            
                except urllib.error.HTTPError as e:
                    print(f"[SEAL Geo] STAC HTTP Error {e.code} at {endpoint}")
                    continue
                except urllib.error.URLError as e:
                    print(f"[SEAL Geo] STAC URL Error at {endpoint}: {e.reason}")
                    continue
                except Exception as e:
                    print(f"[SEAL Geo] STAC error at {endpoint}: {str(e)}")
                    continue
            
            print("[SEAL Geo] All STAC endpoints failed")
                    
        except Exception as e:
            print(f"STAC catalog query failed: {e}")
        
        return None
    
    def _extract_options(self, results: List[Dict]) -> List[Dict]:
        """
        Extract actionable options from query results.
        
        Args:
            results: List of result dictionaries
            
        Returns:
            List of option dictionaries with standardized format
        """
        options = []
        
        for result in results:
            source = result.get("source", "unknown")
            data = result.get("data", {})
            
            if source == "chatbot" or source == "mock":
                # Extract from chatbot/mock response
                if isinstance(data, dict):
                    # Handle 'answer' field from RAG API
                    if "answer" in data:
                        options.append({
                            "type": "chatbot_response",
                            "title": "RAG Assistant Response",
                            "content": data["answer"],
                            "source": source
                        })
                    # Handle legacy 'response' field
                    if "response" in data:
                        options.append({
                            "type": "chatbot_response",
                            "title": "AI Assistant Response",
                            "content": data["response"],
                            "source": source
                        })
                    if "suggestions" in data:
                        for suggestion in data["suggestions"]:
                            options.append({
                                "type": "suggestion",
                                "title": suggestion.get("title", "Suggestion"),
                                "content": suggestion.get("content", ""),
                                "source": source
                            })
                    if "items" in data:
                        for item in data["items"]:
                            options.append({
                                "type": "reference",
                                "title": item.get("title", "Reference"),
                                "description": item.get("description", ""),
                                "url": item.get("url", ""),
                                "source": source
                            })
            
            elif source == "search":
                # Extract from search results
                if isinstance(data, dict):
                    items = data.get("items", data.get("results", []))
                    for item in items:
                        options.append({
                            "type": "search_result",
                            "title": item.get("title", item.get("name", "Result")),
                            "description": item.get("description", ""),
                            "url": item.get("url", ""),
                            "source": source
                        })
            
            elif source == "stac_catalog":
                # Extract from STAC features
                if isinstance(data, dict):
                    features = data.get("features", [])
                    for feature in features:
                        properties = feature.get("properties", {})
                        options.append({
                            "type": "stac_item",
                            "title": properties.get("title", feature.get("id", "Item")),
                            "mission": properties.get("cop:mission", ""),
                            "classification": properties.get("cop:classification", ""),
                            "datetime": properties.get("datetime", ""),
                            "bbox": feature.get("bbox", []),
                            "source": source
                        })
        
        return options
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    def _create_mock_results(self, mission_text: str) -> List[Dict]:
        """Create mock results for testing when API is unavailable.
        
        Args:
            mission_text: Mission text to base mock data on
            
        Returns:
            List of mock result dictionaries
        """
        mock_data = {
            "source": "mock",
            "data": {
                "response": f"Mock response for mission: {mission_text}",
                "suggestions": [
                    {
                        "title": f"Related Mission: {mission_text} Protocol",
                        "content": "Standard operating procedures and guidelines for this type of mission."
                    },
                    {
                        "title": f"Previous {mission_text} Operations",
                        "content": "Historical data and lessons learned from similar missions."
                    },
                    {
                        "title": "Mission Planning Resources",
                        "content": "Templates and checklists for mission preparation."
                    }
                ],
                "items": [
                    {
                        "title": f"{mission_text} - Reference Data",
                        "description": "Geospatial datasets relevant to this mission type",
                        "url": "https://sealgeo.webgis1.com/demo/"
                    },
                    {
                        "title": "Common Operating Picture Guidelines",
                        "description": "Best practices for COP creation and sharing",
                        "url": "https://sealgeo.webgis1.com/demo/"
                    }
                ]
            }
        }
        
        return [mock_data]
    
    def get_mission_suggestions(self, partial_text: str, limit: int = 10) -> List[str]:
        """
        Get mission suggestions based on partial text.
        
        Args:
            partial_text: Partial mission text
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested mission names
        """
        try:
            result = self.query_mission(partial_text)
            if result and result.get("options"):
                suggestions = []
                for option in result["options"][:limit]:
                    if option.get("mission"):
                        suggestions.append(option["mission"])
                    elif option.get("title"):
                        suggestions.append(option["title"])
                return suggestions
        except Exception as e:
            print(f"Error getting suggestions: {e}")
        
        return []
