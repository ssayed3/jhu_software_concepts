import subprocess
import sys
import threading
from pathlib import Path

from flask import Flask, redirect, render_template, url_for, jsonify
from sqlalchemy import func, select

from .load_data import load_scraped_data
from .models import Applicant, SessionLocal




BASE_FOLDER = Path(__file__).resolve().parent

scrape_lock = threading.Lock()
scrape_status = "Ready to pull new data."


def get_analysis_results():
    with SessionLocal() as session:

        # Question 1
        q1 = session.scalar(
            select(func.count())
            .select_from(Applicant)
            .where(func.lower(Applicant.term) == "fall 2026")
        )

        # Question 2
        total_classified = session.scalar(
            select(func.count())
            .select_from(Applicant)
            .where(
                Applicant.us_or_international.is_not(None),
                func.trim(Applicant.us_or_international) != ""
            )
        )

        international = session.scalar(
            select(func.count())
            .select_from(Applicant)
            .where(
                func.lower(Applicant.us_or_international)
                == "international"
            )
        )

        q2 = (
            international / total_classified * 100
            if total_classified
            else 0
        )

        # Question 3
        q3 = session.execute(
            select(
                func.avg(Applicant.gpa),
                func.avg(Applicant.gre),
                func.avg(Applicant.gre_v),
                func.avg(Applicant.gre_aw)
            )
        ).one()

        # Question 4
        q4 = session.scalar(
            select(func.avg(Applicant.gpa))
            .where(
                func.lower(Applicant.term) == "fall 2026",
                func.lower(Applicant.us_or_international)
                == "american",
                Applicant.gpa.is_not(None)
            )
        )

        # Question 5
        fall_2025_total = session.scalar(
            select(func.count())
            .select_from(Applicant)
            .where(func.lower(Applicant.term) == "fall 2025")
        )

        fall_2025_accepted = session.scalar(
            select(func.count())
            .select_from(Applicant)
            .where(
                func.lower(Applicant.term) == "fall 2025",
                func.lower(Applicant.status) == "accepted"
            )
        )

        q5 = (
            fall_2025_accepted / fall_2025_total * 100
            if fall_2025_total
            else 0
        )

        # Question 6
        q6 = session.scalar(
            select(func.avg(Applicant.gpa))
            .where(
                func.lower(Applicant.term) == "fall 2026",
                func.lower(Applicant.status) == "accepted",
                Applicant.gpa.is_not(None)
            )
        )

        # Question 7
        q7 = session.scalar(
            select(func.count())
            .select_from(Applicant)
            .where(
                (
                    func.lower(Applicant.program)
                    .like("%johns hopkins%")
                    | func.lower(Applicant.program).like("%jhu%")
                ),
                (
                    func.lower(Applicant.program)
                    .like("%computer science%")
                    | func.lower(Applicant.program).like("% cs%")
                ),
                (
                    func.lower(Applicant.degree).like("%master%")
                    | func.lower(Applicant.degree).in_(
                        ["ms", "m.s.", "msc", "m.sc."]
                    )
                )
            )
        )

        # Question 8
        q8 = session.scalar(
            select(func.count())
            .select_from(Applicant)
            .where(
                func.lower(Applicant.term) == "fall 2026",
                func.lower(Applicant.status) == "accepted",
                func.lower(Applicant.degree).in_(
                    ["phd", "ph.d.", "ph.d"]
                ),
                (
                    func.lower(Applicant.program)
                    .like("%computer science%")
                    | func.lower(Applicant.program).like("% cs%")
                ),
                (
                    func.lower(Applicant.program).like("%georgetown%")
                    | func.lower(Applicant.program).like(
                        "%massachusetts institute of technology%"
                    )
                    | func.lower(Applicant.program).like("% mit,%")
                    | func.lower(Applicant.program).like("%stanford%")
                    | func.lower(Applicant.program).like(
                        "%carnegie mellon%"
                    )
                    | func.lower(Applicant.program).like("%cmu%")
                )
            )
        )

        # Question 9
        q9_llm = session.scalar(
            select(func.count())
            .select_from(Applicant)
            .where(
                func.lower(Applicant.term) == "fall 2026",
                func.lower(Applicant.status) == "accepted",
                func.lower(Applicant.degree).in_(
                    ["phd", "ph.d.", "ph.d"]
                ),
                (
                    func.lower(
                        Applicant.llm_generated_program
                    ).like("%computer science%")
                    | (
                        func.lower(
                            Applicant.llm_generated_program
                        ) == "cs"
                    )
                ),
                (
                    func.lower(
                        Applicant.llm_generated_university
                    ).like("%georgetown%")
                    | func.lower(
                        Applicant.llm_generated_university
                    ).like(
                        "%massachusetts institute of technology%"
                    )
                    | (
                        func.lower(
                            Applicant.llm_generated_university
                        ) == "mit"
                    )
                    | func.lower(
                        Applicant.llm_generated_university
                    ).like("%stanford%")
                    | func.lower(
                        Applicant.llm_generated_university
                    ).like("%carnegie mellon%")
                    | (
                        func.lower(
                            Applicant.llm_generated_university
                        ) == "cmu"
                    )
                )
            )
        )

        # Original Question 10
        q10 = session.scalar(
            select(func.count())
            .select_from(Applicant)
            .where(
                func.lower(Applicant.term) == "fall 2026",
                func.lower(Applicant.status) == "accepted"
            )
        )

        # Original Question 11
        q11 = session.scalar(
            select(func.avg(Applicant.gpa))
            .where(
                func.lower(Applicant.term) == "fall 2026",
                func.lower(Applicant.us_or_international)
                == "international",
                Applicant.gpa.is_not(None)
            )
        )

        results = [
            {
                "question":
                    "1. How many entries applied for Fall 2026?",
                "answer": f"{q1:,}"
            },
            {
                "question":
                    "2. What percentage of applicants are international?",
                "answer": f"{q2:.2f}%"
            },
            {
                "question":
                    "3. What are the average GPA and GRE scores?",
                "answer": (
                    f"GPA: {q3[0]:.2f}, "
                    f"GRE Quantitative: {q3[1]:.2f}, "
                    f"GRE Verbal: {q3[2]:.2f}, "
                    f"GRE Analytical Writing: {q3[3]:.2f}"
                )
            },
            {
                "question":
                    "4. What is the average GPA of American "
                    "applicants for Fall 2026?",
                "answer": f"{q4:.2f}"
            },
            {
                "question":
                    "5. What percentage of Fall 2025 applications "
                    "were accepted?",
                "answer": f"{q5:.2f}%"
            },
            {
                "question":
                    "6. What is the average GPA of accepted "
                    "applicants for Fall 2026?",
                "answer": f"{q6:.2f}"
            },
            {
                "question":
                    "7. How many applicants applied to Johns Hopkins "
                    "for a Master's in Computer Science?",
                "answer": f"{q7:,}"
            },
            {
                "question":
                    "8. How many Fall 2026 accepted applicants applied "
                    "for a PhD in Computer Science at Georgetown, MIT, "
                    "Stanford, or Carnegie Mellon?",
                "answer": f"{q8:,}"
            },
            {
                "question":
                    "9. Repeat Question 8 using the LLM-generated fields.",
                "answer": (
                    f"Original fields: {q8}, "
                    f"LLM-generated fields: {q9_llm}, "
                    f"Difference: {q9_llm - q8}"
                )
            },
            {
                "question":
                    "10. How many Fall 2026 applicants were accepted?",
                "answer": f"{q10:,}"
            },
            {
                "question":
                    "11. What is the average GPA of international "
                    "applicants for Fall 2026?",
                "answer": f"{q11:.2f}"
            }
        ]

        return results


