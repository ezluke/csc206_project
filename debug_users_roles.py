from db import get_connection

def check_users():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT username, role FROM users")
    users = cursor.fetchall()
    print("Users and Roles:")
    for user in users:
        print(f"User: {user['username']}, Role: '{user['role']}'")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_users()