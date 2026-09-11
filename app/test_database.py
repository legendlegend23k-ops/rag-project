from app.database import get_connection


connection = get_connection()

cursor = connection.cursor()

cursor.execute("""
    CREATE INDEX idx_documents_user_id
    ON documents(user_id)
""")

connection.commit()

connection.close()