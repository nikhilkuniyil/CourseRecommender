import json
import sys
import os
from typing import Dict, List, Optional, Set

# Handle imports for both module and standalone execution
try:
    from .course_scraper import load_courses_json
    from .similarity_matcher import CourseSimilarityMatcher
    from .prerequisite_extractor import PrerequisiteExtractor
except ImportError:
    # Add parent directory to path for standalone execution
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.course_scraper import load_courses_json
    from src.similarity_matcher import CourseSimilarityMatcher
    from src.prerequisite_extractor import PrerequisiteExtractor

class CourseRecommendationAPI:
    def __init__(self, data_dir: str = "data"):
        """Initialize the recommendation API with all components"""
        self.data_dir = data_dir
        
        # Load data
        self.courses = load_courses_json(f"{data_dir}/courses.json")
        self.embeddings = self._load_embeddings(f"{data_dir}/course_embeddings.json")
        self.prerequisites = self._load_prerequisites(f"{data_dir}/prerequisites.json")
        
        # Initialize components
        self.similarity_matcher = CourseSimilarityMatcher(
            f"{data_dir}/course_embeddings.json", 
            f"{data_dir}/courses.json"
        )
        self.prereq_extractor = PrerequisiteExtractor()
        
        # Create course lookup
        self.course_lookup = {f"{c['subject']} {c['number']}": c for c in self.courses}
        
    def _load_embeddings(self, filepath: str) -> Dict:
        """Load course embeddings"""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def _load_prerequisites(self, filepath: str) -> Dict:
        """Load prerequisite data"""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def recommend_courses(self, query: str, completed_courses: List[str] = None, 
                         filters: Dict = None, limit: int = 10) -> List[Dict]:
        """Smart course recommendations combining semantic search and prerequisites"""
        if completed_courses is None:
            completed_courses = []
        if filters is None:
            filters = {}
        
        # Get semantic matches
        semantic_results = self.similarity_matcher.search_courses_by_text(query, top_k=limit*2)
        
        # Filter by prerequisites and other criteria
        recommendations = []
        for result in semantic_results:
            course_id = result['course_id']  # Already in format "DEPT NUM"
            
            # Skip if already completed
            if course_id in completed_courses:
                continue
                
            # Check prerequisites
            if self._check_prerequisites_met(course_id, completed_courses):
                # Apply filters
                course_data = {
                    'subject': result['subject'],
                    'number': course_id.split()[1],
                    'title': result['title'],
                    'units': result['units']
                }
                if self._passes_filters(course_data, filters):
                    recommendations.append({
                        **course_data,
                        'recommendation_score': result['similarity'],
                        'prerequisites_met': True
                    })
            
            if len(recommendations) >= limit:
                break
        
        return recommendations
    
    def generate_learning_path(self, target_course: str, completed_courses: List[str] = None) -> Dict:
        """Generate prerequisite-aware learning path to target course"""
        if completed_courses is None:
            completed_courses = []
        
        # Get prerequisites for target course
        prereqs = self.prerequisites.get(target_course, {}).get('prerequisites', [])
        
        # Find missing prerequisites
        missing_prereqs = [p for p in prereqs if p not in completed_courses]
        
        # Build learning path
        path = []
        for prereq in missing_prereqs:
            if prereq in self.course_lookup:
                path.append(self.course_lookup[prereq])
        
        # Add target course
        if target_course in self.course_lookup:
            target = self.course_lookup[target_course]
        else:
            target = None
        
        return {
            'target_course': target,
            'prerequisites_needed': path,
            'total_units': sum(c.get('units', 0) for c in path),
            'estimated_quarters': len(path) // 3 + (1 if len(path) % 3 else 0)
        }
    
    def search_courses(self, query: str, limit: int = 10) -> List[Dict]:
        """Natural language course search"""
        results = self.similarity_matcher.search_courses_by_text(query, top_k=limit)
        # Convert to consistent format
        return [{
            'subject': r['course_id'].split()[0],
            'number': r['course_id'].split()[1],
            'title': r['title'],
            'units': r['units'],
            'similarity_score': r['similarity']
        } for r in results]
    
    def check_eligibility(self, course_id: str, completed_courses: List[str]) -> Dict:
        """Check if student is eligible for a course"""
        prereqs = self.prerequisites.get(course_id, {})
        required = prereqs.get('prerequisites', [])
        recommended = prereqs.get('recommended', [])
        
        missing_required = [p for p in required if p not in completed_courses]
        missing_recommended = [p for p in recommended if p not in completed_courses]
        
        return {
            'eligible': len(missing_required) == 0,
            'missing_prerequisites': missing_required,
            'missing_recommended': missing_recommended,
            'prerequisites_met': len(required) - len(missing_required),
            'total_prerequisites': len(required)
        }
    
    def find_similar_courses(self, course_id: str, limit: int = 5) -> List[Dict]:
        """Find courses similar to a given course"""
        results = self.similarity_matcher.find_similar_courses(course_id, top_k=limit)
        # Convert to consistent format
        return [{
            'subject': r['course_id'].split()[0],
            'number': r['course_id'].split()[1],
            'title': r['title'],
            'units': r['units'],
            'similarity_score': r['similarity']
        } for r in results]
    
    def get_course_info(self, course_id: str) -> Optional[Dict]:
        """Get detailed information about a course"""
        course = self.course_lookup.get(course_id)
        if not course:
            return None
        
        # Add prerequisite information
        prereqs = self.prerequisites.get(course_id, {})
        similar = self.find_similar_courses(course_id, limit=3)
        
        return {
            **course,
            'prerequisites': prereqs,
            'similar_courses': similar
        }
    
    def _check_prerequisites_met(self, course_id: str, completed_courses: List[str]) -> bool:
        """Check if prerequisites are met for a course"""
        prereqs = self.prerequisites.get(course_id, {}).get('prerequisites', [])
        return all(p in completed_courses for p in prereqs)
    
    def _passes_filters(self, course: Dict, filters: Dict) -> bool:
        """Check if course passes filter criteria"""
        if 'subject' in filters and course['subject'] not in filters['subject']:
            return False
        if 'min_units' in filters and course.get('units', 0) < filters['min_units']:
            return False
        if 'max_units' in filters and course.get('units', 0) > filters['max_units']:
            return False
        if 'level' in filters:
            course_num = int(''.join(filter(str.isdigit, course['number'])))
            if filters['level'] == 'undergraduate' and course_num >= 200:
                return False
            if filters['level'] == 'graduate' and course_num < 200:
                return False
        return True

