from queries import authenticate_user

def check_auth():
    # Assuming password is 'password' or similar. I'll try to find a user with a known password or just check the DB directly.
    # Actually, I can just query the user by username directly to see what authenticate_user would return if password matched.
    from queries import execute_sql
    user = execute_sql("SELECT * FROM users WHERE username = 'user04'")
    if user:
        print(f"User: {user[0]}")
        print(f"Role type: {type(user[0]['role'])}")
        print(f"Role value: '{user[0]['role']}'")
    else:
        print("User not found")

if __name__ == "__main__":
    check_auth()