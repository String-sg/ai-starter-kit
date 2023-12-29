import sqlite3
from basecode.authenticate import hash_password
from basecode.database_module import populate_functions
import streamlit as st
import time
import pandas as pd
import configparser
import os
import ast

class ConfigHandler:
	def __init__(self):
		self.config = configparser.ConfigParser()
		self.config.read('config.ini')

	def get_config_values(self, section, key):
		value = self.config.get(section, key)
		try:
			# Try converting the string value to a Python data structure
			return ast.literal_eval(value)
		except (SyntaxError, ValueError):
			# If not a data structure, return the plain string
			return value

config_handler = ConfigHandler()
SUPER_PWD = st.secrets["super_admin_password"]
SUPER = st.secrets["super_admin"]
STU_PASS = st.secrets["student_password"]
TCH_PASS = st.secrets["teacher_password"]
DEFAULT_TEXT = config_handler.get_config_values('constants', 'DEFAULT_TEXT')
STK_PROMPT_TEMPLATES = config_handler.get_config_values('menu_lists', 'STK_PROMPT_TEMPLATES')
# Fetching constants from config.ini
TCH = config_handler.get_config_values('constants', 'TCH')
STU = config_handler.get_config_values('constants', 'STU')
SA = config_handler.get_config_values('constants', 'SA')
AD = config_handler.get_config_values('constants', 'AD')
ALL_ORG = config_handler.get_config_values('constants', 'ALL_ORG')
MODE = config_handler.get_config_values('constants', 'MODE')
SCH_PROFILES = config_handler.get_config_values('menu_lists', 'SCH_PROFILES')
EDU_ORGS = config_handler.get_config_values('menu_lists', 'EDU_ORGS')
MENU_FUNCS = config_handler.get_config_values('menu_lists', 'MENU_FUNCS')


# Create or check for the 'database' directory in the current working directory
cwd = os.getcwd()
WORKING_DIRECTORY = os.path.join(cwd, "database")

if not os.path.exists(WORKING_DIRECTORY):
	os.makedirs(WORKING_DIRECTORY)

if st.secrets["sql_ext_path"] == "None":
	WORKING_DATABASE= os.path.join(WORKING_DIRECTORY , st.secrets["default_db"])
else:
	WORKING_DATABASE= st.secrets["sql_ext_path"]

def has_at_least_two_rows():
	# Connect to the SQLite database
	with sqlite3.connect(WORKING_DATABASE) as conn:
		cursor = conn.cursor()

		# Query to check the number of records in the user_accounts table
		cursor.execute('SELECT COUNT(*) FROM Users')
		count = cursor.fetchone()[0]

		
	# Return True if the table has at least two rows, otherwise return False
	return count

#set initialise 
def initialise_database():
	pass

def initialise_admin_account():
	conn = sqlite3.connect(WORKING_DATABASE)
	cursor = conn.cursor()

	try:
		# Check if the super_admin account exists
		cursor.execute('SELECT 1 FROM Users WHERE username = ?', (SUPER,))
		admin_account_exists = cursor.fetchone()
		cursor.execute("SELECT COUNT(*) FROM App_Functions")
		count = cursor.fetchone()[0]
		if count == 0:
			populate_functions(MENU_FUNCS)
		if admin_account_exists:
			return
		#populate_functions(MENU_FUNCS)
		# Insert organizations into the Organizations table and retrieve their IDs
		org_ids = {}
		for org in EDU_ORGS:
			cursor.execute('INSERT OR IGNORE INTO Organizations (org_name) VALUES (?)', (org,))
			cursor.execute('SELECT org_id FROM Organizations WHERE org_name = ?', (org,))
			org_ids[org] = cursor.fetchone()[0]

		# Insert profiles into the profile table
		for profile in SCH_PROFILES:
			cursor.execute('INSERT OR IGNORE INTO Profile (profile_name) VALUES (?)', (profile,))
			cursor.execute('SELECT profile_id FROM Profile WHERE profile_name = ?', (profile,))
			profile_id = cursor.fetchone()[0]
			
			# Link each profile to the organizations in the Profile_Link table
			for org in EDU_ORGS:
				cursor.execute('INSERT OR IGNORE INTO Profile_Link (profile_id, org_id) VALUES (?, ?)', (profile_id, org_ids[org]))

		# Create the super_admin account (assuming this logic remains the same)
		cursor.execute('''
			INSERT INTO Users
			(username, password, profile_id, org_id) 
			VALUES (?, ?, ?, ?)
		''', (SUPER, hash_password(SUPER_PWD), SA, ALL_ORG))

		print("super_admin account created")
		conn.commit()
	except Exception as e:
		print(f"An error occurred: {e}")
		conn.rollback()  # Rollback the transaction if an error occurred
	finally:
		conn.close()