def run_scraper():
    global scrape_status

    try:
        scrape_status = "Pulling new GradCafe data..."

        result = subprocess.run(
            [sys.executable, "-m", "src.collect_data"],
            cwd=BASE_FOLDER.parent
        )

        if result.returncode != 0:
            scrape_status = (
                "Data pull stopped with an error. "
                "Check the Terminal for details."
            )

            return

        inserted = load_scraped_data()

        scrape_status = (
            f"Data pull complete. "
            f"{inserted} new applicant(s) added to the database."
        )



    except Exception as error:
        scrape_status = f"Data pull error: {error}"

    finally:
        scrape_lock.release()

def create_app(
    test_config=None,
    analysis_func=None,
    scraper_func=None,
    loader_func=None
):
    app = Flask(__name__)

    if test_config is not None:
        app.config.update(test_config)

    if analysis_func is None:
        analysis_func = get_analysis_results

    if loader_func is None:
        loader_func = load_scraped_data



    @app.route("/")
    @app.route("/analysis")
    def home():
        results = analysis_func()

        return render_template(
            "index.html",
            results=results,
            scrape_status=scrape_status,
            scrape_running=scrape_lock.locked()
        )

    @app.route("/pull-data", methods=["POST"])
    def pull_data():
        global scrape_status

        if not scrape_lock.acquire(blocking=False):
            scrape_status = (
                "A data pull is already running. "
                "Please wait for it to finish."
            )
            return {"busy": True}, 409

        scrape_status = "Starting data pull..."

        # Testing mode: use fake scraper and fake loader
        if app.config.get("TESTING") and scraper_func is not None:
            try:
                rows = scraper_func()
                loader_func(rows)
                return jsonify({"ok": True}), 200

            except Exception as e:
                return jsonify({
                    "ok": False,
                    "error": str(e)
                }), 500

            finally:
                scrape_lock.release()

        # Normal mode: use the original real scraper
        thread = threading.Thread(
            target=run_scraper,
            daemon=True
        )
        thread.start()

        return {"ok": True}, 202

    @app.route("/update-analysis", methods=["POST"])
    def update_analysis():
        global scrape_status

        if scrape_lock.locked():
            scrape_status = (
                "Data pull is still running. "
                "Analysis shown using the current database."
            )
            return {"busy": True}, 409

        scrape_status = (
            "Analysis updated from the current database."
        )
        return {"ok": True}, 200

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    app.run(debug=True)

