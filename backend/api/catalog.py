"""Load and validate the ID-based catalog used by the API."""
import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / 'database'

class DataError(Exception):
    pass

def _read(directory, name, columns):
    try:
        with (directory / name).open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                reader.fieldnames = [{'講義ID': 'course_id', 'subject_id': 'course_id'}.get(name, name) for name in reader.fieldnames]
            if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)) or not set(columns).issubset(reader.fieldnames):
                raise DataError(f'{name}: missing required columns')
            rows = list(reader)
            if any(None in r or any(r.get(k) is None for k in columns) for r in rows):
                raise DataError(f'{name}: malformed row')
            return rows
    except (OSError, csv.Error, UnicodeError) as e:
        raise DataError(f'{name}: cannot read data') from e

def _index(rows, key, filename):
    result = {}
    for row in rows:
        ident = row[key].strip()
        if not ident or ident in result:
            raise DataError(f'{filename}: empty or duplicate {key}')
        result[ident] = row
    return result

def load_catalog(directory=DATA_DIR):
    course_fields = ['course_id', '講義名', '教育区分', '科目区分１', '科目区分２', '受講年次', '単位数', '必修選択区分', '履修前提科目']
    courses = []
    for r in _read(directory, 'courses.csv', course_fields):
        try:
            course = {'course_id': r['course_id'].strip(), 'course_name': r['講義名'].strip(),
                      'education_category': r['教育区分'].strip(), 'subject_category_1': r['科目区分１'].strip(),
                      'subject_category_2': r['科目区分２'].strip(), 'year': int(r['受講年次']),
                      'credits': int(r['単位数']), 'requirement_type': r['必修選択区分'].strip(),
                      'prerequisites': [v.strip() for v in r['履修前提科目'].split('、') if v.strip()]}
        except (TypeError, ValueError) as e:
            raise DataError('courses.csv: invalid year or credits') from e
        if not course['course_name'] or course['year'] < 1 or course['credits'] < 0:
            raise DataError('courses.csv: invalid course')
        courses.append(course)
    jobs = _read(directory, 'jobs.csv', ['job_id', 'job_name', 'description'])
    quals = _read(directory, 'qualifications.csv', ['qualification_id', 'qualification_name', 'description', 'official_url'])
    course_by_id = _index(courses, 'course_id', 'courses.csv')
    job_by_id = _index(jobs, 'job_id', 'jobs.csv')
    qual_by_id = _index(quals, 'qualification_id', 'qualifications.csv')
    relations = []
    for name, fields, left, right in [
        ('job_courses.csv', ['job_id', 'course_id', 'score'], job_by_id, course_by_id),
        ('job_qualifications.csv', ['job_id', 'qualification_id'], job_by_id, qual_by_id),
        ('qualification_courses.csv', ['qualification_id', 'course_id', 'relevance'], qual_by_id, course_by_id),
    ]:
        rows = _read(directory, name, fields)
        seen = set()
        for row in rows:
            pair = (row[fields[0]], row[fields[1]])
            if pair in seen or pair[0] not in left or pair[1] not in right:
                raise DataError(f'{name}: duplicate or unknown reference')
            seen.add(pair)
            if name == 'job_courses.csv':
                try: row['score'] = int(row['score'])
                except ValueError as e: raise DataError(f'{name}: invalid score') from e
                if row['score'] < 0: raise DataError(f'{name}: negative score')
        relations.append(rows)
    return {'courses': courses, 'jobs': jobs, 'qualifications': quals,
            'courses_by_id': course_by_id, 'jobs_by_id': job_by_id, 'qualifications_by_id': qual_by_id,
            'job_courses': relations[0], 'job_qualifications': relations[1], 'qualification_courses': relations[2]}
