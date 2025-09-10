#!/usr/bin/env python3

from course_scraper import fetch_subject, save_courses_json, load_courses_json, subject_codes
import time
import os

def scrape_priority_subjects():
    """Scrape high-priority CS/Engineering subjects first"""
    priority_subjects = ["CSE", "ECE", "DSC", "MATH", "PHYS", "CHEM", "BENG", "MAE"]
    
    print("=== SCRAPING PRIORITY SUBJECTS WITH DESCRIPTIONS ===")
    for subj in priority_subjects:
        print(f"\nScraping {subj}...")
        try:
            courses = fetch_subject("FA25", subj)
            print(f"Found {len(courses)} courses, adding descriptions...")
            
            # Add descriptions
            from course_scraper import fetch_course_description
            for course in courses:
                course["description"] = fetch_course_description(course["subject"], course["number"])
            
            save_courses_json(courses, f"{subj}_courses.json")
            print(f"✓ Saved {len(courses)} {subj} courses with descriptions")
            time.sleep(3)  # Pause between subjects
        except Exception as e:
            print(f"✗ Error scraping {subj}: {e}")

def scrape_remaining_batch(batch_name, subjects):
    """Scrape a batch of remaining subjects"""
    print(f"\n=== SCRAPING BATCH {batch_name} WITH DESCRIPTIONS ===")
    all_courses = []
    
    for subj in subjects:
        print(f"Scraping {subj}...")
        try:
            courses = fetch_subject("FA25", subj)
            print(f"Found {len(courses)} courses, adding descriptions...")
            
            # Add descriptions
            from course_scraper import fetch_course_description
            for course in courses:
                course["description"] = fetch_course_description(course["subject"], course["number"])
            
            all_courses.extend(courses)
            print(f"✓ Found {len(courses)} {subj} courses with descriptions")
            time.sleep(2)  # Pause between subjects
        except Exception as e:
            print(f"✗ Error scraping {subj}: {e}")
    
    # Save batch
    save_courses_json(all_courses, f"batch_{batch_name}.json")
    print(f"✓ Saved batch {batch_name}: {len(all_courses)} total courses with descriptions")

def combine_all_results():
    """Combine all batch results into final file"""
    print("\n=== COMBINING ALL RESULTS ===")
    
    all_courses = []
    files_to_combine = []
    
    # Priority subjects
    priority_subjects = ["CSE", "ECE", "DSC", "MATH", "PHYS", "CHEM", "BENG", "MAE"]
    for subj in priority_subjects:
        filename = f"{subj}_courses.json"
        if os.path.exists(filename):
            files_to_combine.append(filename)
    
    # Batch files
    for batch in ["A", "B", "C"]:
        filename = f"batch_{batch}.json"
        if os.path.exists(filename):
            files_to_combine.append(filename)
    
    # Load and combine
    for filename in files_to_combine:
        try:
            courses = load_courses_json(filename)
            all_courses.extend(courses)
            print(f"✓ Loaded {len(courses)} courses from {filename}")
        except Exception as e:
            print(f"✗ Error loading {filename}: {e}")
    
    # Save final result
    save_courses_json(all_courses, "complete_courses.json")
    print(f"\n✓ FINAL RESULT: {len(all_courses)} total courses saved to complete_courses.json")

if __name__ == "__main__":
    print("BATCH SCRAPER - Choose an option:")
    print("1. Scrape priority subjects (CSE, ECE, DSC, MATH, PHYS, CHEM, BENG, MAE)")
    print("2. Scrape batch A (A-F subjects)")
    print("3. Scrape batch B (G-M subjects)")  
    print("4. Scrape batch C (N-Z subjects)")
    print("5. Combine all results")
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == "1":
        scrape_priority_subjects()
    
    elif choice == "2":
        all_subjects = subject_codes("FA25")
        priority = ["CSE", "ECE", "DSC", "MATH", "PHYS", "CHEM", "BENG", "MAE"]
        remaining = [s for s in all_subjects if s not in priority]
        batch_a = [s for s in remaining if s[0] <= 'F']
        scrape_remaining_batch("A", batch_a)
    
    elif choice == "3":
        all_subjects = subject_codes("FA25")
        priority = ["CSE", "ECE", "DSC", "MATH", "PHYS", "CHEM", "BENG", "MAE"]
        remaining = [s for s in all_subjects if s not in priority]
        batch_b = [s for s in remaining if 'G' <= s[0] <= 'M']
        scrape_remaining_batch("B", batch_b)
    
    elif choice == "4":
        all_subjects = subject_codes("FA25")
        priority = ["CSE", "ECE", "DSC", "MATH", "PHYS", "CHEM", "BENG", "MAE"]
        remaining = [s for s in all_subjects if s not in priority]
        batch_c = [s for s in remaining if s[0] >= 'N']
        scrape_remaining_batch("C", batch_c)
    
    elif choice == "5":
        combine_all_results()
    
    else:
        print("Invalid choice")