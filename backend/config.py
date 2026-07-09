import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────
SECRET_KEY          = os.getenv("SECRET_KEY", "change-me-in-production-please")
MOODLE_BASE_URL     = os.getenv("MOODLE_BASE_URL", "https://your-moodle.example.com")
MOODLE_TOKEN        = os.getenv("MOODLE_TOKEN", "")

# ── Storage ───────────────────────────────────────────────
UPLOAD_DIR          = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── JWT ───────────────────────────────────────────────────
JWT_ALGORITHM       = "HS256"
JWT_EXPIRE_MINUTES  = 480   # 8-hour session

# ── 10 Pre-configured Classrooms ─────────────────────────
CLASSROOMS = [
    {
        "id": "cls-101",
        "name": "Introduction to AI",
        "slug": "intro-ai",
        "subject": "Computer Science",
        "password": None,
        "owner": None,
        "description": "Foundations of artificial intelligence, machine learning basics, and neural networks.",
        "color": "#6366f1",
        "max_participants": 1000,
    },
    {
        "id": "cls-102",
        "name": "Advanced Mathematics",
        "slug": "adv-math",
        "subject": "Mathematics",
        "password": None,
        "owner": None,
        "description": "Calculus, linear algebra, and discrete mathematics for engineering students.",
        "color": "#22d3ee",
        "max_participants": 1000,
    },
    {
        "id": "cls-103",
        "name": "Web Development",
        "slug": "web-dev",
        "subject": "Programming",
        "password": None,
        "owner": None,
        "description": "Full-stack web development using React, Node.js, and modern frameworks.",
        "color": "#f59e0b",
        "max_participants": 1000,
    },
    {
        "id": "cls-104",
        "name": "Data Science & Analytics",
        "slug": "data-science",
        "subject": "Data Science",
        "password": None,
        "owner": None,
        "description": "Statistical analysis, data visualization, and predictive modeling with Python.",
        "color": "#10b981",
        "max_participants": 1000,
    },
    {
        "id": "cls-105",
        "name": "Cybersecurity Essentials",
        "slug": "cybersec",
        "subject": "Security",
        "password": None,
        "owner": None,
        "description": "Network security, ethical hacking, cryptography, and threat analysis.",
        "color": "#ef4444",
        "max_participants": 1000,
    },
    {
        "id": "cls-106",
        "name": "Cloud Computing",
        "slug": "cloud",
        "subject": "Infrastructure",
        "password": None,
        "owner": None,
        "description": "AWS, Azure, GCP architecture, serverless computing, and DevOps practices.",
        "color": "#8b5cf6",
        "max_participants": 1000,
    },
    {
        "id": "cls-107",
        "name": "Digital Marketing",
        "slug": "digital-mktg",
        "subject": "Marketing",
        "password": None,
        "owner": None,
        "description": "SEO, social media strategy, analytics, and growth marketing techniques.",
        "color": "#ec4899",
        "max_participants": 1000,
    },
    {
        "id": "cls-108",
        "name": "Business Management",
        "slug": "biz-mgmt",
        "subject": "Business",
        "password": None,
        "owner": None,
        "description": "Organizational behavior, strategic planning, and leadership principles.",
        "color": "#f97316",
        "max_participants": 1000,
    },
    {
        "id": "cls-109",
        "name": "Graphic Design",
        "slug": "graphic-design",
        "subject": "Design",
        "password": None,
        "owner": None,
        "description": "Visual communication, typography, color theory, and Adobe Creative Suite.",
        "color": "#14b8a6",
        "max_participants": 1000,
    },
    {
        "id": "cls-110",
        "name": "English Literature",
        "slug": "eng-lit",
        "subject": "Humanities",
        "password": None,
        "owner": None,
        "description": "Classic and contemporary literature, critical analysis, and creative writing.",
        "color": "#a78bfa",
        "max_participants": 1000,
    },
    {
        "id": "cls-teacher-meeting",
        "name": "Teacher Meeting Room",
        "slug": "teacher-meeting",
        "subject": "Staff Only",
        "password": None,
        "owner": None,
        "description": "Exclusive room for teachers to hold private meetings.",
        "color": "#ef4444",
        "max_participants": 1000,
    }
]

# ── Lookup helpers ────────────────────────────────────────
CLASSROOM_BY_ID   = {c["id"]:   c for c in CLASSROOMS}
CLASSROOM_BY_SLUG = {c["slug"]: c for c in CLASSROOMS}

STUN_SERVERS = [
    {"urls": "stun:stun.l.google.com:19302"},
    {"urls": "stun:stun1.l.google.com:19302"},
]