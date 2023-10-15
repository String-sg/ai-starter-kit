import sqlite3
from authenticate import hash_password
import streamlit as st
import pandas as pd
import configparser
config = configparser.ConfigParser()
config.read('config.ini')
STK_PROMPT_TEMPLATES = config['menu_lists']['STK_PROMPT_TEMPLATES']
DEFAULT_TEXT = config['constants']['DEFAULT_TEXT']
DEFAULT_PASSWORD = config['constants']['DEFAULT_PASSWORD']

def create_dbs():
	# Connect to the SQLite database
	conn = sqlite3.connect(st.session_state.db_path)
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
			class TEXT,
			sch TEXT,
			org TEXT,
			level TEXT
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


def create_admin_account():
	conn = sqlite3.connect(st.session_state.db_path)
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
	conn = sqlite3.connect(st.session_state.db_path)
	cursor = conn.cursor()
	cursor.execute('UPDATE user_accounts SET password = ? WHERE username = ?', (hashed_pw, username))
	conn.commit()
	conn.close()
	st.write("Password changed successfully!")

def check_accounts_exist():
	"""Check if teacher and student accounts exist."""
	conn = sqlite3.connect(st.session_state.db_path)
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
	conn = sqlite3.connect(st.session_state.db_path)
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
	conn = sqlite3.connect(st.session_state.db_path)
	cursor = conn.cursor()
	# Create teacher accounts
	for i in range(1, 6):
		username = f"tch{i}"
		password = hash_password(f"pwd_tch{i}")
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
	conn = sqlite3.connect(st.session_state.db_path)
	cursor = conn.cursor()

	# Fetch the user accounts and their profiles from the database
	cursor.execute('SELECT username, profile FROM user_accounts')
	users = cursor.fetchall()

	# Convert the fetched user accounts and profiles into a pandas DataFrame
	df = pd.DataFrame(users, columns=["Username", "Profile"])
	st.dataframe(df)  # Display the accounts

	# Allow user to select accounts
	selected_users = st.multiselect(
		f"'You may select multiple users to reset password - reset password is '{DEFAULT_PASSWORD}'", 
		df['Username'].tolist()
	)

	# Handle password reset
	if st.button('Reset Passwords'):
		for user in selected_users:
			# Reset password logic here
			hashed_new_password = hash_password(DEFAULT_PASSWORD)
			cursor.execute('UPDATE user_accounts SET password = ? WHERE username = ?', (hashed_new_password, user))
			st.write(f"Password for {user} has been reset!")

	conn.commit()
	conn.close()

#Current template - link to the function of the application 

def create_prompt_template(username, admin_flag):
	with sqlite3.connect(st.session_state.db_path) as conn:
		cursor = conn.cursor()

		# Fetch all templates for the given user
		cursor.execute('''
			SELECT prompt_name, prompt_text FROM prompt_templates WHERE username = ?
		''', (username,))
		templates = cursor.fetchall()
		template_names = [template[0] for template in templates]

		# Default to the first template name for the user if available
		current_template = template_names[0] if template_names else None

		# Display Streamlit form
		with st.form(key="my_form"):
			st.write("Username:", username)

			# Replace text_input with selectbox for prompt_name
			selected_template_name = st.selectbox("Select a template name", template_names, index=0 if current_template else None)

			# Update current_template_profile based on the selected prompt name
			current_template_profile = next((template[1] for template in templates if template[0] == selected_template_name), '')

			prompt_text = st.text_area("Prompt Template", current_template_profile)

			update_all = False
			if admin_flag:
				update_all = st.checkbox("Update all users using the above prompt templates")
				
			submit_button = st.form_submit_button(label="Submit")

		# Check if fields are blank and form has been submitted
		if submit_button:
			if selected_template_name and prompt_text:
				cursor.execute('''
					SELECT * FROM prompt_templates WHERE username = ? AND prompt_name = ?
				''', (username, selected_template_name))
				
				result = cursor.fetchone()
				if result:
					# Update if username and template name exists
					cursor.execute('''
						UPDATE prompt_templates
						SET prompt_text = ?
						WHERE username = ? AND prompt_name = ?
					''', (prompt_text, username, selected_template_name))
				else:
					# Insert a new row if template doesn't exist for the user
					cursor.execute('''
						INSERT INTO prompt_templates (prompt_name, prompt_text, username)
						VALUES (?, ?, ?)
					''', (selected_template_name, prompt_text, username))
				
				conn.commit()

				# Update the session state profile with the latest template text
				for template in st.session_state.user['prompt_templates']:
					if template['name'] == selected_template_name:
						template['text'] = prompt_text
						break
				else:
					st.session_state.user['prompt_templates'].append({'name': selected_template_name, 'text': prompt_text})

				st.write("Successfully saved the template")
				if update_all:
					update_all_prompt_templates()
				return True
			else:
				st.write("Ensure that none of the fields are blank!")