def load_user_profile(username):
	with sqlite3.connect(WORKING_DATABASE) as conn:
		cursor = conn.cursor()

		# Fetch user details directly with IDs
		cursor.execute('''
			SELECT u.user_id, u.username, u.profile_id,
				   u.school_id, u.class_id, u.org_id, u.level_id
			FROM Users u
			WHERE u.username = ?
		''', (username,))
		
		user_details = cursor.fetchone()

		# If user details are not found
		if not user_details:
			st.write("User not found!")
			return None

		# Constructing the user profile with direct IDs
		profile = {
			"id": user_details[0],          # user_id
			"username": user_details[1],
			"profile_id": user_details[2],
			"school_id": user_details[3],
			"class_id": user_details[4],
			"org_id": user_details[5],
			"level_id": user_details[6],
		}

		return profile

def display_accounts(school_id):
	# Connect to the SQLite database
	conn = sqlite3.connect(WORKING_DATABASE)
	cursor = conn.cursor()

	# Fetch user accounts within the specified school (excluding the columns id, default_vs, and password)
	cursor.execute('''
		SELECT u.user_id, u.username, 
			p.profile_name AS profile_name,
			COALESCE(s.school_name, "N/A") AS school_name,
			COALESCE(c.class_name, "N/A") AS class_name,
			COALESCE(l.level_name, "N/A") AS level_name,  
			o.org_name AS org_name
		FROM Users u
		LEFT JOIN Profile p ON u.profile_id = p.profile_id
		LEFT JOIN Schools s ON u.school_id = s.school_id
		LEFT JOIN Levels l ON u.level_id = l.level_id
		LEFT JOIN Classes c ON u.class_id = c.class_id
		LEFT JOIN Organizations o ON u.org_id = o.org_id
		WHERE u.school_id = ?
	''', (school_id,))

	users = cursor.fetchall()

	# Convert the fetched user data into a pandas DataFrame
	columns = ["User ID", "Username", "Profile", "School", "Level", "Class", "Organisation"]
	df = pd.DataFrame(users, columns=columns)
	st.dataframe(df)  # Display the accounts

	conn.close()

	return df



