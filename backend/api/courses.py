import csv
from pathlib import Path
from typing import TypedDict


COURSES_CSV = (
    Path(__file__).resolve().parents[1]
    / "database"
    / "subjects_simple.csv"
)


class Course(TypedDict):
    course_name: str
    education_category: str
    subject_category_1: str
    subject_category_2: str
    year: int
    credits: int
    requirement_type: str
    prerequisites: list[str]


class CourseDataError(RuntimeError):
    """Raised when the course CSV cannot be read or contains invalid data."""


def load_courses(csv_path: Path = COURSES_CSV) -> list[Course]:
    required_columns = {
        "講義名",
        "教育区分",
        "科目区分１",
        "科目区分２",
        "受講年次",
        "単位数",
        "必修選択区分",
        "履修前提科目",
    }

    try:
        with csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                raise CourseDataError("The course CSV has no header row.")

            missing_columns = required_columns.difference(reader.fieldnames)
            if missing_columns:
                raise CourseDataError(
                    "The course CSV is missing required columns: "
                    + ", ".join(sorted(missing_columns))
                )

            courses: list[Course] = []
            for row in reader:
                row_number = reader.line_num
                try:
                    course_name = (row["講義名"] or "").strip()
                    if not course_name:
                        raise ValueError("講義名 is empty")

                    year = int(row["受講年次"] or "")
                    credits = int(row["単位数"] or "")
                except (TypeError, ValueError) as error:
                    raise CourseDataError(
                        f"Invalid course data on CSV row {row_number}: {error}"
                    ) from error

                prerequisites = (row["履修前提科目"] or "").strip()
                courses.append(
                    {
                        "course_name": course_name,
                        "education_category": (row["教育区分"] or "").strip(),
                        "subject_category_1": (
                            row["科目区分１"] or ""
                        ).strip(),
                        "subject_category_2": (
                            row["科目区分２"] or ""
                        ).strip(),
                        "year": year,
                        "credits": credits,
                        "requirement_type": (
                            row["必修選択区分"] or ""
                        ).strip(),
                        "prerequisites": [
                            item.strip()
                            for item in prerequisites.split("、")
                            if item.strip()
                        ],
                    }
                )

    except OSError as error:
        raise CourseDataError(
            f"Could not read the course CSV at {csv_path}: {error}"
        ) from error
    except csv.Error as error:
        raise CourseDataError(f"Could not parse the course CSV: {error}") from error

    return courses
