import json
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Tuple
import pickle

class CourseEmbeddingGenerator:
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        """Initialize with a pre-trained sentence transformer model"""
        self.model = SentenceTransformer(model_name)
        self.embeddings = {}
        self.course_texts = {}
        
    def prepare_course_text(self, course: Dict) -> str:
        """Combine course title and description for richer context"""
        title = course.get('title', '') or ''
        description = course.get('description', '') or ''
        
        title = title.strip()
        description = description.strip()
        
        # Create rich text representation
        if description:
            return f"{title}. {description}"
        return title
    
    def generate_embeddings(self, courses: List[Dict]) -> Dict[str, np.ndarray]:
        """Generate embeddings for all courses"""
        print(f"Generating embeddings for {len(courses)} courses...")
        
        course_ids = []
        texts = []
        
        # Prepare all course texts
        for course in courses:
            course_id = f"{course['subject']} {course['number']}"
            course_text = self.prepare_course_text(course)
            
            course_ids.append(course_id)
            texts.append(course_text)
            self.course_texts[course_id] = course_text
        
        # Generate embeddings in batch (more efficient)
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Store embeddings
        for course_id, embedding in zip(course_ids, embeddings):
            self.embeddings[course_id] = embedding
            
        print(f"Generated {len(self.embeddings)} embeddings")
        return self.embeddings
    
    def save_embeddings(self, filepath: str):
        """Save embeddings and metadata to file"""
        data = {
            'embeddings': {k: v.tolist() for k, v in self.embeddings.items()},
            'course_texts': self.course_texts,
            'model_name': self.model.get_sentence_embedding_dimension(),
            'embedding_dim': len(next(iter(self.embeddings.values())))
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved embeddings to {filepath}")
    
    def load_embeddings(self, filepath: str):
        """Load embeddings from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.embeddings = {k: np.array(v) for k, v in data['embeddings'].items()}
        self.course_texts = data['course_texts']
        print(f"Loaded {len(self.embeddings)} embeddings")
    
    def get_embedding(self, course_id: str) -> np.ndarray:
        """Get embedding for a specific course"""
        return self.embeddings.get(course_id)
    
    def compute_similarity(self, course1_id: str, course2_id: str) -> float:
        """Compute cosine similarity between two courses"""
        emb1 = self.get_embedding(course1_id)
        emb2 = self.get_embedding(course2_id)
        
        if emb1 is None or emb2 is None:
            return 0.0
        
        # Cosine similarity
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)

def load_courses_json(filepath: str) -> List[Dict]:
    """Load courses from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)

if __name__ == "__main__":
    # Load course data
    courses = load_courses_json("data/courses.json")
    
    # Generate embeddings
    generator = CourseEmbeddingGenerator()
    embeddings = generator.generate_embeddings(courses)
    
    # Save embeddings
    generator.save_embeddings("data/course_embeddings.json")
    
    # Test similarity
    cse_courses = [c for c in courses if c['subject'] == 'CSE'][:5]
    print("\nSample similarity test:")
    for i, course1 in enumerate(cse_courses):
        for course2 in cse_courses[i+1:]:
            id1 = f"{course1['subject']} {course1['number']}"
            id2 = f"{course2['subject']} {course2['number']}"
            similarity = generator.compute_similarity(id1, id2)
            print(f"{id1} <-> {id2}: {similarity:.3f}")
            if i >= 2:  # Limit output
                break
        if i >= 2:
            break