def create_org_structure():
	with sqlite3.connect(WORKING_DATABASE) as conn:
		cursor = conn.cursor()

		# Org selection
		org_query = "SELECT org_name FROM Organizations"
		cursor.execute(org_query)
		orgs = cursor.fetchall()
		org_names = [org[0] for org in orgs]
		org_name = st.selectbox("Select an organization:", org_names)

		# Collect user inputs
		school_name = st.text_input("Enter a school name:")
		num_levels = st.number_input("Enter number of levels in the school:", min_value=1, value=1)

		level_names = [st.text_input(f"Enter name for Level {i + 1}:") for i in range(num_levels)]
		num_classes_per_level = [st.number_input(f"Enter number of classes for Level {i + 1}:", min_value=1, value=1) for i in range(num_levels)]
		class_names = [[st.text_input(f"Enter name for Class {j + 1} in Level {i + 1}:") for j in range(num_classes_per_level[i])] for i in range(num_levels)]
		num_students_per_class = [[st.number_input(f"Enter number of students for Class {j + 1} in Level {i + 1}:", min_value=1, value=1) for j in range(num_classes_per_level[i])] for i in range(num_levels)]
		
		num_teachers = st.number_input("Enter number of teachers for the school:", min_value=1, value=1)

		# When the submit button is pressed
		if st.button('Submit'):
			# Check if school with the same name already exists for the organization
			cursor.execute("SELECT school_name FROM Schools WHERE LOWER(school_name) = ?", (school_name.lower(),))
			existing_school = cursor.fetchone()

			if existing_school:
				st.warning(f"School {school_name} already exists. Please choose a different name")
				

			else:
				cursor.execute("INSERT INTO Schools (org_id, school_name) VALUES ((SELECT org_id FROM Organizations WHERE org_name = ?), ?)", (org_name, school_name))
				student_counter = 1
				for i, level_name in enumerate(level_names):
					cursor.execute("INSERT INTO Levels (org_id, school_id, level_name) VALUES ((SELECT org_id FROM Organizations where org_name = ?),(SELECT school_id FROM Schools WHERE school_name = ?), ?)", (org_name, school_name, level_name))
					for j, class_name in enumerate(class_names[i]):
						cursor.execute("INSERT INTO Classes (org_id, school_id, level_id, class_name) VALUES ((SELECT org_id FROM Organizations where org_name = ?),(SELECT school_id FROM Schools WHERE school_name = ?),(SELECT level_id FROM Levels WHERE level_name = ?), ?)", (org_name, school_name, level_name, class_name))
						school_id_query = "SELECT school_id FROM Schools WHERE school_name = ?"
						cursor.execute(school_id_query, (school_name,))
						school_id = cursor.fetchone()[0]
						
						for k in range(num_students_per_class[i][j]):
							student_username = f"stu{school_id}_{student_counter}"
							cursor.execute("INSERT INTO Users (username, password, profile_id, school_id, class_id, org_id, level_id) VALUES (?, ?, ?, ?, (SELECT class_id FROM Classes WHERE class_name = ?), (SELECT org_id FROM Organizations WHERE org_name = ?), (SELECT level_id FROM Levels WHERE level_name = ?))", (student_username, hash_password(STU_PASS),STU, school_id, class_name, org_name, level_name))
							student_counter += 1
				for t in range(num_teachers):
					teacher_username = f"tch{school_id}_{t + 1}"
					cursor.execute("INSERT INTO Users (username, password, profile_id, school_id, org_id) VALUES (?, ?, ?, ?, (SELECT org_id FROM Organizations WHERE org_name = ?))", (teacher_username, hash_password(TCH_PASS), TCH, school_id, org_name))

				conn.commit()
				st.success("Data inserted successfully!")
				st.rerun()


def check_multiple_schools():
	with sqlite3.connect(WORKING_DATABASE) as conn:
		cursor = conn.cursor()
		cursor.execute("SELECT COUNT(*) FROM Schools")
		num_schools = cursor.fetchone()[0]
		if MODE == 2 and num_schools > 1: # MODE 2 is for multiple schools
			return False
		elif num_schools > 1:# Other MODES is for single school
			return True
		else:# No schools created yet
			return False
		
