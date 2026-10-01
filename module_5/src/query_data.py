
"""Run SQL queries to analyze applicant data stored in PostgreSQL."""

from psycopg import sql

from src.db_config import get_psycopg_connection


def connect_to_database():
    """Create and return a connection to the PostgreSQL database."""
    return get_psycopg_connection()

def question_1(conn):
    """Count applications submitted for Fall 2026."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE LOWER(term) = 'fall 2026'
            LIMIT 1;
        """)

        result = cur.fetchone()[0]

    print("Question 1: How many entries applied for Fall 2026?")
    print(f"Answer: {result}")


def question_2(conn):
    """Calculate the percentage of international applicants."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                100.0 * COUNT(*) FILTER (
                    WHERE LOWER(us_or_international) = 'international'
                )
                / NULLIF(COUNT(*) FILTER (
                    WHERE us_or_international IS NOT NULL
                    AND TRIM(us_or_international) <> ''
                ), 0)
            FROM applicants
            LIMIT 1;
        """)

        result = cur.fetchone()[0]

    print("\nQuestion 2: What percentage of applicants are international?")
    print(f"Answer: {result:.2f}%")


def question_3(conn):
    """Calculate average GPA and GRE scores for all applicants."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                AVG(gpa),
                AVG(gre),
                AVG(gre_v),
                AVG(gre_aw)
            FROM applicants
            LIMIT 1;
        """)

        avg_gpa, avg_gre, avg_gre_v, avg_gre_aw = cur.fetchone()

    print("\nQuestion 3: What are the average GPA and GRE scores?")
    print(f"Average GPA: {avg_gpa:.2f}")
    print(f"Average GRE Quantitative: {avg_gre:.2f}")
    print(f"Average GRE Verbal: {avg_gre_v:.2f}")
    print(f"Average GRE Analytical Writing: {avg_gre_aw:.2f}")


def question_4(conn):
    """Calculate the average GPA of American Fall 2026 applicants."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT AVG(gpa)
            FROM applicants
            WHERE LOWER(term) = 'fall 2026'
              AND LOWER(us_or_international) = 'american'
              AND gpa IS NOT NULL
            LIMIT 1;
        """)

        result = cur.fetchone()[0]

    print(
        "\nQuestion 4: What is the average GPA of American "
        "applicants for Fall 2026?"
    )
    print(f"Answer: {result:.2f}")


def question_5(conn):
    """Calculate the acceptance percentage for Fall 2025 applications."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                100.0 * COUNT(*) FILTER (
                    WHERE LOWER(status) = 'accepted'
                )
                / NULLIF(COUNT(*), 0)
            FROM applicants
            WHERE LOWER(term) = 'fall 2025'
            LIMIT 1;
        """)

        result = cur.fetchone()[0]

    print(
        "\nQuestion 5: What percentage of Fall 2025 "
        "applications were accepted?"
    )
    print(f"Answer: {result:.2f}%")


def question_6(conn):
    """Calculate the average GPA of accepted Fall 2026 applicants."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT AVG(gpa)
            FROM applicants
            WHERE LOWER(term) = 'fall 2026'
              AND LOWER(status) = 'accepted'
              AND gpa IS NOT NULL
            LIMIT 1;
        """)

        result = cur.fetchone()[0]

    print(
        "\nQuestion 6: What is the average GPA of accepted "
        "applicants for Fall 2026?"
    )
    print(f"Answer: {result:.2f}")


def question_7(conn):
    """Count Johns Hopkins master's Computer Science applicants."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE (
                LOWER(program) LIKE '%johns hopkins%'
                OR LOWER(program) LIKE '%jhu%'
            )
            AND (
                LOWER(program) LIKE '%computer science%'
                OR LOWER(program) LIKE '% cs%'
            )
            AND (
                LOWER(degree) LIKE '%master%'
                OR LOWER(degree) IN ('ms', 'm.s.', 'msc', 'm.sc.')
            )
            LIMIT 1;
        """)

        result = cur.fetchone()[0]

    print(
        "\nQuestion 7: How many applicants applied to a Johns Hopkins "
        "master's program in Computer Science?"
    )
    print(f"Answer: {result}")


