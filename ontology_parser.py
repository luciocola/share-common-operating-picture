"""
Parse Red River Flood Ontology to extract mission-relevant concepts.
"""

import xml.etree.ElementTree as ET
import os


def parse_red_river_ontology(owl_file_path):
    """
    Parse the Red River Flood ontology OWL file and extract main classes.
    
    Returns:
        List of tuples (label, uri) for main ontology classes
    """
    try:
        tree = ET.parse(owl_file_path)
        root = tree.getroot()
        
        # Define namespaces
        namespaces = {
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
            'owl': 'http://www.w3.org/2002/07/owl#',
            'rrf': 'http://emergency-mgmt.org/red-river-flood#'
        }
        
        concepts = []
        
        # Find all RDF descriptions that are OWL classes
        for desc in root.findall('.//rdf:Description', namespaces):
            # Check if it's a Class
            type_elem = desc.find('rdf:type[@rdf:resource="http://www.w3.org/2002/07/owl#Class"]', namespaces)
            
            if type_elem is not None:
                # Get the label
                label_elem = desc.find('rdfs:label', namespaces)
                about_attr = desc.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
                
                if label_elem is not None and about_attr:
                    label = label_elem.text
                    uri = about_attr.split('#')[-1] if '#' in about_attr else about_attr
                    
                    # Filter out document-specific instances (e.g., PDF files)
                    if not any(ext in label.lower() for ext in ['.pdf', '.doc', '.txt']):
                        concepts.append((label, uri))
        
        # Sort by label
        concepts.sort(key=lambda x: x[0])
        
        return concepts
        
    except Exception as e:
        print(f"Error parsing ontology: {e}")
        return []


def get_mission_concepts():
    """
    Get mission-relevant concepts from the Red River Flood ontology.
    
    Returns:
        List of concept labels suitable for mission selection
    """
    # Path to ontology file
    ontology_path = os.path.join(
        os.path.dirname(__file__),
        '../red_river_flood_ontology/red_river_ontology.owl'
    )
    
    if not os.path.exists(ontology_path):
        # Fallback to predefined concepts if file not found
        return [
            "Riverine Flooding",
            "Emergency Service",
            "Emergency Response",
            "Flood Hazard",
            "Infrastructure Protection",
            "Evacuation",
            "Red River Flood"
        ]
    
    concepts = parse_red_river_ontology(ontology_path)
    
    # Extract just the labels
    labels = [label for label, uri in concepts if label]
    
    # If we got concepts, return them; otherwise use fallback
    if labels:
        return labels
    else:
        return [
            "Riverine Flooding",
            "Emergency Service",
            "Emergency Response",
            "Flood Hazard",
            "Infrastructure Protection",
            "Evacuation",
            "Red River Flood"
        ]


if __name__ == "__main__":
    # Test the parser
    concepts = get_mission_concepts()
    print(f"Found {len(concepts)} mission concepts:")
    for concept in concepts:
        print(f"  - {concept}")
