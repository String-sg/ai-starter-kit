import streamlit as st
import configparser
import os
import sqlite3
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
DEFAULT_TEXT = config_handler.get_config_values('constants', 'DEFAULT_TEXT')
PROMPT_TEMPLATES_FUNCTIONS = config_handler.get_config_values('menu_lists', 'PROMPT_TEMPLATES_FUNCTIONS')
SA = config_handler.get_config_values('constants', 'SA')
AD = config_handler.get_config_values('constants', 'AD')

# Create or check for the 'database' directory in the current working directory
cwd = os.getcwd()
WORKING_DIRECTORY = os.path.join(cwd, "database")

if not os.path.exists(WORKING_DIRECTORY):
	os.makedirs(WORKING_DIRECTORY)

if st.secrets["sql_ext_path"] == "None":
	WORKING_DATABASE= os.path.join(WORKING_DIRECTORY , st.secrets["default_db"])
else:
	WORKING_DATABASE= st.secrets["sql_ext_path"]

def bot_settings():
	with st.form(key='sliders_form'):
		# Sliders for settings
		st.write("Current User Bot Settings")
		temp = st.slider("Temp", min_value=0.0, max_value=1.0, value=st.session_state.temp, step=0.01)
		presence_penalty = st.slider("Presence Penalty", min_value=-2.0, max_value=2.0, value=st.session_state.presence_penalty, step=0.01)
		frequency_penalty = st.slider("Frequency Penalty", min_value=-2.0, max_value=2.0, value=st.session_state.frequency_penalty, step=0.01)
		chat_memory = st.slider("Chat Memory", min_value=0, max_value=10, value=st.session_state.k_memory, step=1)	
		# Submit button for the form
		submit_button = st.form_submit_button(label='Submit')

		# If the form is successfully submitted, assign values to session state
		if submit_button:
			st.session_state.temp = temp
			st.session_state.presence_penalty = presence_penalty
			st.session_state.frequency_penalty = frequency_penalty
			st.session_state.k_memory = chat_memory
			st.success("Parameters saved!")

def store_bot_settings(user_id, temp, presence_penalty, frequency_penalty):
    with sqlite3.connect(WORKING_DATABASE) as conn:
        cursor = conn.cursor()
        
        # Check if the user has settings already
        cursor.execute('SELECT user_id FROM BotSettings WHERE user_id = ?', (user_id,))
        
        if cursor.fetchone():
            cursor.execute('''
                UPDATE BotSettings
                SET temp = ?, presence_penalty = ?, frequency_penalty = ?
                WHERE user_id = ?
            ''', (temp, presence_penalty, frequency_penalty, user_id))
        else:
            cursor.execute('''
                INSERT INTO BotSettings (user_id, temp, presence_penalty, frequency_penalty)
                VALUES (?, ?, ?, ?)
            ''', (user_id, temp, presence_penalty, frequency_penalty))
        
        conn.commit()
        
def load_bot_settings(user_id):
    with sqlite3.connect(WORKING_DATABASE) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT temp, presence_penalty, frequency_penalty
            FROM BotSettings WHERE user_id = ?
        ''', (user_id,))
        
        data = cursor.fetchone()

        if data:
            temp, presence_penalty, frequency_penalty = data
            st.session_state.temp = temp
            st.session_state.presence_penalty = presence_penalty
            st.session_state.frequency_penalty = frequency_penalty
            st.success("Bot settings loaded successfully!")
        else:
            st.warning("No bot settings found for this user.")



def propagate_bot_settings(profile_id, temp, presence_penalty, frequency_penalty, selected_school_id):
    with sqlite3.connect(WORKING_DATABASE) as conn:
        cursor = conn.cursor()
        
        users_to_update = []
        if profile_id == SA:
            # For SA, get user IDs in the selected school
            cursor.execute('SELECT user_id FROM Users WHERE school_id = ?', (selected_school_id,))
            users_to_update = cursor.fetchall()
        elif profile_id == AD:
            # For AD, get user IDs in their school
            cursor.execute('SELECT user_id FROM Users WHERE school_id = ?', (selected_school_id,))
            users_to_update = cursor.fetchall()

        # Iterate through each user and perform upsert
        for user in users_to_update:
            cursor.execute('''
                INSERT OR REPLACE INTO BotSettings (user_id, temp, presence_penalty, frequency_penalty)
                VALUES (?, ?, ?, ?)
            ''', (user[0], temp, presence_penalty, frequency_penalty))

        conn.commit()



def bot_settings_interface(profile_id, school_id=None):
	with st.form(key='sliders_form'):
		# Sliders for settings
		temp = st.slider("Temp", min_value=0.0, max_value=1.0, value=float(st.session_state.temp), step=0.01)
		presence_penalty = st.slider("Presence Penalty", min_value=-2.0, max_value=2.0, value=float(st.session_state.presence_penalty), step=0.01)
		frequency_penalty = st.slider("Frequency Penalty", min_value=-2.0, max_value=2.0, value=float(st.session_state.frequency_penalty), step=0.01)

		should_propagate = False
		if profile_id in [SA, AD]:
			should_propagate = st.checkbox("Propagate these settings to all users?")

		# Submit button for the form
		submit_button = st.form_submit_button(label='Submit')
		if submit_button:
			st.session_state.temp = temp
			st.session_state.presence_penalty = presence_penalty
			st.session_state.frequency_penalty = frequency_penalty
			store_bot_settings(st.session_state.user['id'], temp, presence_penalty, frequency_penalty)
			st.success("Parameters saved!")
			if should_propagate:
				with sqlite3.connect(WORKING_DATABASE) as conn:
					cursor = conn.cursor()

					# Logic for handling SA and AD profiles:
					if profile_id == SA:
						# Fetch all schools for SA to select from
						cursor.execute("SELECT school_id, school_name FROM Schools")
						schools = cursor.fetchall()
						school_choices = {school[1]: school[0] for school in schools}
						selected_school_name = st.selectbox("Select School for Propagation:", list(school_choices.keys()))
						if selected_school_name == None:
							st.error("Please create a new school first.")
						else:	
							selected_school_id = school_choices[selected_school_name]
							propagate_bot_settings(profile_id, temp, presence_penalty, frequency_penalty, selected_school_id)
							st.success("Propagate complete")
						
					elif profile_id == AD:
						# AD can only propagate to their school, so no need for a selectbox
						selected_school_id = school_id
						st.write(f"You're set to propagate settings to school with ID: {school_id}")
						selected_school_id = school_choices[selected_school_name]
						propagate_bot_settings(profile_id, temp, presence_penalty, frequency_penalty, selected_school_id)
						st.success("Propagate complete")
