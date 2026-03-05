"""
requirements.py
----------------
HR requirement presets for the ATS system.

These dicts are passed directly to ResumeMatcher.set_requirements().

Fields used by matcher.py:
    job_role            str   — display name
    role_description    str   — used for semantic summary scoring
    required_skills     list  — must-have technologies / skills
    preferred_skills    list  — nice-to-have technologies / skills
    experience_required dict  — { freshers_allowed: bool, description: str }
    education_required  dict  — { degree: str, field: str, min_gpa: float }
    projects_required   dict  — { min_count: int, description: str }
"""

# ─────────────────────────────────────────────────────────────────────────────
# Junior Web / Full Stack Developer
# ─────────────────────────────────────────────────────────────────────────────

WEB_DEV_REQUIREMENTS = {
  "info": {
    "name": "Vengatesan G",
    "role": "Full Stack Developer",
    "email": "vengatganesan2206@gmail.com",
    "phone": "+91 7538802537",
    "address": "Kumbakonam, Thanjavur",
    "website": "linkedin.com/in/vengatesan-g-734164337"
  },
  "about": "",
  "skills": [
    "HTML",
    "CSS",
    "JavaScript",
    "React.js",
    "Java",
    "Spring",
    "Spring Boot",
    "MySQL",
    "Postman",
    "Figma",
    "Git",
    "GitHub",
    "IntelliJ",
    "VS Code"
  ],
  "soft_skills": [
    "Project Management",
    "Teamwork",
    "Time Management",
    "Leadership",
    "Critical Thinking"
  ],
  "experience": [],
  "education": [
    {
      "degree": "Higher Secondary Education",
      "institution": "Computer Science Stream",
      "started": "2022",
      "ended": "2023",
      "score": "81",
      "score_max": "100",
      "score_type": "PERCENTAGE"
    },
    {
      "degree": "Bachelor of Computer Science and Engineering",
      "institution": "AVC College of Engineering",
      "started": "2023",
      "ended": "2027",
      "score": "8.4",
      "score_max": "10.0",
      "score_type": "GPA"
    }
  ],
  "projects": [
    {
      "title": "Course Registration System",
      "started": "2026",
      "ended": "PRESENT",
      "description": "Full-stack web application for user registration and efficient course enrollment management. Developed a full-stack Course Registration System enabling users to register and enroll in courses. Ensured efficient backend processing for managing course enrollments.",
      "technologies": [
        "HTML",
        "CSS",
        "JavaScript",
        "Spring Boot",
        "MySQL",
        "Postman"
      ],
      "url": ""
    },
    {
      "title": "Responsive Music Web Application",
      "started": "2025",
      "ended": "2026",
      "description": "Developed a responsive frontend music website focusing on usability, performance, and cross-device compatibility. Ensured smooth performance and compatibility across multiple devices with an interactive and user-friendly interface.",
      "technologies": [
        "HTML",
        "CSS",
        "JavaScript",
        "React.js"
      ],
      "url": ""
    }
  ],
  "languages": [
    "English (Fluent)",
    "Tamil (Fluent)"
  ],
  "achievements": [
    "Secured Runner-Up position in a Mathematical Quiz competition, demonstrating strong analytical and problem-solving skills.",
    "Shortlisted for final presentation in a technical paper presentation event.",
    "Participated in hackathons focusing on problem-solving and teamwork."
  ],
  "job_role":"web_developer"
}
# ─────────────────────────────────────────────────────────────────────────────
# Deep Learning / AI Engineer
# ─────────────────────────────────────────────────────────────────────────────

DL_REQUIREMENTS = {
    "job_role": "Deep Learning / AI Engineer",

    "role_description": (
        "We are looking for a Deep Learning Engineer with strong hands-on experience "
        "in building and deploying neural network models for computer vision or NLP tasks. "
        "The candidate should be comfortable with PyTorch/TensorFlow, model training pipelines, "
        "and deploying models to production environments."
    ),

    "required_skills": [
        "Python", "PyTorch", "TensorFlow", "deep learning",
        "neural networks", "model training", "GPU", "CUDA",
    ],

    "preferred_skills": [
        "Hugging Face", "BERT", "GPT", "YOLO", "OpenCV",
        "MLflow", "Docker", "AWS", "ONNX",
    ],

    "projects_required": {
        "min_count": 2,
        "description": "End-to-end deep learning projects with training, evaluation, and deployment.",
    },

    "education_required": {
        "degree": "Bachelor or Master in Computer Science, AI, or related",
        "field":  "Computer Science, AI, Machine Learning, or Data Science",
        "min_gpa": 0,
    },

    "experience_required": {
        "freshers_allowed": False,
        "description": "Minimum 2 years of industry or research experience required.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Data Science / Analytics
# ─────────────────────────────────────────────────────────────────────────────

DATA_SCIENCE_REQUIREMENTS = {
    "job_role": "Data Scientist / Analyst",

    "role_description": (
        "Seeking a Data Scientist who can transform raw data into actionable insights. "
        "Strong skills in Python, SQL, statistical modelling, and data visualisation are "
        "essential. Experience with ML pipelines and cloud-based data platforms is a plus."
    ),

    "required_skills": [
        "Python", "SQL", "pandas", "numpy", "scikit-learn",
        "data visualisation", "statistics", "machine learning",
    ],

    "preferred_skills": [
        "Tableau", "Power BI", "Spark", "MLflow",
        "AWS", "GCP", "A/B testing", "ETL",
    ],

    "projects_required": {
        "min_count": 2,
        "description": "Data analysis or ML projects with clear business impact metrics.",
    },

    "education_required": {
        "degree": "Bachelor or Master in Statistics, Mathematics, Computer Science, or related",
        "field":  "Statistics, Mathematics, Data Science, or Computer Science",
        "min_gpa": 0,
    },

    "experience_required": {
        "freshers_allowed": True,
        "description": "Strong project portfolio acceptable in lieu of industry experience.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Cloud / DevOps Engineer
# ─────────────────────────────────────────────────────────────────────────────

DEVOPS_REQUIREMENTS = {
    "job_role": "Cloud / DevOps Engineer",

    "role_description": (
        "Looking for a DevOps Engineer experienced in CI/CD pipelines, container orchestration, "
        "and cloud infrastructure. The ideal candidate automates deployments, ensures system "
        "reliability, and supports development teams with robust tooling."
    ),

    "required_skills": [
        "Docker", "Kubernetes", "CI/CD", "Linux", "Git",
        "AWS", "Terraform", "bash scripting",
    ],

    "preferred_skills": [
        "Ansible", "Prometheus", "Grafana", "Jenkins", "GitLab CI",
        "Azure", "GCP", "Helm", "ArgoCD",
    ],

    "projects_required": {
        "min_count": 1,
        "description": "Infrastructure automation or cloud deployment projects.",
    },

    "education_required": {
        "degree": "Bachelor in Computer Science, IT, or related",
        "field":  "Computer Science, Information Technology, or related",
        "min_gpa": 0,
    },

    "experience_required": {
        "freshers_allowed": False,
        "description": "Minimum 1 year of DevOps or cloud infrastructure experience.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Role map — used by main.py --role flag
# ─────────────────────────────────────────────────────────────────────────────

ROLE_MAP = {
    "web":     WEB_DEV_REQUIREMENTS,
    "dl":      DL_REQUIREMENTS,
    "data":    DATA_SCIENCE_REQUIREMENTS,
    "devops":  DEVOPS_REQUIREMENTS,
}