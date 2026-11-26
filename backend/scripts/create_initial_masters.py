"""Build the initial ID-based CSVs. Existing output is never overwritten."""
import csv
from pathlib import Path

APP = Path(__file__).resolve().parents[2]
DB = APP / 'backend' / 'database'

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def write(path, fields, rows):
    with path.open('x', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

outputs = ['courses.csv', 'jobs.csv', 'qualifications.csv', 'job_courses.csv',
           'job_qualifications.csv', 'qualification_courses.csv', 'unmatched_relations.csv']
existing = [name for name in outputs if (DB / name).exists()]
if existing:
    raise SystemExit('Refusing to overwrite existing files: ' + ', '.join(existing))

courses = read(DB / 'subjects_simple.csv')
jobs = read(APP / 'jobs.csv')
qualifications = read(APP / 'qualifications.csv')

def unique_index(rows, field, id_field):
    result = {}
    for row in rows:
        name, ident = row[field].strip(), row[id_field].strip()
        if not name or not ident or name in result or ident in result.values():
            raise ValueError(f'Duplicate or empty {field}/{id_field}: {name!r}, {ident!r}')
        result[name] = ident
    return result

# IDs are assigned once in source order; courses.csv is the durable master afterward.
for i, row in enumerate(courses, 1):
    row['course_id'] = f'C{i:03d}'
course_index = unique_index(courses, '講義名', 'course_id')
job_index = unique_index(jobs, 'job_name', 'job_id')
qual_index = unique_index(qualifications, 'qualification_name', 'qualification_id')
job_alias = {'ITサポート、ヘルプデスク': 'ITサポート・ヘルプデスク'}
course_alias = {'情報セキュリティー': '情報セキュリティ', '国際統計分類I': '国際統計分類Ⅰ'}
def lookup(index, value, aliases):
    return index.get(aliases.get(value, value))
unmatched = []
def missing(source, line, kind, value, relation):
    unmatched.append(dict(source_file=source, source_row=line, relation=relation, missing_type=kind, source_value=value))

jc = []
with (APP / 'data.csv').open(encoding='utf-8-sig', newline='') as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) != len(header):
            raise ValueError(f'data.csv row {reader.line_num}: unexpected column count')
        course = lookup(course_index, row[0], course_alias)
        for name, value in zip(header[1:], row[1:]):
            if name == '未定':  # Existing ranking excludes this column.
                continue
            job = lookup(job_index, name, job_alias)
            if not course:
                missing('data.csv', reader.line_num, 'course', row[0], name)
            if not job:
                missing('data.csv', reader.line_num, 'job', name, row[0])
            if job and course:
                score = int(value)
                if score < 0:
                    raise ValueError('Negative score')
                jc.append(dict(job_id=job, course_id=course, score=score))

jq, qc = set(), set()
with (APP / 'data1.csv').open(encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        j, q, c = row['職業'], row['資格'], row['関連度の高い講義']
        job = lookup(job_index, j, job_alias)
        qual = qual_index.get(q.strip())
        course = lookup(course_index, c, course_alias)
        if not job: missing('data1.csv', reader.line_num, 'job', j, f'{q} / {c}')
        if not qual: missing('data1.csv', reader.line_num, 'qualification', q, f'{j} / {c}')
        if not course: missing('data1.csv', reader.line_num, 'course', c, f'{j} / {q}')
        if job and qual: jq.add((job, qual))
        if qual and course: qc.add((qual, course))

if len({(r['job_id'], r['course_id']) for r in jc}) != len(jc):
    raise ValueError('Duplicate job/course pair')
write(DB / 'courses.csv', ['course_id'] + [k for k in courses[0] if k != 'course_id'], courses)
write(DB / 'jobs.csv', list(jobs[0]), jobs)
write(DB / 'qualifications.csv', list(qualifications[0]), qualifications)
write(DB / 'job_courses.csv', ['job_id', 'course_id', 'score'], jc)
write(DB / 'job_qualifications.csv', ['job_id', 'qualification_id'], [dict(job_id=j, qualification_id=q) for j, q in sorted(jq)])
write(DB / 'qualification_courses.csv', ['qualification_id', 'course_id', 'relevance'], [dict(qualification_id=q, course_id=c, relevance='') for q, c in sorted(qc)])
write(DB / 'unmatched_relations.csv', ['source_file', 'source_row', 'relation', 'missing_type', 'source_value'], unmatched)
print(f'courses={len(courses)} jobs={len(jobs)} qualifications={len(qualifications)} job_courses={len(jc)} job_qualifications={len(jq)} qualification_courses={len(qc)} unmatched={len(unmatched)}')
