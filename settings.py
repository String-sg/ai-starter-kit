import sqlite3
import streamlit as st
import hashlib
import pandas as pd
import os

# Create or check for the 'database' directory in the current working directory
cwd = os.getcwd()
database_path = os.path.join(cwd, "database")

if not os.path.exists(database_path):
    os.makedirs(database_path)

# Set DB_NAME to be within the 'database' directory
DB_NAME = os.path.join(database_path, st.secrets["default_db"])


def create_dbs():
	# Connect to the SQLite database
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()

	# Conversation data table
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS data_table (
			id INTEGER PRIMARY KEY,
			date TEXT NOT NULL UNIQUE,
			username TEXT NOT NULL,
			profile TEXT NOT NULL,
			chatbot_ans TEXT NOT NULL,
			user_prompt TEXT NOT NULL,
			tokens TEXT
		)
	''')


	# User accounts table
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS user_accounts (
			id INTEGER PRIMARY KEY,
			username TEXT NOT NULL UNIQUE,
			password TEXT NOT NULL,
			profile TEXT NOT NULL,
			default_bot TEXT    
		)
	''')

	# Storing of files in SQLIte table note the name here refers to file names
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS files
		(id INTEGER PRIMARY KEY, 
		username TEXT NOT NULL, 
		name TEXT NOT NULL,		
		data BLOB NOT NULL,
		metadata TEXT NOT NULL
		)
	''')

	# Store class objects in SQLite table storing of vector stores so that students need not generate their vectorstore
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS vector_dbs
		(id INTEGER PRIMARY KEY, 
		class_name TEXT NOT NULL, 
		data BLOB NOT NULL,
		username TEXT NOT NULL,
		UNIQUE(class_name, username)
		)
	''')

	# Storing of files in SQLIte table for the prompt templates
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS prompt_templates (
			id INTEGER PRIMARY KEY,
			prompt_name TEXT NOT NULL,
			prompt_text TEXT NOT NULL, 
			username TEXT NOT NULL
		)
	''') 
	conn.commit()
	conn.close()




def hash_password(password):
	"""Hashes a password using SHA-256."""
	return hashlib.sha256(password.encode()).hexdigest()

# def check_password(username, password):
#     """Checks if the password matches the stored password."""
#     hashed_password = hash_password(password)
#     cursor.execute('SELECT password FROM user_accounts WHERE username = ?', (username,))
#     stored_password = cursor.fetchone()
#     if stored_password and hashed_password == stored_password[0]:
#         return True
#     return False

def check_password(username, password):
	"""Checks if the password matches the stored password and sets the profile in session state."""
	hashed_password = hash_password(password)
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	
	# Fetch both the password and profile for the given username
	cursor.execute('SELECT password, profile FROM user_accounts WHERE username = ?', (username,))
	result = cursor.fetchone()
	conn.commit()
	conn.close()
	# Check if the result exists and the hashed password matches the stored password
	if result and hashed_password == result[0]:
		# Set the user's profile in the session state
		st.session_state.user = {
			'username': username,
			'profile': result[1]
		}
		
		return True
	return False

def create_admin_account():
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	cursor.execute('SELECT 1 FROM user_accounts WHERE username = "administrator"')
	admin_account_exists = cursor.fetchone()
	if admin_account_exists:
		conn.close()
		pass
	else:
		cursor.execute('INSERT INTO user_accounts (username, password, profile) VALUES (?, ?, ?)', ("administrator", hash_password("pass1234"), "administrator"))
		print("administrator account created")
		conn.commit()
		conn.close()


def change_password(username, new_password):
	"""Updates the password for the given username."""
	hashed_pw = hash_password(new_password)
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	cursor.execute('UPDATE user_accounts SET password = ? WHERE username = ?', (hashed_pw, username))
	conn.commit()
	conn.close()
	st.write("Password changed successfully!")

def check_accounts_exist():
	"""Check if teacher and student accounts exist."""
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	
	# Checking teacher accounts
	for i in range(1, 6):
		username = f"tch{i}"
		cursor.execute('SELECT 1 FROM user_accounts WHERE username = ?', (username,))
		if cursor.fetchone() is None:
			conn.commit()
			conn.close()
			return False
	
	# Checking student accounts
	for i in range(1, 41):
		username = f"stu{i}"
		cursor.execute('SELECT 1 FROM user_accounts WHERE username = ?', (username,))
		if cursor.fetchone() is None:
			conn.commit()
			conn.close()
			return False
	conn.close()
	return True

def check_setup():
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	cursor.execute('SELECT 1 FROM user_accounts WHERE username = "administrator"')
	admin_account_exists = cursor.fetchone()
	if admin_account_exists:
		cursor.execute('SELECT password FROM user_accounts WHERE username = "administrator"')
		admin_password = cursor.fetchone()[0]
		conn.commit()
		conn.close()
		if admin_password == hash_password("pass1234"):
			st.write("To start creating your teachers account, please change the password of your administrator account")
			if password_settings("administrator"):
				if create_teachers_and_students():
					display_accounts()
		else:
			display_accounts()
	


def password_settings(username):
	st.subheader("Change Password")

	# Form to change password
	with st.form(key='change_password_form'):
		st.write("Username: ", username)
		new_password = st.text_input("New Password", type="password", max_chars=16)
		repeat_new_password = st.text_input("Repeat New Password", type="password", max_chars=16)
		submit_button = st.form_submit_button("Change Password")

		# On submit, check if new passwords match and then update the password.
		if submit_button:
			if new_password != repeat_new_password:
				st.error("New password and repeat new password do not match.")
				return False
			else:
				change_password(username, new_password)
				return True


def create_teachers_and_students():
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	# Create teacher accounts
	for i in range(1, 6):
		username = f"tch{i}"
		password = hash_password("pass1234")
		cursor.execute('INSERT INTO user_accounts (username, password, profile) VALUES (?, ?, ?)', (username, password, "teacher"))
	
	# Create student accounts
	for i in range(1, 41):
		username = f"stu{i}"
		password = hash_password(f"pwd{i}")
		cursor.execute('INSERT INTO user_accounts (username, password, profile) VALUES (?, ?, ?)', (username, password, "student"))
	
	conn.commit()
	conn.close()
	st.write("Teacher and student accounts created successfully!")
	return True


def display_accounts():
	# Connect to the SQLite database
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()

	# Fetch the user accounts and their profiles from the database
	cursor.execute('SELECT username, profile FROM user_accounts')
	users = cursor.fetchall()

	# Convert the fetched user accounts and profiles into a pandas DataFrame
	df = pd.DataFrame(users, columns=["Username", "Profile"])
	st.dataframe(df)  # Display the accounts

	# Allow user to select accounts
	selected_users = st.multiselect(
		"'You may select multiple users to reset password - reset password is 'default_password'", 
		df['Username'].tolist()
	)

	# Handle password reset
	if st.button('Reset Passwords'):
		for user in selected_users:
			# Reset password logic here
			hashed_new_password = hash_password("default_password")
			cursor.execute('UPDATE user_accounts SET password = ? WHERE username = ?', (hashed_new_password, user))
			st.write(f"Password for {user} has been reset!")

	conn.commit()
	conn.close()


def create_prompt_template(username, current_name, current_template):
	with sqlite3.connect(DB_NAME) as conn:
		cursor = conn.cursor()
		
		# Display Streamlit form
		with st.form(key="my_form"):
			st.write("Username:", username)
			prompt_name = st.text_input("Name of template", current_name)
			prompt_text = st.text_area("Prompt Template", current_template)
			submit_button = st.form_submit_button(label="Submit")

		# Check if fields are blank and form has been submitted
		if submit_button:
			if prompt_name and prompt_text:
				cursor.execute('''
					SELECT * FROM prompt_templates WHERE username = ?
				''', (username,))
				
				result = cursor.fetchone()
				if result:
					# Update if username exists
					cursor.execute('''
						UPDATE prompt_templates
						SET prompt_name = ?, prompt_text = ?
						WHERE username = ?
					''', (prompt_name, prompt_text, username))
				else:
					# Insert a new row if username doesn't exist
					cursor.execute('''
						INSERT INTO prompt_templates (prompt_name, prompt_text, username)
						VALUES (?, ?, ?)
					''', (prompt_name, prompt_text, username))
				conn.commit()
				saved = {
					"username": username,
					"template_name": prompt_name,
					"prompt_data": prompt_text
				}
				st.session_state.prompt_profile = saved
				st.write("Successfully saved the template")
				update_all_prompt_templates()
				return True
			else:
				st.write("Ensure that none of the fields are blank!")

# Function to load the current template
def load_current_template(username):
	with sqlite3.connect(DB_NAME) as conn:
		cursor = conn.cursor()
		
		cursor.execute('''
			SELECT * FROM prompt_templates WHERE username = ?
		''', (username,))
		
		result = cursor.fetchone()
		
		if result:
			data = {
				"username": result[3],
				"template_name": result[1],
				"prompt_data": result[2]
			}
		else:
			data = {
				"username": st.session_state.user["username"],
				"template_name": "default",
				"prompt_data": "You are a helpful assistant"
			}
		
	return data

def update_all_prompt_templates():
    # Extract data from session state
    username_from_session = st.session_state.prompt_profile["username"]
    current_name = st.session_state.prompt_profile["template_name"]
    current_template = st.session_state.prompt_profile["prompt_data"]
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM user_accounts')  # Fetch all usernames from the user_accounts table
        all_users = cursor.fetchall()
        
        for user in all_users:
            username = user[0]  # Unpack the tuple
            
            # Skip the original user, since we've already saved for them
            if username != username_from_session:
                cursor.execute('''
                    SELECT * FROM prompt_templates WHERE username = ?
                ''', (username,))
                
                result = cursor.fetchone()
                if result:
                    # Update if username exists
                    cursor.execute('''
                        UPDATE prompt_templates
                        SET prompt_name = ?, prompt_text = ?
                        WHERE username = ?
                    ''', (current_name, current_template, username))
                else:
                    # Insert a new row if username doesn't exist
                    cursor.execute('''
                        INSERT INTO prompt_templates (prompt_name, prompt_text, username)
                        VALUES (?, ?, ?)
                    ''', (current_name, current_template, username))
        conn.commit()
    st.write(f"Successfully updated templates for all users except {username_from_session}!")