def remove_or_reassign_teacher_ui(school_id):
	"""
	Display the UI for assigning, removing, or reassigning teachers to/from classes in Streamlit.

	:param WORKING_DATABASE: Path to the SQLite database file.
	:param school_id: The ID of the school to which teachers should be restricted.
	"""

	st.title("Assign, Remove, or Reassign Teachers to/from Classes")

	with sqlite3.connect(WORKING_DATABASE) as conn:
		cursor = conn.cursor()

		show_unassigned = st.checkbox("Show unassigned teachers")

		if show_unassigned:
			# Fetch teachers not assigned to any class in the specified school
			cursor.execute("""
				SELECT username FROM Users
				WHERE school_id = ? AND profile_id = ? AND user_id NOT IN (SELECT teacher_id FROM Teacher_Assignments)
			""", (school_id, TCH))
			unassigned_teachers = [teacher[0] for teacher in cursor.fetchall()]
			selected_teacher = st.selectbox("Select Unassigned Teacher:", unassigned_teachers)
		else:
			# Fetch teachers currently assigned to classes from the specified school
			cursor.execute("""
				SELECT DISTINCT u.username
				FROM Users u
				JOIN Teacher_Assignments ta ON u.user_id = ta.teacher_id
				WHERE u.school_id = ?
			""", (school_id,))
			assigned_teachers = [teacher[0] for teacher in cursor.fetchall()]
			selected_teacher = st.selectbox("Select Teacher to Remove or Reassign:", assigned_teachers)

			# Once a teacher is selected, fetch and display the classes assigned to that teacher
			if selected_teacher:
				cursor.execute("""
					SELECT c.class_name
					FROM Classes c
					JOIN Teacher_Assignments ta ON c.class_id = ta.class_id
					JOIN Users u ON ta.teacher_id = u.user_id
					WHERE u.username = ? AND u.school_id = ?
				""", (selected_teacher, school_id))
				assigned_classes_to_teacher = [class_[0] for class_ in cursor.fetchall()]
				st.write(f"Classes currently assigned to {selected_teacher}: {', '.join(assigned_classes_to_teacher)}")

		remove_assignment = st.checkbox("Remove teacher from all classes")

		if not remove_assignment:
			# Fetching classes from the specified school
			cursor.execute("SELECT class_name FROM Classes WHERE school_id = ?", (school_id,))
			all_classes = [class_[0] for class_ in cursor.fetchall()]
			selected_classes = st.multiselect("Select Classes (For Reassignment or Assignment):", all_classes, default=all_classes[0])

		st.markdown("---")
		btn_process = st.button("Process Teacher")

		if btn_process:
			cursor.execute("SELECT user_id FROM Users WHERE username = ?", (selected_teacher,))
			teacher_record = cursor.fetchone()
			if teacher_record is None:
				st.write("Teacher not found!")
				return
				# Handle the case where there's no matching teacher, maybe return or raise a custom exception
			else:
				teacher_id = cursor.fetchone()[0]

			if remove_assignment:
				# Remove teacher from all currently assigned classes
				cursor.execute("DELETE FROM Teacher_Assignments WHERE teacher_id = ?", (teacher_id,))
				cursor.execute("UPDATE Users SET class_id = NULL WHERE user_id = ?", (teacher_id,))
			else:
				if not selected_classes:
					# Remove teacher from all currently assigned classes
					# cursor.execute("DELETE FROM Teacher_Assignments WHERE teacher_id = ?", (teacher_id,))
					return

				# If classes are selected for reassignment or assignment, assign teacher to those classes
				for index, new_class in enumerate(selected_classes):
					cursor.execute("SELECT class_id, level_id FROM Classes WHERE class_name = ?", (new_class,))
					class_data = cursor.fetchone()
					class_id, level_id = class_data
					
					# Check if the teacher is already assigned to this class
					cursor.execute("""
						SELECT COUNT(*)
						FROM Teacher_Assignments
						WHERE teacher_id = ? AND class_id = ?
					""", (teacher_id, class_id))
					already_assigned = cursor.fetchone()[0] > 0

					# If not already assigned, then proceed with the assignment
					if not already_assigned:
						cursor.execute("INSERT INTO Teacher_Assignments(teacher_id, school_id, level_id, class_id) VALUES (?, ?, ?, ?)", (teacher_id, school_id, level_id, class_id))

						# Update the first class to the Users table if it's the first class in the list
						if index == 0:
							cursor.execute("UPDATE Users SET class_id = ? WHERE user_id = ?", (class_id, teacher_id))

			conn.commit()
			st.success(f"Teacher {selected_teacher} has been processed successfully!")




