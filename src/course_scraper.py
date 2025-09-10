import requests, bs4, time, csv, json
import re

UNITS_RE   = re.compile(r"\(\s*(\d+)\s+Units?", re.I | re.DOTALL)  # captures 1 in "( 1 Units )" with whitespace
NUM_RE     = re.compile(r"^\d{1,3}[A-Z]*$")                 # 87, 170R, 197DC, 296

BASE     = "https://act.ucsd.edu/scheduleOfClasses/scheduleOfClassesStudentResult.htm"
HEADERS  = {"User-Agent": "Mozilla/5.0 (course-finder bot)"}

def fetch_subject_page(term, subj, page=1):
    """Fetch a specific page for a subject"""
    payload = {
        "selectedTerm":      term,
        "selectedSubjects":  subj,
        "searchType":        "subject",
    }
    if page > 1:
        payload["page"] = str(page)
    
    r = requests.post(BASE, data=payload, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def get_max_pages(term, subj):
    """Find maximum pages by testing until we get no courses"""
    page = 1
    while page <= 20:  # Safety limit
        try:
            html = fetch_subject_page(term, subj, page)
            courses = parse_courses(html, term, subj, False)
            if not courses:  # No courses found, we've gone too far
                return page - 1
            page += 1
        except:
            return page - 1
    return 20  # Fallback

def fetch_subject(term, subj):
    """Fetch all pages for a subject"""
    max_pages = get_max_pages(term, subj)
    
    all_courses = []
    for page in range(1, max_pages + 1):
        html = fetch_subject_page(term, subj, page)
        all_courses.extend(parse_courses(html, term, subj, False))
        time.sleep(0.3)
    
    return all_courses

def fetch_course_description(subject, course_number):
    """Fetch course description from UCSD catalog"""
    # Special case for DSE courses - they're listed under MAS department
    if subject == "DSE":
        url = "https://catalog.ucsd.edu/courses/MAS.html"
        course_id = f"dse{course_number.lower()}"
    else:
        url = f"https://catalog.ucsd.edu/courses/{subject}.html"
        course_id = f"{subject.lower()}{course_number.lower()}"
    
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        soup = bs4.BeautifulSoup(r.text, "html.parser")
        
        # Look for anchor with course id
        anchor = soup.find("a", {"id": course_id})
        
        if anchor:
            # Find the next course-descriptions paragraph
            current = anchor.parent
            while current:
                current = current.find_next_sibling()
                if current and current.name == "p" and "course-descriptions" in current.get("class", []):
                    return current.get_text(strip=True)
        
        return None
        
    except Exception as e:
        return None

def parse_courses(html: str, term: str, subj: str, include_descriptions=False):
    soup = bs4.BeautifulSoup(html, "html.parser")
    rows = []
    seen_courses = set()  # Track unique courses

    # Method 1: Find courses with span.boldtxt (undergraduate courses)
    for tr in soup.find_all("tr"):
        if not tr.find("span", class_="boldtxt"):
            continue
            
        hdr_cells = tr.find_all("td", class_="crsheader")
        if not hdr_cells:
            continue

        number_cell = next((td for td in hdr_cells if NUM_RE.match(td.get_text(strip=True))), None)
        if not number_cell:
            continue
        number = number_cell.get_text(strip=True)

        title_cell = None
        for cell in hdr_cells:
            cell_text = cell.get_text(strip=True)
            if UNITS_RE.search(cell_text):
                title_cell = cell
                break
        
        if not title_cell:
            continue
            
        title_line = title_cell.get_text(" ", strip=True)
        m = UNITS_RE.search(title_line)
        if not m:
            continue
        units = int(m.group(1))
        title = UNITS_RE.sub("", title_line).strip().rstrip(")")

        course_key = f"{subj}-{number}"
        if course_key not in seen_courses:
            course_data = {
                "term":    term,
                "subject": subj,
                "number":  number,
                "title":   title,
                "units":   units,
            }
            
            if include_descriptions:
                description = fetch_course_description(subj, number)
                course_data["description"] = description
            
            rows.append(course_data)
            seen_courses.add(course_key)
    
    # Method 2: Look for graduate courses in course title rows (different structure)
    for tr in soup.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 2:
            continue
            
        # Look for rows that might contain course titles with units
        for cell in cells:
            cell_text = cell.get_text(" ", strip=True)
            if UNITS_RE.search(cell_text) and len(cell_text) > 10:  # Likely a title with units
                # Look for course number in nearby cells or in the title
                course_number = None
                
                # Check if course number is in the title itself
                title_parts = cell_text.split()
                for part in title_parts:
                    if NUM_RE.match(part) and len(part) >= 3 and part.startswith('2'):
                        course_number = part
                        break
                
                # If not found in title, check other cells in the row
                if not course_number:
                    for other_cell in cells:
                        other_text = other_cell.get_text(strip=True)
                        if NUM_RE.match(other_text) and len(other_text) >= 3 and other_text.startswith('2'):
                            course_number = other_text
                            break
                
                if course_number:
                    m = UNITS_RE.search(cell_text)
                    if m:
                        units = int(m.group(1))
                        title = UNITS_RE.sub("", cell_text).strip().rstrip(")")
                        
                        course_key = f"{subj}-{course_number}"
                        if course_key not in seen_courses:
                            course_data = {
                                "term":    term,
                                "subject": subj,
                                "number":  course_number,
                                "title":   title,
                                "units":   units,
                            }
                            
                            if include_descriptions:
                                description = fetch_course_description(subj, course_number)
                                course_data["description"] = description
                            
                            rows.append(course_data)
                            seen_courses.add(course_key)
                        break
    
    return rows

def subject_codes(term):
    url = "https://act.ucsd.edu/scheduleOfClasses/subject-list.json"
    return [s["code"].strip() for s in
            requests.get(url, params={"selectedTerm": term}, headers=HEADERS).json()]

def scrape_term(term, include_descriptions=False):
    all_rows = []
    for subj in subject_codes(term):
        courses = fetch_subject(term, subj)
        if include_descriptions:
            # Add descriptions to courses
            for course in courses:
                course["description"] = fetch_course_description(subj, course["number"])
        all_rows.extend(courses)
        time.sleep(0.5)
    return all_rows

def save_courses_json(courses, filename="courses.json"):
    """Save courses to JSON file"""
    with open(filename, "w") as f:
        json.dump(courses, f, indent=2)

def load_courses_json(filename="courses.json"):
    """Load courses from JSON file"""
    with open(filename, "r") as f:
        return json.load(f)

# Example usage:
if __name__ == "__main__":
    # Scrape all subjects for a term with descriptions (takes several minutes)
    all_courses = scrape_term("FA25", include_descriptions=True)
    print(f"Total courses scraped: {len(all_courses)}")
    
    # Save to JSON
    save_courses_json(all_courses, "courses.json")
    print("Courses saved to courses.json")
    
    # Test loading
    loaded_courses = load_courses_json("courses.json")
    print(f"Loaded {len(loaded_courses)} courses from JSON")
