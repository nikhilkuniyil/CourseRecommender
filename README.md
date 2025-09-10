# CourseRecommender

A production-ready tool that helps UCSD students discover and select courses by providing comprehensive course data scraping and recommendation capabilities.

## Features

- **Complete Course Data**: Scrapes all UCSD courses including undergraduate and graduate levels
- **Comprehensive Information**: Course numbers, titles, units, descriptions, and prerequisites
- **Robust Scraping**: Handles pagination and network issues with retry logic
- **Batch Processing**: Efficient scraping in manageable batches to avoid timeouts
- **Production Ready**: Clean code structure with proper error handling

## Project Structure

```
CourseRecommender/
├── src/
│   ├── course_scraper.py    # Main scraping functionality
│   └── __init__.py
├── data/
│   └── courses.json         # Complete course dataset
├── scripts/
│   ├── batch_scraper.py     # Batch scraping utility
│   └── add_descriptions.py  # Description enhancement
├── tests/
├── requirements.txt         # Dependencies
├── .gitignore
└── README.md
```

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd CourseRecommender

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Using Existing Data

```python
from src.course_scraper import load_courses_json

# Load complete course dataset
courses = load_courses_json("data/courses.json")
print(f"Loaded {len(courses)} courses")

# Search for specific courses
cse_courses = [c for c in courses if c['subject'] == 'CSE']
```

### Scraping New Data

```python
# For batch scraping (recommended)
python scripts/batch_scraper.py

# For individual subjects
from src.course_scraper import fetch_subject
courses = fetch_subject("FA25", "CSE")
```

## Data Format

Each course entry contains:
```json
{
  "term": "FA25",
  "subject": "CSE",
  "number": "253",
  "title": "Fundamentals of Digital Image Processing",
  "units": 4,
  "description": "Course description with prerequisites..."
}
```

## Requirements

- Python 3.6+
- requests>=2.25.0
- beautifulsoup4>=4.9.0

## Roadmap

- [x] Complete course data scraping
- [x] Batch processing for reliability
- [x] Production-ready code structure
- [ ] Course recommendation algorithm
- [ ] Search and filtering API
- [ ] Web interface
- [ ] Topic-based matching

## Contributing

This project follows production standards with proper code organization, error handling, and documentation.