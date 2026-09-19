from sqlalchemy import func, select

from models import Applicant, SessionLocal


def question_1(session):
    statement = (
        select(func.count())
        .select_from(Applicant)
        .where(func.lower(Applicant.term) == "fall 2026")
    )

    result = session.scalar(statement)

    print("Question 1: How many entries applied for Fall 2026?")
    print(f"Answer: {result}")


def question_4(session):
    statement = (
        select(func.avg(Applicant.gpa))
        .where(
            func.lower(Applicant.term) == "fall 2026",
            func.lower(Applicant.us_or_international) == "american",
            Applicant.gpa.is_not(None)
        )
    )

    result = session.scalar(statement)

    print("\nQuestion 4: What is the average GPA of American applicants for Fall 2026?")
    print(f"Answer: {result:.2f}")


def question_5(session):
    total_statement = (
        select(func.count())
        .select_from(Applicant)
        .where(func.lower(Applicant.term) == "fall 2025")
    )

    accepted_statement = (
        select(func.count())
        .select_from(Applicant)
        .where(
            func.lower(Applicant.term) == "fall 2025",
            func.lower(Applicant.status) == "accepted"
        )
    )

    total = session.scalar(total_statement)
    accepted = session.scalar(accepted_statement)

    percentage = (accepted / total * 100) if total else 0

    print("\nQuestion 5: What percentage of Fall 2025 applications were accepted?")
    print(f"Answer: {percentage:.2f}%")


def question_8(session):
    statement = (
        select(func.count())
        .select_from(Applicant)
        .where(
            func.lower(Applicant.term) == "fall 2026",
            func.lower(Applicant.status) == "accepted",
            func.lower(Applicant.degree).in_(["phd", "ph.d.", "ph.d"]),
            (
                func.lower(Applicant.program).like("%computer science%")
                | func.lower(Applicant.program).like("% cs%")
            ),
            (
                func.lower(Applicant.program).like("%georgetown%")
                | func.lower(Applicant.program).like(
                    "%massachusetts institute of technology%"
                )
                | func.lower(Applicant.program).like("% mit,%")
                | func.lower(Applicant.program).like("%stanford%")
                | func.lower(Applicant.program).like("%carnegie mellon%")
                | func.lower(Applicant.program).like("%cmu%")
            )
        )
    )

    result = session.scalar(statement)

    print(
        "\nQuestion 8: How many Fall 2026 accepted applicants applied "
        "for a PhD in Computer Science at Georgetown, MIT, Stanford, "
        "or Carnegie Mellon?"
    )
    print(f"Answer: {result}")

    return result


def question_9(session, original_count):
    statement = (
        select(func.count())
        .select_from(Applicant)
        .where(
            func.lower(Applicant.term) == "fall 2026",
            func.lower(Applicant.status) == "accepted",
            func.lower(Applicant.degree).in_(["phd", "ph.d.", "ph.d"]),
            (
                func.lower(Applicant.llm_generated_program).like(
                    "%computer science%"
                )
                | (func.lower(Applicant.llm_generated_program) == "cs")
            ),
            (
                func.lower(Applicant.llm_generated_university).like(
                    "%georgetown%"
                )
                | func.lower(Applicant.llm_generated_university).like(
                    "%massachusetts institute of technology%"
                )
                | (func.lower(Applicant.llm_generated_university) == "mit")
                | func.lower(Applicant.llm_generated_university).like(
                    "%stanford%"
                )
                | func.lower(Applicant.llm_generated_university).like(
                    "%carnegie mellon%"
                )
                | (func.lower(Applicant.llm_generated_university) == "cmu")
            )
        )
    )

    llm_count = session.scalar(statement)
    difference = llm_count - original_count

    print(
        "\nQuestion 9: Repeat Question 8 using the LLM-generated "
        "program and university fields."
    )
    print(f"Original-field count: {original_count}")
    print(f"LLM-generated-field count: {llm_count}")
    print(f"Difference: {difference}")

    if difference != 0:
        print(
            "Explanation: The LLM-standardized fields may normalize "
            "variations in university and program names, which can "
            "change which records match the query."
        )
    else:
        print(
            "Explanation: The original and LLM-generated fields "
            "produced the same count."
        )


def question_10(session):
    statement = (
        select(func.count())
        .select_from(Applicant)
        .where(
            func.lower(Applicant.term) == "fall 2026",
            func.lower(Applicant.status) == "accepted"
        )
    )

    result = session.scalar(statement)

    print("\nQuestion 10: How many Fall 2026 applicants were accepted?")
    print(f"Answer: {result}")


def main():
    with SessionLocal() as session:
        question_1(session)
        question_4(session)
        question_5(session)

        original_count = question_8(session)
        question_9(session, original_count)

        question_10(session)


if __name__ == "__main__":
    main()