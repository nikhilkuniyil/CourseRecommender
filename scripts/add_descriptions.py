#!/usr/bin/env python3

from course_scraper import fetch_course_description, load_courses_json, save_courses_json
import os

def add_descriptions_to_existing():
    """Add descriptions to existing priority subject files"""
    
    priority_subjects = ["CSE", "ECE", "DSC", "MATH", "PHYS", "CHEM", "BENG", "MAE"]
    
    for subj in priority_subjects:
        filename = f"{subj}_courses.json"
        if os.path.exists(filename):
            print(f"Adding descriptions to {filename}...")
            
            # Load existing courses
            courses = load_courses_json(filename)
            
            # Add descriptions
            for course in courses:
                if "description" not in course or course["description"] is None:
                    course["description"] = fetch_course_description(course["subject"], course["number"])
            
            # Save updated file
            save_courses_json(courses, filename)
            print(f"✓ Updated {len(courses)} courses in {filename}")
        else:
            print(f"✗ {filename} not found")

if __name__ == "__main__":
    add_descriptions_to_existing()