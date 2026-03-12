from database import get_connection

def save_message(username, room, message):

    conn = get_connection()

    cursor = conn.cursor()

    query = """
    INSERT INTO messages (username, room, message)
    VALUES (%s, %s, %s)
    """

    cursor.execute(query, (username, room, message))

    conn.commit()

    cursor.close()
    conn.close()