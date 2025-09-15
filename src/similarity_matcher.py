import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from sentence_transformers import SentenceTransformer

class CourseSimilarityMatcher:
    def __init__(self, embeddings_path: str = "data/course_embeddings.json", 
                 courses_path: str = "data/courses.json"):
        """Initialize with pre-computed embeddings and course data"""
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.embeddings = {}
        self.courses = {}
        self.course_texts = {}
        
        # Load data
        self._load_embeddings(embeddings_path)
        self._load_courses(courses_path)
        
    def _load_embeddings(self, filepath: str):
        """Load pre-computed embeddings"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.embeddings = {k: np.array(v) for k, v in data['embeddings'].items()}
        self.course_texts = data['course_texts']
        print(f"Loaded {len(self.embeddings)} embeddings")
    
    def _load_courses(self, filepath: str):
        """Load course metadata"""
        with open(filepath, 'r') as f:
            courses_list = json.load(f)
        
        # Convert to dict for fast lookup
        for course in courses_list:
            course_id = f"{course['subject']} {course['number']}"
            self.courses[course_id] = course
        print(f"Loaded {len(self.courses)} courses")
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
    
    def find_similar_courses(self, course_id: str, top_k: int = 10, 
                           subject_filter: Optional[str] = None) -> List[Dict]:
        """Find most similar courses to a given course"""
        if course_id not in self.embeddings:
            return []
        
        query_embedding = self.embeddings[course_id]
        similarities = []
        
        # Compute similarity with all other courses
        for other_id, other_embedding in self.embeddings.items():
            if other_id == course_id:
                continue
                
            # Apply subject filter if specified
            if subject_filter:
                other_subject = other_id.split()[0]
                if other_subject != subject_filter:
                    continue
            
            similarity = self._cosine_similarity(query_embedding, other_embedding)
            similarities.append((other_id, similarity))
        
        # Sort by similarity and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for course_id_sim, sim_score in similarities[:top_k]:
            course_info = self.courses.get(course_id_sim, {})
            results.append({
                'course_id': course_id_sim,
                'title': course_info.get('title', ''),
                'subject': course_info.get('subject', ''),
                'units': course_info.get('units', 0),
                'similarity': round(sim_score, 3)
            })
        
        return results
    
    def search_courses_by_text(self, query: str, top_k: int = 10,
                              subject_filter: Optional[str] = None) -> List[Dict]:
        """Search courses using natural language query"""
        # Generate embedding for the query
        query_embedding = self.model.encode([query])[0]
        similarities = []
        
        # Compute similarity with all courses
        for course_id, course_embedding in self.embeddings.items():
            # Apply subject filter if specified
            if subject_filter:
                course_subject = course_id.split()[0]
                if course_subject != subject_filter:
                    continue
            
            similarity = self._cosine_similarity(query_embedding, course_embedding)
            similarities.append((course_id, similarity))
        
        # Sort by similarity and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for course_id, sim_score in similarities[:top_k]:
            course_info = self.courses.get(course_id, {})
            results.append({
                'course_id': course_id,
                'title': course_info.get('title', ''),
                'subject': course_info.get('subject', ''),
                'units': course_info.get('units', 0),
                'similarity': round(sim_score, 3),
                'description_snippet': self.course_texts.get(course_id, '')[:100] + '...'
            })
        
        return results
    
    def get_course_recommendations(self, course_id: str, top_k: int = 5) -> Dict:
        """Get comprehensive recommendations for a course"""
        if course_id not in self.courses:
            return {'error': f'Course {course_id} not found'}
        
        course_info = self.courses[course_id]
        similar_courses = self.find_similar_courses(course_id, top_k)
        
        # Get cross-department recommendations
        current_subject = course_info['subject']
        cross_dept = self.find_similar_courses(course_id, top_k=3, 
                                             subject_filter=None)
        cross_dept = [c for c in cross_dept if c['subject'] != current_subject][:3]
        
        return {
            'query_course': {
                'course_id': course_id,
                'title': course_info.get('title', ''),
                'subject': course_info.get('subject', ''),
                'units': course_info.get('units', 0)
            },
            'similar_courses': similar_courses,
            'cross_department': cross_dept,
            'total_found': len(similar_courses)
        }

def main():
    """Test the similarity matcher"""
    print("Initializing Course Similarity Matcher...")
    matcher = CourseSimilarityMatcher()
    
    # Test 1: Find similar courses
    print("\n=== Test 1: Similar Courses ===")
    test_course = "CSE 151A"
    similar = matcher.find_similar_courses(test_course, top_k=5)
    print(f"Courses similar to {test_course}:")
    for course in similar:
        print(f"  {course['course_id']}: {course['title']} (similarity: {course['similarity']})")
    
    # Test 2: Text search
    print("\n=== Test 2: Text Search ===")
    query = "machine learning algorithms"
    results = matcher.search_courses_by_text(query, top_k=5)
    print(f"Search results for '{query}':")
    for course in results:
        print(f"  {course['course_id']}: {course['title']} (similarity: {course['similarity']})")
    
    # Test 3: Comprehensive recommendations
    print("\n=== Test 3: Comprehensive Recommendations ===")
    recommendations = matcher.get_course_recommendations("CSE 158", top_k=3)
    print(f"Recommendations for {recommendations['query_course']['course_id']}:")
    print(f"Similar courses:")
    for course in recommendations['similar_courses']:
        print(f"  {course['course_id']}: {course['title']} ({course['similarity']})")
    print(f"Cross-department:")
    for course in recommendations['cross_department']:
        print(f"  {course['course_id']}: {course['title']} ({course['similarity']})")

if __name__ == "__main__":
    main()