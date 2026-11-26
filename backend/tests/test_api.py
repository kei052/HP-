import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from main import CoursesHandler
from api.catalog import load_catalog
from models.recommendation import percentage

class ApiTests(unittest.TestCase):
    def setUp(self):
        fixture = Path(__file__).resolve().parents[1] / 'dummy_database'
        self.mock_catalog = patch('main.load_catalog', side_effect=lambda: load_catalog(fixture))
        self.mock_catalog.start()
        self.addCleanup(self.mock_catalog.stop)
    def request(self, method, path, body=None):
        data = b'' if body is None else json.dumps(body).encode()
        raw = (f'{method} {path} HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: {len(data)}\r\n\r\n').encode() + data
        class Socket:
            def __init__(self): self.input = io.BytesIO(raw); self.output = bytearray()
            def makefile(self, mode, *args): return self.input
            def sendall(self, value): self.output.extend(value)
        sock = Socket()
        CoursesHandler(sock, ('127.0.0.1', 1234), None)
        head, body = bytes(sock.output).split(b'\r\n\r\n', 1)
        return int(head.split(b' ', 2)[1]), json.loads(body) if body else None
    def test_lists_and_details(self):
        for path, key, count in [('/courses','courses',3),('/jobs','jobs',2),('/qualifications','qualifications',2)]:
            status, result = self.request('GET', path)
            self.assertEqual((status, result['count'],len(result[key])), (200,count,count))
        status, result = self.request('GET','/jobs/D-J001')
        self.assertEqual(status,200)
        self.assertEqual(result['qualifications'][0]['qualification_id'],'D-Q001')
        self.assertEqual(result['courses'][0]['course_id'],'D-C002')
        status, result = self.request('GET','/qualifications/D-Q001')
        self.assertEqual({r['course_id'] for r in result['courses']},{'D-C001','D-C002'})
        self.assertEqual(result['jobs'][0]['job_id'],'D-J001')
        self.assertEqual(self.request('GET','/jobs/no-such-id')[0],404)
    def test_diagnosis_and_simulation(self):
        status, r = self.request('POST','/simulation',{'completed_course_ids':['D-C001','D-C001'], 'candidate_course_ids':['D-C002','D-C001']})
        self.assertEqual(status,200)
        self.assertEqual(r['completed']['jobs'][0]['rate'],38)
        self.assertEqual(r['completed']['jobs'][0]['recommended_course_ids'],['D-C002'])
        self.assertEqual(r['completed']['qualifications'][0]['rate'],50)
        self.assertEqual(r['simulated']['jobs'][0]['rate'],100)
        self.assertEqual(r['simulated']['qualifications'][0]['rate'],100)
        status, r = self.request('POST','/diagnosis',{'completed_course_ids':[]})
        self.assertEqual(status,200)
        self.assertTrue(all(x['rate']==0 for x in r['completed']['jobs']+r['completed']['qualifications']))
        self.assertEqual(percentage(1, 8),13)
        self.assertEqual(percentage(0, 0),0)
    def test_invalid_inputs(self):
        self.assertEqual(self.request('POST','/diagnosis',{'completed_course_ids':['unknown']})[0],400)
        self.assertEqual(self.request('POST','/diagnosis',{'completed_course_ids':'D-C001'})[0],400)
        self.assertEqual(self.request('POST','/simulation',{'completed_course_ids':[]})[0],400)
        self.assertEqual(self.request('GET','/not-found')[0],404)
        self.assertEqual(self.request('OPTIONS','/diagnosis')[0],204)

if __name__ == '__main__': unittest.main()