def change_teacher_profile_ui(school_id):
	"""
	Display the UI for changing the profile of teachers in a specific school.

	:param school_id: The ID of the school.
	"""
	st.title("Change Teacher Profiles")

	with sqlite3.connect(WORKING_DATABASE) as conn:
		cursor = conn.cursor()

		# Fetch all profile names and their IDs excluding the 'STU' profile
		cursor.execute("SELECT profile_id, profile_name FROM Profile WHERE profile_id != ? AND profile_id != ?", (STU,SA))
		profiles_data = cursor.fetchall()
		profile_id_to_name = {id: name for id, name in profiles_data}
		profile_name_to_id = {name: id for id, name in profiles_data}

		# Get profile_ids that match the SCH_PROFILES list
		sch_profile_ids = [profile_name_to_id[profile_name] for profile_name in SCH_PROFILES if profile_name in profile_name_to_id]

		# Fetch all teachers within the given school that have a profile in SCH_PROFILES
		cursor.execute("""
			SELECT user_id, username, profile_id 
			FROM Users 
			WHERE school_id = ? AND profile_id IN ({})
		""".format(','.join('?' * len(sch_profile_ids))), [school_id] + sch_profile_ids)
		teachers = cursor.fetchall()

		# If no teachers are found
		if not teachers:
			st.write("No teachers found for this school!")
			return

		# Store the selected profile for each teacher
		teacher_profile_selections = {}

		# Display all teachers with a selectbox for changing their profile
		for teacher in teachers:
			user_id, username, current_profile_id = teacher
			selected_profile_name = st.selectbox(
				f"Change profile for {username}",
				options=list(profile_name_to_id.keys()),
				index=list(profile_id_to_name.keys()).index(current_profile_id),
				key=username
			)
			teacher_profile_selections[user_id] = profile_name_to_id[selected_profile_name]

		# If a button is pressed, update the selected teachers' profiles
		if st.button("Update Profiles"):
			for user_id, new_profile_id in teacher_profile_selections.items():
				cursor.execute("""
					UPDATE Users
					SET profile_id = ?
					WHERE user_id = ?
				""", (new_profile_id, user_id))
			conn.commit()
			st.success("Teacher profiles updated successfully!")




def reassign_student_ui(school_id):
	"""
	Display the UI for reassigning students from one class to another in Streamlit.

	:param WORKING_DATABASE: Path to the SQLite database file.
	:param STU: Global variable for student's profile_id.
	:param school_id: The ID of the school to which students are to be reassigned.
	"""

	st.title("Reassign Students to Another Class")

	with sqlite3.connect(WORKING_DATABASE) as conn:
		cursor = conn.cursor()

		# Fetching all levels within the school
		cursor.execute("SELECT DISTINCT level_id FROM Classes WHERE school_id = ?", (school_id,))
		all_levels = [level[0] for level in cursor.fetchall()]
		selected_level = st.selectbox("Select Level:", all_levels)

		# Fetching all classes within the selected level and school
		cursor.execute("SELECT class_name FROM Classes WHERE school_id = ? AND level_id = ?", (school_id, selected_level))
		all_classes_in_level = [class_[0] for class_ in cursor.fetchall()]
		selected_class = st.selectbox("Select Class:", all_classes_in_level)

		# Fetching students from the selected class and level
		cursor.execute("SELECT username FROM Users WHERE profile_id = ? AND school_id = ? AND class_id IN (SELECT class_id FROM Classes WHERE class_name = ?)", (STU, school_id, selected_class))
		students_in_class = [student[0] for student in cursor.fetchall()]
		selected_students = st.multiselect("Select Students to Reassign:", students_in_class)

		st.markdown("---")

		# Fetching all classes within the same school for reassignment (excluding the currently selected class)
		cursor.execute("SELECT class_name FROM Classes WHERE school_id = ? AND class_name != ?", (school_id, selected_class))
		all_classes_for_reassignment = [class_[0] for class_ in cursor.fetchall()]
		new_class = st.selectbox("Select New Class for Reassignment:", all_classes_for_reassignment)

		btn_reassign = st.button("Reassign Students")

		if btn_reassign:
			# Fetching class_id for the selected new class
			cursor.execute("SELECT class_id FROM Classes WHERE class_name = ?", (new_class,))
			new_class_id = cursor.fetchone()[0]

			for student in selected_students:
				cursor.execute("SELECT user_id FROM Users WHERE username = ?", (student,))
				student_id = cursor.fetchone()[0]

				# Update student's class_id to the new class
				cursor.execute("UPDATE Users SET class_id = ? WHERE user_id = ?", (new_class_id, student_id))

			conn.commit()
			st.success(f"Selected students have been reassigned to {new_class} successfully!")


