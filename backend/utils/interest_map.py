"""
utils/interest_map.py
=====================
Keyword-to-interest inference map for the Validation Agent.

When a student mentions an interest in free-form speech rather than using
the canonical category name, this map normalises it to the correct value
from interest_categories in career_data.json.

IMPORTANT: Every value in this map must appear in the interest_categories
array in career_data.json. Modify both together — never one without the other.

This map is POPULATED in Milestone 3 when the Validation Agent is built.
Currently contains example entries to establish the pattern.
"""

from typing import Dict

# ---------------------------------------------------------------------------
# Interest inference map
# ---------------------------------------------------------------------------
# Key   : substring or keyword that appears in student speech (lowercase)
# Value : canonical interest category from career_data.json interest_categories
# ---------------------------------------------------------------------------
INTEREST_KEYWORD_MAP: Dict[str, str] = {
    # Web Development
    "building websites": "Web Development",
    "web apps": "Web Development",
    "web development": "Web Development",
    "website": "Web Development",
    "web design": "Web Development",

    # Full Stack Development
    "full stack": "Full Stack Development",
    "fullstack": "Full Stack Development",
    "mern": "Full Stack Development",
    "mean": "Full Stack Development",

    # Frontend Development
    "frontend": "Frontend Development",
    "front end": "Frontend Development",
    "user interface": "Frontend Development",
    "ui development": "Frontend Development",
    "react developer": "Frontend Development",

    # Backend Development
    "backend": "Backend Development",
    "back end": "Backend Development",
    "server side": "Backend Development",
    "api development": "Backend Development",
    "rest api": "Backend Development",

    # Mobile Development
    "mobile apps": "Mobile Development",
    "android": "Mobile Development",
    "ios": "Mobile Development",
    "flutter": "Mobile Development",
    "react native": "Mobile Development",
    "mobile development": "Mobile Development",

    # Data Science
    "data science": "Data Science",
    "data analysis": "Data Science",
    "analyzing data": "Data Science",
    "working with data": "Data Science",
    "statistics": "Data Science",
    "visualizing data": "Data Science",

    # Data Engineering
    "data engineering": "Data Engineering",
    "data pipelines": "Data Engineering",
    "etl": "Data Engineering",
    "big data": "Data Engineering",

    # Artificial Intelligence
    "artificial intelligence": "Artificial Intelligence",
    "ai": "Artificial Intelligence",
    "building ai": "Artificial Intelligence",
    "intelligent systems": "Artificial Intelligence",

    # Machine Learning
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Machine Learning",
    "neural networks": "Machine Learning",
    "model training": "Machine Learning",
    "prediction": "Machine Learning",

    # Cloud Computing
    "cloud": "Cloud Computing",
    "aws": "Cloud Computing",
    "azure": "Cloud Computing",
    "google cloud": "Cloud Computing",
    "cloud infrastructure": "Cloud Computing",
    "cloud services": "Cloud Computing",

    # DevOps
    "devops": "DevOps",
    "ci/cd": "DevOps",
    "automation": "Automation",
    "deployment": "DevOps",
    "kubernetes": "DevOps",
    "docker": "DevOps",

    # Cybersecurity
    "cybersecurity": "Cybersecurity",
    "security": "Cybersecurity",
    "ethical hacking": "Cybersecurity",
    "penetration testing": "Cybersecurity",
    "hacking": "Cybersecurity",
    "network security": "Cybersecurity",

    # Networking
    "networking": "Networking",
    "computer networks": "Networking",

    # Database Management
    "databases": "Database Management",
    "sql": "Database Management",
    "database design": "Database Management",
    "database management": "Database Management",

    # UI/UX Design
    "ui/ux": "UI/UX Design",
    "ux design": "UI/UX Design",
    "ui design": "UI/UX Design",
    "product design": "Product Design",
    "user experience": "UI/UX Design",
    "wireframing": "UI/UX Design",
    "figma": "UI/UX Design",

    # Problem Solving
    "problem solving": "Problem Solving",
    "algorithms": "Problem Solving",
    "competitive programming": "Problem Solving",
    "coding challenges": "Problem Solving",

    # System Design
    "system design": "System Design",
    "architecture": "System Design",
    "distributed systems": "System Design",

    # Open Source
    "open source": "Open Source",
    "contributing to open source": "Open Source",
    "github": "Open Source",
}


# ---------------------------------------------------------------------------
# Learning style inference map
# ---------------------------------------------------------------------------
# Key   : substring or keyword in student speech (lowercase)
# Value : canonical preferred_learning_style value
# ---------------------------------------------------------------------------
LEARNING_STYLE_KEYWORD_MAP: Dict[str, str] = {
    # Project-based
    "learn by doing": "project-based",
    "learning by doing": "project-based",
    "building projects": "project-based",
    "hands-on": "project-based",
    "hands on": "project-based",
    "practical learning": "project-based",
    "project based": "project-based",
    "building things": "project-based",
    "making things": "project-based",

    # Video-based
    "watching tutorials": "video-based",
    "watch tutorials": "video-based",
    "video tutorials": "video-based",
    "youtube": "video-based",
    "video based": "video-based",
    "online courses": "video-based",
    "coursera": "video-based",
    "udemy": "video-based",
    "lecture videos": "video-based",

    # Reading-based
    "reading documentation": "reading-based",
    "reading books": "reading-based",
    "reading articles": "reading-based",
    "documentation": "reading-based",
    "reading based": "reading-based",
    "textbooks": "reading-based",
    "blog posts": "reading-based",
    "technical articles": "reading-based",

    # Mixed
    "mixed": "mixed",
    "combination": "mixed",
    "all methods": "mixed",
    "everything": "mixed",
    "variety": "mixed",
}


def infer_interests(text: str) -> list:
    """
    Infer interest categories from free-form text using keyword matching.

    Parameters
    ----------
    text : str
        Raw transcript or user input text.

    Returns
    -------
    list
        Deduplicated list of matched canonical interest category strings.
        Returns an empty list if no keywords match.
    """
    text_lower = text.lower()
    matched = []
    seen = set()

    for keyword, category in INTEREST_KEYWORD_MAP.items():
        if keyword in text_lower and category not in seen:
            matched.append(category)
            seen.add(category)

    return matched


def infer_learning_style(text: str) -> str | None:
    """
    Infer preferred_learning_style from free-form text.

    Parameters
    ----------
    text : str
        Raw transcript or user input text.

    Returns
    -------
    str or None
        Canonical learning style value, or None if no match found
        (caller should apply default "mixed").
    """
    text_lower = text.lower()

    for keyword, style in LEARNING_STYLE_KEYWORD_MAP.items():
        if keyword in text_lower:
            return style

    return None
