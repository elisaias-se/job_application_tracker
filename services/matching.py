"""Deterministic matching against each job's required skills; no external API."""
import json


def normalize_skills(skills):
    """Trim and deduplicate exact skill names, preserving first-entered spelling."""
    if isinstance(skills, str):
        skills = skills.split(',')
    unique = {}
    for skill in skills or []:
        if isinstance(skill, str) and skill.strip():
            skill = skill.strip()
            unique.setdefault(skill.casefold(), skill)
    return list(unique.values())


def rank_jobs(jobs, user_skills):
    user = {skill.casefold() for skill in normalize_skills(user_skills)}
    results = []
    for job in jobs:
        requirements = job.get('requirements')
        if isinstance(requirements, str):
            try:
                requirements = json.loads(requirements)
            except (ValueError, TypeError):
                requirements = []
        # Only JSON arrays represent requirements. Legacy/imported objects are unscored.
        required = normalize_skills(requirements if isinstance(requirements, list) else [])
        matched = [skill for skill in required if skill.casefold() in user]
        missing = [skill for skill in required if skill.casefold() not in user]
        score = len(matched) / len(required) if required else None
        results.append(dict(job, matched=matched, missing=missing, required_count=len(required),
                            score=score, percentage=int(score * 100 + 0.5) if score is not None else None))
    return sorted(results, key=lambda job: (
        job['score'] is None, -(job['score'] or 0),
        job['job_title'].casefold(), job['company_name'].casefold(), job['job_id']))