def process_user_profile(profile_name):
	"""
	Process a user profile to determine the school_id based on profile_name.

	:param profile_name: The profile_name of the user.
	:return: school_id or None, and possibly a user-friendly message.
	"""
	with sqlite3.connect(WORKING_DATABASE) as conn:
		cursor = conn.cursor()

		if profile_name == SA:   # Using the global SA constant
			# Fetch all organization names directly
			cursor.execute('SELECT org_name FROM Organizations')
			all_organization_names = cursor.fetchall()

			# Assuming st.selectbox is from Streamlit for user input.
			org_name_selected = st.selectbox("Choose an Organization:", [org[0] for org in all_organization_names])
			
			# Fetch the org_id based on the org_name
			cursor.execute('SELECT org_id FROM Organizations WHERE org_name = ?', (org_name_selected,))
			org_id = cursor.fetchone()[0]
			
			# Fetch schools associated with the selected org_id
			cursor.execute('SELECT school_name FROM Schools WHERE org_id = ?', (org_id,))
			schools_in_org = cursor.fetchall()

			# If no schools found
			if not schools_in_org:
				return None, "No schools found for the selected organization. Please create a school first."

			school_selected = st.selectbox("Choose a School within the Organization:", [school[0] for school in schools_in_org])

			# Fetch the school_id for the selected school
			cursor.execute('SELECT school_id FROM Schools WHERE school_name = ?', (school_selected,))
			school_id = cursor.fetchone()[0]

			return school_id, f"Selected school ID: {school_id} within Organization: {org_name_selected}"
		else:   # Using the global AD constant
			return st.session_state.user["school_id"], f"User's school ID: {st.session_state.user['school_id']}"

#this is the interface for the addition of school
def add_level(school_id):
	st.subheader("Add Level")
	with sqlite3.connect(WORKING_DATABASE) as conn:
		cursor = conn.cursor()
		
		# Retrieve org_id based on school_id
		cursor.execute("SELECT org_id FROM Schools WHERE school_id = ?", (school_id,))
		org_id = cursor.fetchone()[0]

		# Collect inputs
		level_name = st.text_input("Enter level name:")
		
		if st.button('Add Level'):
			# Check if level with the same name already exists for the school
			cursor.execute("SELECT level_name FROM Levels WHERE school_id = ? AND level_name = ?", (school_id, level_name))
			existing_level = cursor.fetchone()
			
			if existing_level:
				st.warning(f"Level {level_name} already exists for this school. Please choose a different name.")
			else:
				cursor.execute("INSERT INTO Levels (org_id, school_id, level_name) VALUES (?, ?, ?)", (org_id, school_id, level_name))
				conn.commit()
				st.success("Level added successfully!")

				
#------------------------------------------------------------------------------------------------add later -------------------------------------------------
#this is the interface for the addition of class
def add_class(school_id):
	st.subheader("Add Class")
	with sqlite3.connect(WORKING_DATABASE) as conn:
		cursor = conn.cursor()
		
		# Retrieve org_id based on school_id
		cursor.execute("SELECT org_id FROM Schools WHERE school_id = ?", (school_id,))
		org_id = cursor.fetchone()[0]

		# Retrieve available levels for the school
		cursor.execute("SELECT DISTINCT level_name FROM Levels WHERE school_id = ?", (school_id,))
		available_levels = [level[0] for level in cursor.fetchall()]

		# Collect inputs
		level_name = st.selectbox("Select level:", available_levels)
		class_name = st.text_input("Enter class name:")
		
		if st.button('Add Class'):
			# Check if class with the same name already exists for the selected level and school
			cursor.execute("SELECT class_name FROM Classes WHERE school_id = ? AND level_id = (SELECT level_id FROM Levels WHERE level_name = ? AND school_id = ?) AND class_name = ?", (school_id, level_name, school_id, class_name))
			existing_class = cursor.fetchone()
			
			if existing_class:
				st.warning(f"Class {class_name} already exists for this level and school. Please choose a different name.")
			else:
				cursor.execute("INSERT INTO Classes (org_id, school_id, level_id, class_name) VALUES (?, ?, (SELECT level_id FROM Levels WHERE level_name = ? AND school_id = ?), ?)", (org_id, school_id, level_name, school_id, class_name))
				conn.commit()
				st.success("Class added successfully!")

