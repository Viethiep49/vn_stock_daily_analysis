import os
from typing import List

SKILLS_DIR = os.path.dirname(os.path.abspath(__file__))

def list_skills() -> List[str]:
    """
    Lists available skill names (filenames without .md extension).
    """
    skills = []
    for file in os.listdir(SKILLS_DIR):
        if file.endswith(".md"):
            skills.append(file[:-3])
    return sorted(skills)

def get_skill_content(skill_name: str) -> str:
    """
    Loads the .md file content for a given skill name.
    """
    file_path = os.path.join(SKILLS_DIR, f"{skill_name}.md")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Skill file not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
