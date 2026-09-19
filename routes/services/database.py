import os
import mysql.connector


def get_db_connection():
    db_host = os.getenv("DB_HOST")

    # LOCAL MYSQL
    if not db_host:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="Raushan@2nd",
            database="arogyacare"
        )

    # AIVEN / PRODUCTION MYSQL
    return mysql.connector.connect(
        host=db_host,
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "defaultdb"),
        ssl_verify_cert=False,
        ssl_verify_identity=False
    )


def safe_close(cursor=None, connection=None):
    try:
        if cursor:
            cursor.close()
    except Exception:
        pass

    try:
        if connection:
            connection.close()
    except Exception:
        pass