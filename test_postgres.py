
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()


def main():
    try:
        with psycopg.connect(
            host=os.environ["INFRA_POSTGRES_HOST"],
            port=os.getenv("INFRA_POSTGRES_PORT", "5432"),
            dbname=os.environ["INFRA_POSTGRES_DBNAME"],
            user=os.environ["INFRA_POSTGRES_USER"],
            password=os.environ["INFRA_POSTGRES_PASS"],
            connect_timeout=10,
        ) as conn:

            print("Connected to PostgreSQL successfully!")

            with conn.cursor() as cursor:

                # 1. Count records in both tables
                print("\n--- Database Record Counts ---")

                cursor.execute(
                    "SELECT COUNT(*) FROM public.plan_document_run;"
                )
                print(
                    "plan_document_run records:",
                    cursor.fetchone()[0],
                )

                cursor.execute(
                    "SELECT COUNT(*) FROM public.plan_life_cycle;"
                )
                print(
                    "plan_life_cycle records:",
                    cursor.fetchone()[0],
                )

                # 2. Latest 10 plans
                cursor.execute("""
                    SELECT
                        id, name, label,
                        document_provider, record_keeper,
                        created_on, last_modified_at
                    FROM public.plan
                    ORDER BY created_on DESC NULLS LAST
                    LIMIT 10;
                """)

                print("\n--- Latest 10 records from public.plan ---")
                for row in cursor.fetchall():
                    print(row)

                # 3. Latest 10 PensionPro-related plans
                cursor.execute("""
                    SELECT
                        id, pp_plan_id, sp_plan_id,
                        tpa_firm_name, plan_status,
                        created_on, last_updated_on
                    FROM public.pp_plan
                    ORDER BY created_on DESC NULLS LAST
                    LIMIT 10;
                """)

                print("\n--- Latest records from public.pp_plan ---")
                rows = cursor.fetchall()

                if rows:
                    for row in rows:
                        print(row)
                else:
                    print("No records found.")

                # 4. Latest 10 document-processing runs
                cursor.execute("""
                    SELECT
                        id, name, employer_name, source,
                        plan_type, run_status, group_run_status,
                        start_time, end_time, created_at
                    FROM public.plan_document_run
                    ORDER BY created_at DESC NULLS LAST
                    LIMIT 10;
                """)

                print(
                    "\n--- Latest 10 records from "
                    "public.plan_document_run ---"
                )

                rows = cursor.fetchall()

                if rows:
                    for row in rows:
                        print(row)
                else:
                    print("No processing runs found.")

                # 5. Latest 10 plan lifecycle records
                cursor.execute("""
                    SELECT
                        id, name, label, plan_category,
                        service_type, record_keeper_firm,
                        document_provider, created_at, is_active
                    FROM public.plan_life_cycle
                    ORDER BY created_at DESC NULLS LAST
                    LIMIT 10;
                """)

                print(
                    "\n--- Latest 10 records from "
                    "public.plan_life_cycle ---"
                )

                rows = cursor.fetchall()

                if rows:
                    for row in rows:
                        print(row)
                else:
                    print("No lifecycle records found.")

        print("\nRead-only inspection completed.")
        print("Database connection closed successfully.")

    except KeyError as error:
        print(f"Missing environment variable: {error}")
        print("Check your .env file.")

    except psycopg.Error as error:
        print("PostgreSQL error:", error)

    except Exception as error:
        print("Unexpected error:", error)


if __name__ == "__main__":
    main()
