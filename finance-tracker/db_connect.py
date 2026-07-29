import os
import psycopg2

try:
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "5432")),
        database=os.environ.get("DB_NAME", "finance_tracker"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", ""),
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print("Подключение успешно! Версия PostgreSQL:", version)
    cur.close()
    conn.close()
except Exception as e:
    print("Ошибка подключения:", e)
