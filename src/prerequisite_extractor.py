import re
import json
from typing import Dict, List, Set, Tuple

class PrerequisiteExtractor:
    def __init__(self):
        # Common prerequisite patterns
        self.patterns = [
            # "Prerequisites: CSE 100, CSE 101"
            r'Prerequisites?\s*:\s*([^.]+?)(?:\.|$)',
            # "Prereq: MATH 20A-B-C"
            r'Prereq\s*:\s*([^.]+?)(?:\.|$)',
            # "Students must have completed ECE 109"
            r'Students must have completed\s+([^.]+?)(?:\.|$)',
            # "Recommended preparation: CSE 12"
            r'Recommended preparation\s*:\s*([^.]+?)(?:\.|$)',
        ]
        
        # Course code pattern: DEPT ###[A-Z]?
        self.course_pattern = r'\b([A-Z]{2,4})\s+(\d{1,3}[A-Z]*)\b'
        
        # Logical operators
        self.and_words = ['and', '&', ',']
        self.or_words = ['or', 'either']
        
    def extract_course_codes(self, text: str) -> List[str]:
        """Extract all course codes from text"""
        matches = re.findall(self.course_pattern, text)
        return [f"{dept} {num}" for dept, num in matches]
    
    def parse_prerequisite_text(self, text: str) -> Dict[str, List[str]]:
        """Parse prerequisite text and return structured data"""
        result = {
            'prerequisites': [],
            'corequisites': [],
            'recommended': []
        }
        
        # Find prerequisite sections
        for pattern in self.patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Determine type based on keywords
                if 'recommended' in match.lower():
                    result['recommended'].extend(self.extract_course_codes(match))
                elif 'corequisite' in match.lower() or 'concurrent' in match.lower():
                    result['corequisites'].extend(self.extract_course_codes(match))
                else:
                    result['prerequisites'].extend(self.extract_course_codes(match))
        
        # Remove duplicates while preserving order
        for key in result:
            result[key] = list(dict.fromkeys(result[key]))
            
        return result
    
    def extract_all_prerequisites(self, courses: List[Dict]) -> Dict[str, Dict]:
        """Extract prerequisites for all courses"""
        prerequisite_graph = {}
        
        for course in courses:
            course_id = f"{course['subject']} {course['number']}"
            description = course.get('description', '')
            
            if description:
                prereqs = self.parse_prerequisite_text(description)
                if any(prereqs.values()):  # Only add if has prerequisites
                    prerequisite_graph[course_id] = prereqs
        
        return prerequisite_graph
    
    def get_all_course_codes(self, courses: List[Dict]) -> Set[str]:
        """Get all valid course codes from the dataset"""
        return {f"{course['subject']} {course['number']}" for course in courses}
    
    def validate_prerequisites(self, prerequisite_graph: Dict, valid_courses: Set[str]) -> Dict:
        """Validate that prerequisite courses exist in the dataset"""
        validation_report = {
            'valid': {},
            'invalid': {},
            'stats': {}
        }
        
        total_prereqs = 0
        valid_prereqs = 0
        
        for course_id, prereqs in prerequisite_graph.items():
            validation_report['valid'][course_id] = {}
            validation_report['invalid'][course_id] = {}
            
            for prereq_type, prereq_list in prereqs.items():
                valid_list = []
                invalid_list = []
                
                for prereq in prereq_list:
                    total_prereqs += 1
                    if prereq in valid_courses:
                        valid_list.append(prereq)
                        valid_prereqs += 1
                    else:
                        invalid_list.append(prereq)
                
                if valid_list:
                    validation_report['valid'][course_id][prereq_type] = valid_list
                if invalid_list:
                    validation_report['invalid'][course_id][prereq_type] = invalid_list
        
        validation_report['stats'] = {
            'total_prerequisites': total_prereqs,
            'valid_prerequisites': valid_prereqs,
            'invalid_prerequisites': total_prereqs - valid_prereqs,
            'validation_rate': valid_prereqs / total_prereqs if total_prereqs > 0 else 0
        }
        
        return validation_report

def load_courses_json(filepath: str) -> List[Dict]:
    """Load courses from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def save_prerequisites_json(data: Dict, filepath: str):
    """Save prerequisite data to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    # Load course data
    courses = load_courses_json("data/courses.json")
    
    # Extract prerequisites
    extractor = PrerequisiteExtractor()
    prerequisite_graph = extractor.extract_all_prerequisites(courses)
    
    # Validate prerequisites
    valid_courses = extractor.get_all_course_codes(courses)
    validation = extractor.validate_prerequisites(prerequisite_graph, valid_courses)
    
    # Save results
    save_prerequisites_json(prerequisite_graph, "data/prerequisites.json")
    save_prerequisites_json(validation, "data/prerequisite_validation.json")
    
    # Print summary
    stats = validation['stats']
    print(f"Prerequisite Extraction Complete:")
    print(f"- Courses with prerequisites: {len(prerequisite_graph)}")
    print(f"- Total prerequisite relationships: {stats['total_prerequisites']}")
    print(f"- Valid prerequisites: {stats['valid_prerequisites']}")
    print(f"- Invalid prerequisites: {stats['invalid_prerequisites']}")
    print(f"- Validation rate: {stats['validation_rate']:.2%}")