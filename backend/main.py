import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from api.courses import CourseDataError, load_courses


class CoursesHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: object) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        if urlsplit(self.path).path != "/courses":
            self._send_json(404, {"error": "Not found"})
            return

        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        if urlsplit(self.path).path != "/courses":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            courses = load_courses()
        except CourseDataError as error:
            self.log_error("Failed to load courses: %s", error)
            self._send_json(500, {"error": "Course data is unavailable"})
            return

        self._send_json(
            200,
            {
                "count": len(courses),
                "courses": courses,
            },
        )


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), CoursesHandler)
    print(f"Courses API listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping courses API.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