#this is the interface for the addition of users
def add_user(school_id):
	try: 
		st.subheader("Add User")
		with sqlite3.connect(WORKING_DATABASE) as conn:
			cursor = conn.cursor()

			# Retrieve org_id based on school_id
			cursor.execute("SELECT org_id FROM Schools WHERE school_id = ?", (school_id,))
			org_id = cursor.fetchone()[0]

			# Determine type of user to add
			user_type = st.selectbox("Select user type:", ["Teacher", "Student"])

			# Capture common inputs
			username = st.text_input(f"Enter {user_type.lower()} username (Do not put tch1/stu1 at the start as it will be appended automatically):")

			if user_type == "Teacher":
				if st.button(f'Add {user_type}'):
					teacher_username = f"tch{school_id}_{username}"
					cursor.execute("INSERT INTO Users (username, password, profile_id, school_id, org_id) VALUES (?, ?, ?, ?, ?)", (teacher_username, hash_password(TCH_PASS), TCH, school_id, org_id))
					conn.commit()
					st.success(f"{user_type} added successfully!")
			
			elif user_type == "Student":
				# Retrieve available classes for the school
				cursor.execute("SELECT class_name FROM Classes WHERE school_id = ?", (school_id,))
				available_classes = [cls[0] for cls in cursor.fetchall()]
				class_name = st.selectbox("Select class:", available_classes)

				if st.button(f'Add {user_type}'):
					student_username = f"stu{school_id}_{username}"
					cursor.execute("INSERT INTO Users (username, password, profile_id, school_id, class_id, org_id, level_id) VALUES (?, ?, ?, ?, (SELECT class_id FROM Classes WHERE class_name = ? AND school_id = ?), ?, (SELECT level_id FROM Levels WHERE level_name = (SELECT level_name FROM Classes WHERE class_name = ? AND school_id = ?) AND school_id = ?))", 
								(student_username, hash_password(STU_PASS), STU, school_id, class_name, school_id, org_id, class_name, school_id, school_id))
					conn.commit()
					st.success(f"{user_type} added successfully!")
	except Exception as e:
		st.write("An error occurred:", 	e)


def display_options(cursor, table_name, column_name, previous_conditions=[]):
	query = f"SELECT DISTINCT {column_name} FROM {table_name} WHERE 1=1"
	for condition in previous_conditions:
		query += f" AND {condition}"
	cursor.execute(query)
	results = cursor.fetchall()
	options = [result[0] for result in results]
	return st.selectbox(f"Select from {table_name}", options)