# Convenience functions for CLI usage
def create_api(data_dir: str = "data") -> CourseRecommendationAPI:
    """Create and return a CourseRecommendationAPI instance"""
    return CourseRecommendationAPI(data_dir)

if __name__ == "__main__":
    # Example usage
    api = create_api()
    
    # Test semantic search
    print("=== Semantic Search Test ===")
    results = api.search_courses("machine learning algorithms", limit=3)
    for r in results:
        print(f"{r['subject']} {r['number']}: {r['title']} (score: {r['similarity_score']:.3f})")
    
    # Test recommendations
    print("\n=== Recommendation Test ===")
    completed = ["CSE 12", "CSE 15L", "MATH 20A"]
    recs = api.recommend_courses("data structures", completed_courses=completed, limit=3)
    for r in recs:
        print(f"{r['subject']} {r['number']}: {r['title']} (score: {r['recommendation_score']:.3f})")
    
    # Test learning path
    print("\n=== Learning Path Test ===")
    path = api.generate_learning_path("CSE 151A", completed_courses=completed)
    print(f"Target: {path['target_course']['title'] if path['target_course'] else 'Not found'}")
    print(f"Prerequisites needed: {len(path['prerequisites_needed'])}")
    for p in path['prerequisites_needed']:
        print(f"  - {p['subject']} {p['number']}: {p['title']}")