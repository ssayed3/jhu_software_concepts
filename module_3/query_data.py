
import os

import psycopg


DB_NAME = "module3_db"
DB_USER = os.getenv("DB_USER", "sayedsayed")


def connect_to_database():
    return psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER
    )


def question_1(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE LOWER(term) = 'fall 2026';
        """)

        result = cur.fetchone()[0]

    print("Question 1: How many entries applied for Fall 2026?")
    print(f"Answer: {result}")


def question_2(conn):
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
            FROM applicants;
        """)

        result = cur.fetchone()[0]

    print("\nQuestion 2: What percentage of applicants are international?")
    print(f"Answer: {result:.2f}%")


def question_3(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                AVG(gpa),
                AVG(gre),
                AVG(gre_v),
                AVG(gre_aw)
            FROM applicants;
        """)

        avg_gpa, avg_gre, avg_gre_v, avg_gre_aw = cur.fetchone()

    print("\nQuestion 3: What are the average GPA and GRE scores?")
    print(f"Average GPA: {avg_gpa:.2f}")
    print(f"Average GRE Quantitative: {avg_gre:.2f}")
    print(f"Average GRE Verbal: {avg_gre_v:.2f}")
    print(f"Average GRE Analytical Writing: {avg_gre_aw:.2f}")


def question_4(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT AVG(gpa)
            FROM applicants
            WHERE LOWER(term) = 'fall 2026'
              AND LOWER(us_or_international) = 'american'
              AND gpa IS NOT NULL;
        """)

        result = cur.fetchone()[0]

    print("\nQuestion 4: What is the average GPA of American applicants for Fall 2026?")
    print(f"Answer: {result:.2f}")


def question_5(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                100.0 * COUNT(*) FILTER (
                    WHERE LOWER(status) = 'accepted'
                )
                / NULLIF(COUNT(*), 0)
            FROM applicants
            WHERE LOWER(term) = 'fall 2025';
        """)

        result = cur.fetchone()[0]

    print("\nQuestion 5: What percentage of Fall 2025 applications were accepted?")
    print(f"Answer: {result:.2f}%")


def question_6(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT AVG(gpa)
            FROM applicants
            WHERE LOWER(term) = 'fall 2026'
              AND LOWER(status) = 'accepted'
              AND gpa IS NOT NULL;
        """)

        result = cur.fetchone()[0]

    print("\nQuestion 6: What is the average GPA of accepted applicants for Fall 2026?")
    print(f"Answer: {result:.2f}")


def question_7(conn):
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
            );
        """)

        result = cur.fetchone()[0]

    print("\nQuestion 7: How many applicants applied to a Johns Hopkins master's program in Computer Science?")
    print(f"Answer: {result}")


def question_8(conn):
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
                    OR LOWER(program) LIKE '%massachusetts institute of technology%'
                    OR LOWER(program) LIKE '% mit,%'
                    OR LOWER(program) LIKE '%stanford%'
                    OR LOWER(program) LIKE '%carnegie mellon%'
                    OR LOWER(program) LIKE '%cmu%'
              );
        """)

        result = cur.fetchone()[0]

    print("\nQuestion 8: How many Fall 2026 accepted applicants applied for a PhD in Computer Science at Georgetown, MIT, Stanford, or Carnegie Mellon?")
    print(f"Answer: {result}")

    return result


def question_9(conn, original_count):
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
                    OR LOWER(llm_generated_university) LIKE '%massachusetts institute of technology%'
                    OR LOWER(llm_generated_university) = 'mit'
                    OR LOWER(llm_generated_university) LIKE '%stanford%'
                    OR LOWER(llm_generated_university) LIKE '%carnegie mellon%'
                    OR LOWER(llm_generated_university) = 'cmu'
              );
        """)

        llm_count = cur.fetchone()[0]

    difference = llm_count - original_count

    print("\nQuestion 9: Repeat Question 8 using the LLM-generated program and university fields.")
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
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE LOWER(term) = 'fall 2026'
              AND LOWER(status) = 'accepted';
        """)

        result = cur.fetchone()[0]

    print("\nQuestion 10: How many Fall 2026 applicants were accepted?")
    print(f"Answer: {result}")


def question_11(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT AVG(gpa)
            FROM applicants
            WHERE LOWER(term) = 'fall 2026'
              AND LOWER(us_or_international) = 'international'
              AND gpa IS NOT NULL;
        """)

        result = cur.fetchone()[0]

    print("\nQuestion 11: What is the average GPA of international applicants for Fall 2026?")
    print(f"Answer: {result:.2f}")
    
def main():
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


if __name__ == "__main__":
    main()


