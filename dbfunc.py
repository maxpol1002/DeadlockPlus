import json
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

        return exists

    finally:
        cursor.close()
        db_conn.close()


def get_users_uids():
    try:
        db_conn = psycopg2.connect(DB_URL, sslmode="require")
        cursor = db_conn.cursor()
        cursor.execute('SELECT usteamid FROM users')
        rows = cursor.fetchall()
        users_uids = [row[0] for row in rows]

        return users_uids

    finally:
        cursor.close()
        db_conn.close()


def get_user_uid(user_id):
    try:
        db_conn = psycopg2.connect(DB_URL, sslmode="require")
        cursor = db_conn.cursor()
        cursor.execute('SELECT usteamid FROM users WHERE user_id = %s', (user_id,))
        uid = cursor.fetchone()
        if uid:
            return uid[0]

        return None

    finally:
        cursor.close()
        db_conn.close()


def get_user_id(usteamid):
    try:
        db_conn = psycopg2.connect(DB_URL, sslmode="require")
        cursor = db_conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE usteamid = %s', (usteamid,))
        user_id = cursor.fetchone()
        if user_id:
            return user_id[0]

        return None

    finally:
        cursor.close()
        db_conn.close()


def insert_users_matches(matches):
    try:
        db_conn = psycopg2.connect(DB_URL, sslmode="require")
        cursor = db_conn.cursor()
        for match in matches:
            match_data = json.dumps(match)
            cursor.execute('INSERT INTO matches (match_id, data) VALUES (%s, %s) ON CONFLICT (match_id) DO NOTHING',
                           (match.get('match_id'), match_data))

        db_conn.commit()

    finally:
        cursor.close()
        db_conn.close()


def update_user_matches(user_uid, match_id):
    try:
        db_conn = psycopg2.connect(DB_URL, sslmode="require")
        cursor = db_conn.cursor()
        cursor.execute('UPDATE users SET matches_list = matches_list || %s '
                       'WHERE usteamid = %s AND array_position(matches_list, %s) IS NULL',
                       ([match_id], user_uid, match_id))

        db_conn.commit()

    finally:
        cursor.close()
        db_conn.close()


def get_matchids_foruser(user_id):
    try:
        db_conn = psycopg2.connect(DB_URL, sslmode="require")
        cursor = db_conn.cursor()
        cursor.execute('SELECT matches_list FROM users WHERE user_id = %s', (user_id,))
        matchids = cursor.fetchone()
        if matchids:
            return matchids[0]

        return None

    finally:
        cursor.close()
        db_conn.close()


def get_match_data(match_id):
    try:
        db_conn = psycopg2.connect(DB_URL, sslmode="require")
        cursor = db_conn.cursor()
        cursor.execute('SELECT data from matches WHERE match_id = %s', (match_id,))
        match_data = cursor.fetchone()
        if match_data:
            return match_data[0]

        return None

    finally:
        cursor.close()
        db_conn.close()


def get_user_match_count(user_matchids: list, match_mode: int) -> int:
    if not user_matchids:
        return 0

    try:
        db_conn = psycopg2.connect(DB_URL, sslmode="require")
        cursor = db_conn.cursor()
        query = """
            SELECT COUNT(*) FROM matches WHERE match_id = ANY(%s) AND (data ->> 'match_mode') = %s
        """
        cursor.execute(query, (user_matchids, str(match_mode)))
        match_count = cursor.fetchone()[0]

        return match_count

    finally:
        cursor.close()
        db_conn.close()


def remove_user_first_match(user_matchids: list, match_mode: int, user_uid):
    try:
        db_conn = psycopg2.connect(DB_URL, sslmode="require")
        cursor = db_conn.cursor()
        query = """
            SELECT match_id FROM matches WHERE match_id = ANY(%s) AND (data ->> 'match_mode') = %s 
            ORDER BY match_id
        """
        cursor.execute(query, (user_matchids, str(match_mode)))
        match_id = cursor.fetchone()
        if match_id and match_id[0]:
            first_match_id = match_id[0]
            cursor.execute('UPDATE users SET matches_list = array_remove(matches_list, %s) WHERE usteamid = %s',
                           (first_match_id, user_uid))
            db_conn.commit()

            return first_match_id

    finally:
        cursor.close()
        db_conn.close()


def if_any_user_has_match(match_id):
    try:
        db_conn = psycopg2.connect(DB_URL, sslmode="require")
        cursor = db_conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE %s = ANY(matches_list)', (match_id,))
        result = cursor.fetchone()
        if result:
            return True
        return False

    finally:
        cursor.close()
        db_conn.close()


def if_user_has_match(usteamid, match_id):
    try:
        db_conn = psycopg2.connect(DB_URL, sslmode="require")
        cursor = db_conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE usteamid = %s AND %s = ANY(matches_list)', (usteamid, match_id))
        result = cursor.fetchone()
        if result:
            return True
        return False

    finally:
        cursor.close()
        db_conn.close()


def delete_match(match_id):
    try:
        db_conn = psycopg2.connect(DB_URL, sslmode="require")
        cursor = db_conn.cursor()
        cursor.execute('DELETE FROM matches WHERE match_id = %s', (match_id,))
        db_conn.commit()

    finally:
        cursor.close()
        db_conn.close()


def get_all_users_avg_elot():
    users_avg_elo = {}
    query = '''
            WITH max_elo AS (
                SELECT user_id,
                       MAX((matches.data->>'match_elo')::float) AS max_elo
                FROM users
                JOIN LATERAL unnest(users.matches_list) AS u_match_id ON TRUE
                JOIN matches ON matches.match_id = u_match_id
                WHERE (matches.data->>'match_mode')::int = 1
                GROUP BY user_id
            )
            SELECT u.user_id, 
                   AVG((m.data->>'match_elo')::float) AS avg_elo
            FROM users u
            JOIN LATERAL unnest(u.matches_list) AS u_match_id ON TRUE
            JOIN matches m ON m.match_id = u_match_id
            JOIN max_elo me ON me.user_id = u.user_id
            WHERE (m.data->>'match_mode')::int = 1
              AND (m.data->>'match_elo')::float >= me.max_elo - 300
            GROUP BY u.user_id
            HAVING COUNT(CASE WHEN (m.data->>'match_mode')::int = 1 THEN 1 END) >= 10;
        '''

    try:
        db_conn = psycopg2.connect(DB_URL, sslmode="require")
        cursor = db_conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            user_id, avg_elo = row
            users_avg_elo[user_id] = int(avg_elo)

    finally:
        cursor.close()
        db_conn.close()

    return users_avg_elo