def load_user_profile(username):
	with sqlite3.connect(st.session_state.db_path) as conn:
		cursor = conn.cursor()
		
		# Query to get user details
		cursor.execute('''
			SELECT * FROM user_accounts WHERE username = ?
		''', (username,))
		user_details = cursor.fetchone()
		
		# If user details are not found
		if not user_details:
			st.write("User not found!")
			return None

		# Query to get all prompt templates for the user
		cursor.execute('''
			SELECT prompt_name, prompt_text FROM prompt_templates WHERE username = ?
		''', (username,))
		prompt_templates = cursor.fetchall()

		# Ensure the user has all standard templates, adding default ones if necessary
		user_template_names = [template[0] for template in prompt_templates]
		for prompt_name in STK_PROMPT_TEMPLATES:
			if prompt_name not in user_template_names:
				prompt_templates.append((prompt_name, DEFAULT_TEXT))

		# Constructing the user profile
		profile = {
			"id": user_details[0],
			"username": user_details[1],
			"password": user_details[2],
			"profile": user_details[3],
			"class": user_details[4],
			"sch": user_details[5],
			"org": user_details[6],
			"level": user_details[7],
			"prompt_templates": [{'name': template[0], 'text': template[1]} for template in prompt_templates]
		}

		return profile



# def load_user_profile(username):
# 	with sqlite3.connect(st.session_state.db_path) as conn:
# 		cursor = conn.cursor()
		
# 		# Query to get user details
# 		cursor.execute('''
# 			SELECT * FROM user_accounts WHERE username = ?
# 		''', (username,))
# 		user_details = cursor.fetchone()
		
# 		# If user details are not found
# 		if not user_details:
# 			st.write("User not found!")
# 			return None

# 		# Query to get all prompt templates for the user
# 		cursor.execute('''
# 			SELECT prompt_name, prompt_text FROM prompt_templates WHERE username = ?
# 		''', (username,))
# 		prompt_templates = cursor.fetchall()

# 		# Constructing the user profile
# 		profile = {
# 			"id": user_details[0],
# 			"username": user_details[1],
# 			"password": user_details[2],
# 			"group": user_details[3],
# 			"org": user_details[4],
# 			"grade": user_details[5],
# 			"profile": user_details[6],
# 			"default_bot": user_details[7],
# 			"prompt_templates": [{'name': template[0], 'text': template[1]} for template in prompt_templates]
# 		}

# 		return profile


# def update_all_prompt_templates():
# 	# Extract data from session state
# 	username_from_session = st.session_state.prompt_profile["username"]
# 	current_name = st.session_state.prompt_profile["template_name"]
# 	current_template = st.session_state.prompt_profile["prompt_data"]
	
# 	with sqlite3.connect(st.session_state.db_path) as conn:
# 		cursor = conn.cursor()
# 		cursor.execute('SELECT username FROM user_accounts')  # Fetch all usernames from the user_accounts table
# 		all_users = cursor.fetchall()
		
# 		for user in all_users:
# 			username = user[0]  # Unpack the tuple
			
# 			# Skip the original user, since we've already saved for them
# 			if username != username_from_session:
# 				cursor.execute('''
# 					SELECT * FROM prompt_templates WHERE username = ?
# 				''', (username,))
				
# 				result = cursor.fetchone()
# 				if result:
# 					# Update if username exists
# 					cursor.execute('''
# 						UPDATE prompt_templates
# 						SET prompt_name = ?, prompt_text = ?
# 						WHERE username = ?
# 					''', (current_name, current_template, username))
# 				else:
# 					# Insert a new row if username doesn't exist
# 					cursor.execute('''
# 						INSERT INTO prompt_templates (prompt_name, prompt_text, username)
# 						VALUES (?, ?, ?)
# 					''', (current_name, current_template, username))
# 		conn.commit()
# 	st.write(f"Successfully updated templates for all users except {username_from_session}!")

#this function only for administrator
def update_all_prompt_templates():
	# Extract data from session state
	username_from_session = st.session_state.user["username"]
	current_template = [template for template in st.session_state.user["prompt_templates"] if template["name"] == st.session_state.user["template_name"]]
	
	# Ensure that a template was found in the session state
	if not current_template:
		st.write("Error: Template not found in session state!")
		return
	current_name = current_template[0]["name"]
	current_text = current_template[0]["text"]

	with sqlite3.connect(st.session_state.db_path) as conn:
		cursor = conn.cursor()
		cursor.execute('SELECT username FROM user_accounts')  # Fetch all usernames from the user_accounts table
		all_users = cursor.fetchall()

		for user in all_users:
			username = user[0]  # Unpack the tuple
			
			# Skip the original user, since we've already saved for them
			if username != username_from_session:
				cursor.execute('''
					SELECT * FROM prompt_templates WHERE username = ? AND prompt_name = ?
				''', (username, current_name))
				
				result = cursor.fetchone()
				if result:
					# Update if username and template name exists
					cursor.execute('''
						UPDATE prompt_templates
						SET prompt_text = ?
						WHERE username = ? AND prompt_name = ?
					''', (current_text, username, current_name))
				else:
					# Insert a new row if username doesn't have this template
					cursor.execute('''
						INSERT INTO prompt_templates (prompt_name, prompt_text, username)
						VALUES (?, ?, ?)
					''', (current_name, current_text, username))
		conn.commit()
	st.write(f"Successfully updated templates for all users except {username_from_session}!")
