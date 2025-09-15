#!/usr/bin/env python3
"""
CourseRecommendationAPI Demo
Showcases the intelligent course recommendation system
"""

from src.recommendation_api import create_api

def main():
    print("🎓 UCSD Course Recommendation System")
    print("=" * 50)
    
    # Initialize API
    print("Loading course data and embeddings...")
    api = create_api()
    print(f"✓ Loaded {len(api.courses)} courses with semantic embeddings\n")
    
    # Demo 1: Natural Language Search
    print("🔍 DEMO 1: Natural Language Search")
    print("-" * 30)
    queries = ["machine learning with python", "data structures algorithms", "computer graphics"]
    
    for query in queries:
        print(f"Query: '{query}'")
        results = api.search_courses(query, limit=2)
        for r in results:
            print(f"  → {r['subject']} {r['number']}: {r['title']} (score: {r['similarity_score']:.3f})")
        print()
    
    # Demo 2: Smart Recommendations
    print("🎯 DEMO 2: Smart Course Recommendations")
    print("-" * 35)
    completed_courses = ["CSE 12", "CSE 15L", "MATH 20A", "MATH 20B"]
    print(f"Student completed: {', '.join(completed_courses)}")
    print("Looking for: 'advanced programming'")
    
    recs = api.recommend_courses("advanced programming", completed_courses=completed_courses, limit=3)
    print(f"Found {len(recs)} eligible recommendations:")
    for r in recs:
        print(f"  → {r['subject']} {r['number']}: {r['title']} (score: {r['recommendation_score']:.3f})")
    print()
    
    # Demo 3: Learning Path Generation
    print("🛤️  DEMO 3: Learning Path Generation")
    print("-" * 32)
    target = "CSE 151A"
    print(f"Target course: {target}")
    print(f"Student completed: {', '.join(completed_courses[:2])}")
    
    path = api.generate_learning_path(target, completed_courses[:2])
    if path['target_course']:
        print(f"Goal: {path['target_course']['title']}")
        print(f"Prerequisites needed: {len(path['prerequisites_needed'])}")
        print(f"Estimated time: {path['estimated_quarters']} quarters")
        if path['prerequisites_needed']:
            print("Required courses:")
            for p in path['prerequisites_needed'][:3]:  # Show first 3
                print(f"  → {p['subject']} {p['number']}: {p['title']}")
            if len(path['prerequisites_needed']) > 3:
                print(f"  ... and {len(path['prerequisites_needed']) - 3} more")
    print()
    
    # Demo 4: Course Similarity
    print("🔗 DEMO 4: Course Similarity Discovery")
    print("-" * 34)
    course = "CSE 158"
    print(f"Find courses similar to: {course}")
    
    similar = api.find_similar_courses(course, limit=3)
    for s in similar:
        print(f"  → {s['subject']} {s['number']}: {s['title']} (similarity: {s['similarity_score']:.3f})")
    print()
    
    # Demo 5: Cross-Department Discovery
    print("🌐 DEMO 5: Cross-Department Discovery")
    print("-" * 33)
    print("Finding ML courses across all departments:")
    
    ml_courses = api.search_courses("machine learning neural networks", limit=5)
    departments = set()
    for course in ml_courses:
        dept = course['subject']
        if dept not in departments:
            departments.add(dept)
            print(f"  {dept}: {course['subject']} {course['number']} - {course['title']}")
    
    print(f"\n✨ Found ML courses in {len(departments)} different departments!")
    
    print("\n" + "=" * 50)
    print("🚀 CourseRecommendationAPI Demo Complete!")
    print("Ready for integration into web apps, chatbots, or academic advisors.")

if __name__ == "__main__":
    main()