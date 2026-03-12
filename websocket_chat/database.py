import mysql.connector

def get_connection():

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="242002",   # change to your password
        database="websocket"
    )

    return conn