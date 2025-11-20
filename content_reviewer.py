"""
Tech Talk Content Reviewer Agent

AI agent that evaluates Tech Talk documentation and knowledge articles for quality,
completeness, and identifies areas for improvement.
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum


class QualityRating(Enum):
    HIGH = "High"
    MEDIUM = "Medium" 
    LOW = "Low"


@dataclass
class PlaceholderFlags:
    has_placeholders: bool
    details: str = ""


@dataclass
class ContentReview:
    content_id: str
    title: str
    overall_rating: str
    completeness_score: int
    placeholder_flags: PlaceholderFlags
    key_issues: List[str]
    suggested_fixes: List[str]
    evaluation_timestamp: str


class TechTalkContentReviewer:
    """
    AI agent for reviewing Tech Talk content quality and completeness.
    """
    
    def __init__(self):
        self.placeholder_patterns = [
            r'\b(tbd|todo|coming soon|placeholder|lorem ipsum|insert.*here)\b',
            r'\{\{.*?\}\}',  # Template variables
            r'\[.*?\]',      # Bracketed placeholders
            r'xxx+',         # Multiple x's
            r'\.{3,}',       # Multiple dots
            r'pending|draft|wip|work in progress',
            r'to be.*(?:added|written|completed|updated)',
            r'example.*(?:goes here|needed|tbd)',
        ]
        
        self.quality_indicators = {
            'title': 10,
            'overview': 15,
            'body_content': 30,
            'examples': 20,
            'references': 10,
            'metadata': 10,
            'formatting': 5
        }
    
    def review_content(self, content: str, title: str = "", content_id: str = "") -> ContentReview:
        """
        Main method to review content and return structured evaluation.
        
        Args:
            content: The text content to review
            title: Title of the content (optional)
            content_id: Unique identifier for the content (optional)
            
        Returns:
            ContentReview object with evaluation results
        """
        # Extract title if not provided
        if not title:
            title = self._extract_title(content)
        
        if not content_id:
            content_id = f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Perform analysis
        placeholder_flags = self._detect_placeholders(content)
        completeness_score = self._calculate_completeness_score(content, title)
        overall_rating = self._determine_overall_rating(completeness_score, placeholder_flags)
        key_issues = self._identify_key_issues(content, title, completeness_score)
        suggested_fixes = self._generate_suggestions(key_issues, content)
        
        return ContentReview(
            content_id=content_id,
            title=title,
            overall_rating=overall_rating.value,
            completeness_score=completeness_score,
            placeholder_flags=placeholder_flags,
            key_issues=key_issues,
            suggested_fixes=suggested_fixes,
            evaluation_timestamp=datetime.now().isoformat()
        )
    
    def _extract_title(self, content: str) -> str:
        """Extract title from content if not provided."""
        lines = content.strip().split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and not line.startswith('#'):
                return line[:100]  # Limit title length
            elif line.startswith('# '):
                return line[2:].strip()
        return "Untitled Content"
    
    def _detect_placeholders(self, content: str) -> PlaceholderFlags:
        """Detect placeholder text and dummy content."""
        content_lower = content.lower()
        found_placeholders = []
        
        for pattern in self.placeholder_patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            if matches:
                found_placeholders.extend(matches)
        
        # Check for very short sections
        lines = content.split('\n')
        short_sections = [line for line in lines if 0 < len(line.strip()) < 20]
        
        has_placeholders = bool(found_placeholders or len(short_sections) > len(lines) * 0.3)
        
        details = ""
        if found_placeholders:
            details = f"Found placeholders: {', '.join(set(found_placeholders[:3]))}"
        if len(short_sections) > 5:
            details += f" {len(short_sections)} very short lines detected"
            
        return PlaceholderFlags(has_placeholders=has_placeholders, details=details.strip())
    
    def _calculate_completeness_score(self, content: str, title: str) -> int:
        """Calculate completeness score based on various factors."""
        score = 0
        content_lower = content.lower()
        word_count = len(content.split())
        
        # Title quality (10 points)
        if title and len(title.strip()) > 5:
            score += 10
        elif title:
            score += 5
            
        # Overview/introduction (15 points)
        if any(keyword in content_lower for keyword in ['overview', 'introduction', 'summary']):
            score += 15
        elif word_count > 50:
            score += 10
            
        # Body content depth (30 points)
        if word_count > 500:
            score += 30
        elif word_count > 200:
            score += 20
        elif word_count > 100:
            score += 10
            
        # Examples (20 points)
        example_indicators = ['example', 'for instance', 'code', '```', 'sample']
        if any(indicator in content_lower for indicator in example_indicators):
            score += 20
        elif 'step' in content_lower or 'how to' in content_lower:
            score += 10
            
        # References/links (10 points)
        if 'http' in content or 'www.' in content or '[' in content:
            score += 10
        elif 'see also' in content_lower or 'reference' in content_lower:
            score += 5
            
        # Metadata (10 points)
        metadata_indicators = ['author', 'date', 'updated', 'version', 'owner']
        if any(indicator in content_lower for indicator in metadata_indicators):
            score += 10
            
        # Formatting (5 points)
        if '#' in content or '*' in content or '-' in content:
            score += 5
            
        return min(score, 100)  # Cap at 100
    
    def _determine_overall_rating(self, score: int, placeholder_flags: PlaceholderFlags) -> QualityRating:
        """Determine overall quality rating."""
        if placeholder_flags.has_placeholders:
            score -= 20  # Penalty for placeholders
            
        if score >= 80:
            return QualityRating.HIGH
        elif score >= 50:
            return QualityRating.MEDIUM
        else:
            return QualityRating.LOW
    
    def _identify_key_issues(self, content: str, title: str, score: int) -> List[str]:
        """Identify specific issues with the content."""
        issues = []
        content_lower = content.lower()
        word_count = len(content.split())
        
        if not title or len(title.strip()) < 5:
            issues.append("Missing or inadequate title")
            
        if word_count < 100:
            issues.append("Content too brief - needs more detailed explanation")
            
        if not any(keyword in content_lower for keyword in ['example', 'code', '```']):
            issues.append("Missing practical examples or code samples")
            
        if not any(keyword in content_lower for keyword in ['author', 'date', 'updated', 'owner']):
            issues.append("Missing metadata (author, date, version info)")
            
        if 'http' not in content and 'reference' not in content_lower:
            issues.append("No external references or links provided")
            
        # Check for placeholder patterns
        placeholder_found = False
        for pattern in self.placeholder_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                placeholder_found = True
                break
                
        if placeholder_found:
            issues.append("Contains placeholder text that needs completion")
            
        return issues[:5]  # Limit to 5 issues
    
    def _generate_suggestions(self, issues: List[str], content: str) -> List[str]:
        """Generate specific improvement suggestions."""
        suggestions = []
        
        for issue in issues:
            if "title" in issue.lower():
                suggestions.append("Add a clear, descriptive title that summarizes the content purpose")
            elif "brief" in issue.lower():
                suggestions.append("Expand content with detailed explanations, use cases, and context")
            elif "example" in issue.lower():
                suggestions.append("Include practical code examples with step-by-step explanations")
            elif "metadata" in issue.lower():
                suggestions.append("Add document metadata: author name, creation/update dates, version")
            elif "reference" in issue.lower():
                suggestions.append("Include relevant links to documentation, tools, or related resources")
            elif "placeholder" in issue.lower():
                suggestions.append("Replace all placeholder text with actual content")
                
        # Add general suggestions based on content analysis
        if len(content.split()) < 200:
            suggestions.append("Consider adding troubleshooting section or FAQ")
            
        return suggestions[:5]  # Limit to 5 suggestions
    
    def to_json(self, review: ContentReview) -> str:
        """Convert review to JSON format."""
        return json.dumps(asdict(review), indent=2)
    
    def to_dict(self, review: ContentReview) -> Dict[str, Any]:
        """Convert review to dictionary format."""
        return asdict(review)


# Example usage and testing
if __name__ == "__main__":
    reviewer = TechTalkContentReviewer()
    
    # Test with sample content
    sample_content = """
    # API Integration Guide
    
    This guide covers how to integrate with our API.
    
    ## Overview
    TBD - need to add overview section
    
    ## Authentication
    Use API keys for authentication. Example coming soon.
    
    ## Endpoints
    - GET /users
    - POST /users
    
    More details to be added later.
    """
    
    review = reviewer.review_content(sample_content, "API Integration Guide")
    print(reviewer.to_json(review))