def question_8(conn):
    """Count selected accepted Fall 2026 PhD Computer Science applicants."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE LOWER(term) = 'fall 2026'
              AND LOWER(status) = 'accepted'
              AND LOWER(degree) IN ('phd', 'ph.d.', 'ph.d')
              AND (
                    LOWER(program) LIKE '%computer science%'
                    OR LOWER(program) LIKE '% cs%'
              )
              AND (
                    LOWER(program) LIKE '%georgetown%'
                    OR LOWER(program) LIKE
                        '%massachusetts institute of technology%'
                    OR LOWER(program) LIKE '% mit,%'
                    OR LOWER(program) LIKE '%stanford%'
                    OR LOWER(program) LIKE '%carnegie mellon%'
                    OR LOWER(program) LIKE '%cmu%'
              )
            LIMIT 1;
        """)

        result = cur.fetchone()[0]

    print(
        "\nQuestion 8: How many Fall 2026 accepted applicants applied "
        "for a PhD in Computer Science at Georgetown, MIT, Stanford, "
        "or Carnegie Mellon?"
    )
    print(f"Answer: {result}")

    return result


def question_9(conn, original_count):
    """Repeat Question 8 using the LLM-generated standardized fields."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE LOWER(term) = 'fall 2026'
              AND LOWER(status) = 'accepted'
              AND LOWER(degree) IN ('phd', 'ph.d.', 'ph.d')
              AND (
                    LOWER(llm_generated_program) LIKE '%computer science%'
                    OR LOWER(llm_generated_program) = 'cs'
              )
              AND (
                    LOWER(llm_generated_university) LIKE '%georgetown%'
                    OR LOWER(llm_generated_university) LIKE
                        '%massachusetts institute of technology%'
                    OR LOWER(llm_generated_university) = 'mit'
                    OR LOWER(llm_generated_university) LIKE '%stanford%'
                    OR LOWER(llm_generated_university) LIKE
                        '%carnegie mellon%'
                    OR LOWER(llm_generated_university) = 'cmu'
              )
            LIMIT 1;
        """)

        llm_count = cur.fetchone()[0]

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
            "Explanation: The LLM-standardized fields may normalize variations "
            "in university and program names, which can change which records "
            "match the query."
        )
    else:
        print(
            "Explanation: The original and LLM-generated fields produced "
            "the same count for this query."
        )


def question_10(conn):
    """Count accepted Fall 2026 applicants."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE LOWER(term) = 'fall 2026'
              AND LOWER(status) = 'accepted'
            LIMIT 1;
        """)

        result = cur.fetchone()[0]

    print("\nQuestion 10: How many Fall 2026 applicants were accepted?")
    print(f"Answer: {result}")


def question_11(conn):
    """Calculate the average GPA of international Fall 2026 applicants."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT AVG(gpa)
            FROM applicants
            WHERE LOWER(term) = 'fall 2026'
              AND LOWER(us_or_international) = 'international'
              AND gpa IS NOT NULL
            LIMIT 1;
        """)

        result = cur.fetchone()[0]

    print(
        "\nQuestion 11: What is the average GPA of international "
        "applicants for Fall 2026?"
    )
    print(f"Answer: {result:.2f}")

def clamp_limit(limit):
    """Clamp a requested query limit to the allowed range of 1 to 100."""
    return max(1, min(int(limit), 100))

def get_applicants(conn, limit=10):
    """Return applicants while enforcing a safe maximum result limit."""
    safe_limit = clamp_limit(limit)

    statement = sql.SQL(
        """
        SELECT
            program,
            status,
            term,
            degree,
            url
        FROM applicants
        LIMIT %s;
        """
    )

    with conn.cursor() as cur:
        cur.execute(statement, (safe_limit,))
        rows = cur.fetchall()

    return rows

def get_applicant_by_url(conn, url):
    """Return an applicant matching the given URL, or None if not found."""
    statement = sql.SQL(
        """
        SELECT
            program,
            status,
            term,
            degree,
            url
        FROM applicants
        WHERE url = %s
        LIMIT 1;
        """
    )

    with conn.cursor() as cur:
        cur.execute(statement, (url,))
        row = cur.fetchone()

    if row is None:
        return None

    return {
        "program": row[0],
        "status": row[1],
        "term": row[2],
        "degree": row[3],
        "url": row[4]
    }


def main():
    """Run all applicant analysis queries in sequence."""
    with connect_to_database() as conn:
        question_1(conn)
        question_2(conn)
        question_3(conn)
        question_4(conn)
        question_5(conn)
        question_6(conn)
        question_7(conn)

        original_count = question_8(conn)
        question_9(conn, original_count)

        question_10(conn)
        question_11(conn)


if __name__ == "__main__":  # pragma: no cover
    main()
