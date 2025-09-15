from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
from src.recommendation_api import create_api

# Initialize FastAPI app
app = FastAPI(
    title="UCSD Course Recommendation API",
    description="Intelligent course discovery and recommendation system",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize our recommendation API
course_api = create_api()

# Request/Response models
class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10

class RecommendationRequest(BaseModel):
    query: str
    completed_courses: List[str] = []
    filters: Optional[Dict] = None
    limit: Optional[int] = 10

class LearningPathRequest(BaseModel):
    target_course: str
    completed_courses: List[str] = []

class EligibilityRequest(BaseModel):
    course_id: str
    completed_courses: List[str] = []

class SimilarCoursesRequest(BaseModel):
    course_id: str
    limit: Optional[int] = 5

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "UCSD Course Recommendation API",
        "endpoints": {
            "search": "/api/search",
            "recommend": "/api/recommend", 
            "learning_path": "/api/learning-path",
            "eligibility": "/api/eligibility",
            "similar": "/api/similar",
            "course_info": "/api/course/{course_id}"
        }
    }

@app.post("/api/search")
async def search_courses(request: SearchRequest):
    """Natural language course search"""
    try:
        results = course_api.search_courses(request.query, limit=request.limit)
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommend")
async def get_recommendations(request: RecommendationRequest):
    """Smart course recommendations with prerequisite filtering"""
    try:
        recommendations = course_api.recommend_courses(
            request.query,
            completed_courses=request.completed_courses,
            filters=request.filters,
            limit=request.limit
        )
        return {
            "query": request.query,
            "completed_courses": request.completed_courses,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/learning-path")
async def generate_learning_path(request: LearningPathRequest):
    """Generate prerequisite-aware learning path"""
    try:
        path = course_api.generate_learning_path(
            request.target_course,
            completed_courses=request.completed_courses
        )
        return {
            "target_course": request.target_course,
            "completed_courses": request.completed_courses,
            "learning_path": path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/eligibility")
async def check_eligibility(request: EligibilityRequest):
    """Check if student is eligible for a course"""
    try:
        eligibility = course_api.check_eligibility(
            request.course_id,
            request.completed_courses
        )
        return {
            "course_id": request.course_id,
            "completed_courses": request.completed_courses,
            "eligibility": eligibility
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/similar")
async def find_similar_courses(request: SimilarCoursesRequest):
    """Find courses similar to a given course"""
    try:
        similar = course_api.find_similar_courses(
            request.course_id,
            limit=request.limit
        )
        return {
            "course_id": request.course_id,
            "similar_courses": similar,
            "count": len(similar)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/course/{course_id}")
async def get_course_info(course_id: str):
    """Get detailed information about a course"""
    try:
        # Replace URL encoding
        course_id = course_id.replace("%20", " ")
        info = course_api.get_course_info(course_id)
        
        if not info:
            raise HTTPException(status_code=404, detail=f"Course {course_id} not found")
        
        return {
            "course_id": course_id,
            "course_info": info
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_api_stats():
    """Get API statistics"""
    return {
        "total_courses": len(course_api.courses),
        "courses_with_embeddings": len(course_api.embeddings),
        "courses_with_prerequisites": len(course_api.prerequisites),
        "api_version": "1.0.0"
    }

if __name__ == "__main__":
    print("🚀 Starting UCSD Course Recommendation API...")
    print("📚 Loading course data and embeddings...")
    print(f"✅ Ready! {len(course_api.courses)} courses loaded")
    print("🌐 API available at: http://localhost:8000")
    print("📖 API docs at: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)