import json
from course_scraper import load_courses_json

def load_course_database(filename="courses.json"):
    """Load course database from JSON file"""
    return load_courses_json(filename)

def search_courses(courses, topics):
    """Search and rank courses based on topic relevance"""
    scored_courses = []
    
    for course in courses:
        score = 0
        searchable_text = f"{course['title']} {course.get('description', '')}".lower()
        
        # Score based on topic matches
        for topic in topics:
            topic_lower = topic.lower()
            if topic_lower in searchable_text:
                score += searchable_text.count(topic_lower)
        
        if score > 0:
            scored_courses.append((score, course))
    
    # Sort by score (highest first)
    scored_courses.sort(key=lambda x: x[0], reverse=True)
    return [course for score, course in scored_courses]

def recommend_courses(topics, filename="courses.json"):
    """Main function to get course recommendations"""
    courses = load_course_database(filename)
    return search_courses(courses, topics)

if __name__ == "__main__":
    # Example usage
    topics = ["machine learning", "algorithms", "data"]
    recommendations = recommend_courses(topics)
    
    print(f"Top 10 courses for topics: {topics}")
    for i, course in enumerate(recommendations[:10], 1):
        print(f"{i}. {course['subject']} {course['number']}: {course['title']} ({course['units']} units)")