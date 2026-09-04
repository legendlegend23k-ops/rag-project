from app.database import get_connection


connection = get_connection()

cursor = connection.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY,
        filename TEXT NOT NULL
    )
""")

cursor.execute("""
    INSERT INTO documents (filename)
    VALUES (?)
""", ("example.pdf",))

connection.commit()

print("Document inserted.")

connection.close()