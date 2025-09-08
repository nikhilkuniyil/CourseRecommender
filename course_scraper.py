import requests, bs4, time, csv, json
import re

UNITS_RE   = re.compile(r"\(\s*(\d+)\s+Units?", re.I | re.DOTALL)  # captures 1 in "( 1 Units )" with whitespace
NUM_RE     = re.compile(r"^\d{1,3}[A-Z]*$")                 # 87, 170R, 197DC, 296

BASE     = "https://act.ucsd.edu/scheduleOfClasses/scheduleOfClassesStudentResult.htm"
HEADERS  = {"User-Agent": "Mozilla/5.0 (course-finder bot)"}

def fetch_subject(term, subj):
    payload = {
        "selectedTerm":      term,
        "selectedSubjects":  subj,      # single code or comma-separated list
        "searchType":        "subject",
    }
    r = requests.post(BASE, data=payload, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text                                           # full HTML

def parse_courses(html: str, term: str, subj: str):
    soup = bs4.BeautifulSoup(html, "html.parser")
    rows = []

    # Find all tr elements that contain span.boldtxt
    for tr in soup.find_all("tr"):
        if not tr.find("span", class_="boldtxt"):
            continue
            
        hdr_cells = tr.find_all("td", class_="crsheader")
        if not hdr_cells:
            continue

        # pick the first crsheader whose text looks like a number (87, 170R, 296…)
        number_cell = next((td for td in hdr_cells if NUM_RE.match(td.get_text(strip=True))), None)
        if not number_cell:
            continue
        number = number_cell.get_text(strip=True)

        # Find the title and units in the cell with course info
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
        # Clean up title by removing units pattern and extra parentheses
        title = UNITS_RE.sub("", title_line).strip().rstrip(")")

        rows.append({
            "term":    term,
            "subject": subj,
            "number":  number,
            "title":   title,
            "units":   units,
        })
    return rows

def subject_codes(term):
    url = "https://act.ucsd.edu/scheduleOfClasses/subject-list.json"
    return [s["code"].strip() for s in
            requests.get(url, params={"selectedTerm": term}, headers=HEADERS).json()]

def scrape_term(term):
    all_rows = []
    for subj in subject_codes(term):
        html  = fetch_subject(term, subj)
        all_rows.extend(parse_courses(html, term, subj))
        time.sleep(0.5)                                      # be nice
    return all_rows

# Example usage:
if __name__ == "__main__":
    # Scrape a single subject
    html = fetch_subject("FA25", "MATH")
    courses = parse_courses(html, "FA25", "MATH")
    print(f"Found {len(courses)} MATH courses on page 1")
    
    # Uncomment to scrape all subjects for a term (takes several minutes)
    # all_courses = scrape_term("FA25")
    # print(f"Total courses scraped: {len(all_courses)}")
    
    # Uncomment to save to CSV
    # with open("fa25_courses.csv", "w", newline="") as f:
    #     w = csv.DictWriter(f, fieldnames=["term", "subject", "number", "title", "units"])
    #     w.writeheader()
    #     w.writerows(all_courses)


