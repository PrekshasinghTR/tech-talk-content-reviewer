"""
FastAPI Web Interface for Tech Talk Content Reviewer

Provides REST API endpoints for content evaluation.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn

from content_reviewer import TechTalkContentReviewer, ContentReview


app = FastAPI(
    title="Tech Talk Content Reviewer API",
    description="AI agent that reviews Tech Talk content for quality and completeness",
    version="1.0.0"
)

# Enable CORS for web applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the reviewer
reviewer = TechTalkContentReviewer()


class ContentRequest(BaseModel):
    content: str
    title: Optional[str] = ""
    content_id: Optional[str] = ""


class ContentResponse(BaseModel):
    content_id: str
    title: str
    overall_rating: str
    completeness_score: int
    placeholder_flags: Dict[str, Any]
    key_issues: list
    suggested_fixes: list
    evaluation_timestamp: str


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Tech Talk Content Reviewer API is running",
        "version": "1.0.0",
        "endpoints": {
            "review": "/review - POST content for evaluation",
            "batch_review": "/batch-review - POST multiple contents",
            "health": "/health - API health status"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "content-reviewer"}


@app.post("/review", response_model=ContentResponse)
async def review_content(request: ContentRequest):
    """
    Review a single piece of content.
    
    Args:
        request: ContentRequest with content text and optional metadata
        
    Returns:
        ContentResponse with evaluation results
    """
    try:
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        review = reviewer.review_content(
            content=request.content,
            title=request.title,
            content_id=request.content_id
        )
        
        return ContentResponse(
            content_id=review.content_id,
            title=review.title,
            overall_rating=review.overall_rating,
            completeness_score=review.completeness_score,
            placeholder_flags={
                "has_placeholders": review.placeholder_flags.has_placeholders,
                "details": review.placeholder_flags.details
            },
            key_issues=review.key_issues,
            suggested_fixes=review.suggested_fixes,
            evaluation_timestamp=review.evaluation_timestamp
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing content: {str(e)}")


class BatchContentRequest(BaseModel):
    contents: list[ContentRequest]


class BatchContentResponse(BaseModel):
    results: list[ContentResponse]
    summary: Dict[str, Any]


@app.post("/batch-review", response_model=BatchContentResponse)
async def batch_review_content(request: BatchContentRequest):
    """
    Review multiple pieces of content in batch.
    
    Args:
        request: BatchContentRequest with list of contents
        
    Returns:
        BatchContentResponse with all evaluation results and summary
    """
    try:
        if not request.contents:
            raise HTTPException(status_code=400, detail="No content provided")
        
        results = []
        ratings_count = {"High": 0, "Medium": 0, "Low": 0}
        total_score = 0
        placeholder_count = 0
        
        for content_req in request.contents:
            if not content_req.content.strip():
                continue
                
            review = reviewer.review_content(
                content=content_req.content,
                title=content_req.title,
                content_id=content_req.content_id
            )
            
            result = ContentResponse(
                content_id=review.content_id,
                title=review.title,
                overall_rating=review.overall_rating,
                completeness_score=review.completeness_score,
                placeholder_flags={
                    "has_placeholders": review.placeholder_flags.has_placeholders,
                    "details": review.placeholder_flags.details
                },
                key_issues=review.key_issues,
                suggested_fixes=review.suggested_fixes,
                evaluation_timestamp=review.evaluation_timestamp
            )
            
            results.append(result)
            ratings_count[review.overall_rating] += 1
            total_score += review.completeness_score
            if review.placeholder_flags.has_placeholders:
                placeholder_count += 1
        
        # Calculate summary statistics
        total_items = len(results)
        avg_score = total_score / total_items if total_items > 0 else 0
        
        summary = {
            "total_items": total_items,
            "average_score": round(avg_score, 1),
            "ratings_distribution": ratings_count,
            "items_with_placeholders": placeholder_count,
            "placeholder_percentage": round((placeholder_count / total_items) * 100, 1) if total_items > 0 else 0
        }
        
        return BatchContentResponse(results=results, summary=summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing batch content: {str(e)}")


@app.get("/stats")
async def get_evaluation_stats():
    """
    Get information about evaluation criteria and scoring.
    """
    return {
        "scoring_criteria": {
            "title": "10 points - Clear, descriptive title",
            "overview": "15 points - Introduction or overview section",
            "body_content": "30 points - Detailed content (word count based)",
            "examples": "20 points - Code examples or practical samples",
            "references": "10 points - External links or references",
            "metadata": "10 points - Author, date, version information",
            "formatting": "5 points - Proper markdown/formatting"
        },
        "quality_ratings": {
            "High": "80-100 points, minimal issues",
            "Medium": "50-79 points, some improvements needed",
            "Low": "0-49 points, significant improvements required"
        },
        "placeholder_patterns": [
            "TBD, TODO, Coming soon",
            "Template variables {{var}}",
            "Bracketed placeholders [insert here]",
            "Multiple dots or x's",
            "Draft/WIP indicators"
        ]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)