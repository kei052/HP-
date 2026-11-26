"""Public catalog, job/qualification details, diagnosis and simulation API.

Use ``app_server.py`` for the normal web application (same-origin UI + login + API).
This module can also run as a standalone API for the bundled API tests.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, unquote
from api.catalog import load_catalog, DataError
from models.recommendation import evaluate


class InputError(ValueError):
    pass


def course_ids(payload, key, catalog):
    raw = payload.get(key)
    if not isinstance(raw, list) or any(not isinstance(x, str) for x in raw):
        raise InputError(f'{key} must be a list of IDs')
    if any(x not in catalog['courses_by_id'] for x in raw):
        raise InputError(f'{key} contains an unknown course ID')
    return list(dict.fromkeys(raw))


def catalog_get(path, catalog):
    path = unquote(urlsplit(path).path)
    if path in ('/catalog', '/api/catalog'):
        return 200, {k: catalog[k] for k in ('courses', 'jobs', 'qualifications', 'job_courses',
                                            'job_qualifications', 'qualification_courses')}
    for segment, key in (('/courses', 'courses'), ('/jobs', 'jobs'), ('/qualifications', 'qualifications')):
        if path == segment:
            return 200, {'count': len(catalog[key]), key: catalog[key]}
        if path.startswith(segment + '/'):
            ident = path[len(segment) + 1:]
            if '/' in ident or not ident:
                return 404, {'error': 'Not found'}
            if key == 'courses':
                found = catalog['courses_by_id'].get(ident)
                return (200, found) if found else (404, {'error': 'Not found'})
            if key == 'jobs':
                found = catalog['jobs_by_id'].get(ident)
                if not found:
                    return 404, {'error': 'Not found'}
                courses = [{**catalog['courses_by_id'][r['course_id']], 'score': r['score']}
                           for r in catalog['job_courses'] if r['job_id'] == ident]
                courses.sort(key=lambda row: -row['score'])
                qualifications = [catalog['qualifications_by_id'][r['qualification_id']]
                                  for r in catalog['job_qualifications'] if r['job_id'] == ident]
                return 200, {**found, 'courses': courses, 'qualifications': qualifications}
            found = catalog['qualifications_by_id'].get(ident)
            if not found:
                return 404, {'error': 'Not found'}
            courses = [catalog['courses_by_id'][r['course_id']]
                       for r in catalog['qualification_courses'] if r['qualification_id'] == ident]
            jobs = [catalog['jobs_by_id'][r['job_id']]
                    for r in catalog['job_qualifications'] if r['qualification_id'] == ident]
            return 200, {**found, 'courses': courses, 'jobs': jobs}
    return 404, {'error': 'Not found'}


def catalog_post(path, payload, catalog):
    path = urlsplit(path).path
    if path not in ('/diagnosis', '/simulation'):
        return 404, {'error': 'Not found'}
    if not isinstance(payload, dict):
        raise InputError('JSON object is required')
    completed = course_ids(payload, 'completed_course_ids', catalog)
    result = {'completed': evaluate(catalog, completed)}
    if path == '/simulation':
        candidate = course_ids(payload, 'candidate_course_ids', catalog)
        result['simulated'] = evaluate(catalog, completed + candidate)
    return 200, result


class CoursesHandler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        try:
            status, result = catalog_get(self.path, load_catalog())
        except DataError as e:
            self.log_error('Catalog error: %s', e)
            status, result = 500, {'error': 'Catalog unavailable'}
        self._send_json(status, result)

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1_000_000:
                raise InputError('Invalid request length')
            payload = json.loads(self.rfile.read(length))
            status, result = catalog_post(self.path, payload, load_catalog())
        except (InputError, ValueError, json.JSONDecodeError) as e:
            status, result = 400, {'error': str(e)}
        except DataError as e:
            self.log_error('Catalog error: %s', e)
            status, result = 500, {'error': 'Catalog unavailable'}
        self._send_json(status, result)


def main():
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '8000'))
    print(f'Catalog-only API on http://{host}:{port} (UI+account: app_server.py)')
    ThreadingHTTPServer((host, port), CoursesHandler).serve_forever()


if __name__ == '__main__':
    main()