def remove_user(school_id):
	#not working yet
	st.subheader("Remove Users")
	conn = sqlite3.connect(WORKING_DATABASE)
	cursor = conn.cursor()

	# Fetch all users except the super_admin and the current user
	cursor.execute("SELECT user_id, username FROM Users WHERE school_id=? AND user_id NOT IN (?)", (school_id, 1))
	users = cursor.fetchall()

	if not users:
		st.write("No users available for deletion.")
		return

	user_options = [user[1] for user in users]
	selected_user = st.selectbox("Select User", user_options)
	user_id = [user[0] for user in users if user[1] == selected_user][0]
	

	if st.button(f"Delete User with ID {user_id}"):
		confirmation = st.checkbox("Are you sure? This action cannot be undone.")

		if confirmation:
			try:
				# Delete or handle dependent records in other tables first
				cursor.execute("DELETE FROM Teacher_Assignments WHERE teacher_id=?", (user_id,))
				cursor.execute("DELETE FROM Data_Table WHERE user_id=?", (user_id,))
				cursor.execute("DELETE FROM Files WHERE user_id=?", (user_id,))
				cursor.execute("DELETE FROM Vector_Stores WHERE user_id=?", (user_id,))
				cursor.execute("DELETE FROM Prompt_Templates WHERE user_id=?", (user_id,))
				cursor.execute("DELETE FROM App_Functions_Link WHERE user_id=?", (user_id,))
				cursor.execute("DELETE FROM BotSettings WHERE user_id=?", (user_id,))
				cursor.execute("DELETE FROM User_VectorStores WHERE user_id=?", (user_id,))
				#Finally, delete the user
				cursor.execute("DELETE FROM Users WHERE username=?", ("tch1_tch1_18",))

				conn.commit()
				st.write("User Deleted Successfully!")
			except sqlite3.Error as e:
				st.write("An error occurred:", e)
				conn.rollback()
			finally:
				conn.close()
		else:
			st.write("Deletion cancelled.")

def delete_if_no_association(cursor, table_name, column_name, value):
	""" Check if a value has no associated records """
	associated_tables = {
		"Schools": ["Levels", "Classes", "Users"],
		"Levels": ["Classes", "Users"],
		"Classes": ["Users"]
	}

	for associated_table in associated_tables.get(table_name, []):
		cursor.execute(f"SELECT COUNT(*) FROM {associated_table} WHERE {column_name}=?", (value,))
		count = cursor.fetchone()[0]
		if count > 0:
			return False
	
	cursor.execute(f"DELETE FROM {table_name} WHERE {column_name}=?", (value,))
	return True

def delete_class(class_id):
	with sqlite3.connect(WORKING_DATABASE) as conn:
		cursor = conn.cursor()
		success = delete_if_no_association(cursor, "Classes", "class_id", class_id)
		return "Class Deleted Successfully!" if success else "Cannot delete: Class has associated records."

def delete_level(level_id):
	with sqlite3.connect(WORKING_DATABASE) as conn:
		cursor = conn.cursor()
		success = delete_if_no_association(cursor, "Levels", "level_id", level_id)
		return "Level Deleted Successfully!" if success else "Cannot delete: Level has associated records."

def delete_school(school_id):
	with sqlite3.connect(WORKING_DATABASE) as conn:
		cursor = conn.cursor()
		success = delete_if_no_association(cursor, "Schools", "school_id", school_id)
		return "School Deleted Successfully!" if success else "Cannot delete: School has associated records."
def get_values_from_table(table_name, column_name):
	""" Fetch values from a given table and column """
	with sqlite3.connect(WORKING_DATABASE) as conn:
		cursor = conn.cursor()
		cursor.execute(f"SELECT DISTINCT {column_name} FROM {table_name}")
		return [item[0] for item in cursor.fetchall()]
	
#this is the interface for the delete class, levels or schools 
def streamlit_delete_interface():
	st.title("Delete Records")

	choice = st.selectbox("Which entity do you want to delete?", ["Class", "Level", "School"])
	
	if choice == "Class":
		class_ids = get_values_from_table("Classes", "class_id")
		selected_class = st.selectbox("Choose a Class to delete:", class_ids)
		if st.button("Delete Class"):
			result = delete_class(selected_class)
			st.write(result)

	elif choice == "Level":
		level_ids = get_values_from_table("Levels", "level_id")
		selected_level = st.selectbox("Choose a Level to delete:", level_ids)
		if st.button("Delete Level"):
			result = delete_level(selected_level)
			st.write(result)

	elif choice == "School":
		school_ids = get_values_from_table("Schools", "school_id")
		selected_school = st.selectbox("Choose a School to delete:", school_ids)
		if st.button("Delete School"):
			result = delete_school(selected_school)
			st.write(result)
