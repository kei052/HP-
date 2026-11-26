"""ID-based matching shared by diagnosis and simulation endpoints."""
from collections import defaultdict
from math import floor


def percentage(part, total):
    """Round halves up, consistently with JavaScript Math.round for >=0."""
    return floor(part * 100 / total + 0.5) if total > 0 else 0


def evaluate(catalog, selected_ids):
    selected = set(selected_ids)
    by_job = defaultdict(list)
    for rel in catalog['job_courses']:
        by_job[rel['job_id']].append(rel)
    by_qualification = defaultdict(list)
    for rel in catalog['qualification_courses']:
        by_qualification[rel['qualification_id']].append(rel['course_id'])

    jobs = []
    for job in catalog['jobs']:
        rels = by_job[job['job_id']]
        total = sum(rel['score'] for rel in rels)
        taken = sum(rel['score'] for rel in rels if rel['course_id'] in selected)
        recommended = sorted((rel for rel in rels if rel['course_id'] not in selected and rel['score'] > 0),
                             key=lambda rel: -rel['score'])
        jobs.append({'job_id': job['job_id'], 'job_name': job['job_name'], 'rate': percentage(taken, total),
                     'recommended_course_ids': [rel['course_id'] for rel in recommended[:5]]})
    jobs.sort(key=lambda item: -item['rate'])
    quals = []
    for qual in catalog['qualifications']:
        rels = by_qualification[qual['qualification_id']]
        missing = [course_id for course_id in rels if course_id not in selected]
        quals.append({'qualification_id': qual['qualification_id'], 'qualification_name': qual['qualification_name'],
                      'rate': percentage(len(rels) - len(missing), len(rels)),
                      'missing_course_ids': missing})
    quals.sort(key=lambda item: -item['rate'])
    return {'jobs': jobs, 'qualifications': quals}
