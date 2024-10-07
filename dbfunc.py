import os

import psycopg2


DB_URL = os.getenv('DATABASE_URL')


def users_table_insert(user_id: int, name: str, username: str, steam_link: str, usteamid: int, comm_id: int):
    try:
        db_conn = psycopg2.connect(DB_URL, sslmode="require")
        cursor = db_conn.cursor()
        cursor.execute('INSERT INTO users (user_id, name, username, steam_link, usteamid, comm_id) '
                       'VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING',
                       (user_id, name, username, steam_link, usteamid, comm_id))

        db_conn.commit()

    except Exception as e:
        db_conn.rollback()

    finally:
        cursor.close()
        db_conn.close()


def is_user_registered(user_id: int):
    try:
        db_conn = psycopg2.connect(DB_URL, sslmode="require")
        cursor = db_conn.cursor()
        cursor.execute('SELECT EXISTS(SELECT 1 FROM users WHERE user_id = %s)', (user_id,))
        exists = cursor.fetchone()[0]

    finally:
        cursor.close()
        db_conn.close()

    return exists
