import sqlite3
from basecode.authenticate import hash_password
import streamlit as st
import pandas as pd
import configparser
import os
import ast

config = configparser.ConfigParser()
config.read('config.ini')
DEFAULT_TEXT = config['constants']['DEFAULT_TEXT']
DEFAULT_PASSWORD = st.secrets["default_password"]

# Create or check for the 'database' directory in the current working directory
cwd = os.getcwd()
WORKING_DIRECTORY = os.path.join(cwd, "database")

if not os.path.exists(WORKING_DIRECTORY):
	os.makedirs(WORKING_DIRECTORY)

if st.secrets["sql_ext_path"] == "None":
	WORKING_DATABASE= os.path.join(WORKING_DIRECTORY , st.secrets["default_db"])
else:
	WORKING_DATABASE= st.secrets["sql_ext_path"]

def change_password(username, new_password):
	"""Updates the password for the given username."""
	hashed_pw = hash_password(new_password)
	conn = sqlite3.connect(WORKING_DATABASE)
	cursor = conn.cursor()
	cursor.execute('UPDATE Users SET password = ? WHERE username = ?', (hashed_pw, username))
	st.session_state.user['password'] = hash_password
	conn.commit()
	conn.close()
	st.write("Password changed successfully!")
	

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


def reset_passwords(df):
    # Connect to the SQLite database
    conn = sqlite3.connect(WORKING_DATABASE)
    cursor = conn.cursor()

    # Get unique profiles from the dataframe and ask admin to choose
    profiles = sorted(df['Profile'].unique().tolist())
    selected_profile = st.selectbox("Select a profile:", profiles)

    # Filter the dataframe by profile
    df_filtered = df[df['Profile'] == selected_profile]

    if selected_profile == "student":
        # If the profile is student, provide options for level and class
        levels = sorted(df_filtered['Level'].unique().tolist())
        selected_level = st.selectbox("Select a level:", levels)

        # Filter dataframe further by level
        df_filtered = df_filtered[df_filtered['Level'] == selected_level]

        classes = sorted(df_filtered['Class'].unique().tolist())
        selected_class = st.selectbox("Select a class:", classes)

        # Filter dataframe further by class
        df_filtered = df_filtered[df_filtered['Class'] == selected_class]

    # Note: If the profile is "teacher", it will already show all teachers from the dataframe.

    # Allow user to select accounts from the filtered list
    selected_users = st.multiselect(
        "You may select multiple users - reset password is '{}'".format(DEFAULT_PASSWORD), 
        df_filtered['Username'].tolist()
    )

    reset_password = st.text_input("Please enter a temp password for user: (The default password is given)", DEFAULT_PASSWORD)

    # Handle password reset
    if st.button('Reset Passwords'):
        for user in selected_users:
            # Reset password logic here
            hashed_new_password = hash_password(reset_password)
            cursor.execute('UPDATE Users SET password = ? WHERE username = ?', (hashed_new_password, user))
            st.write(f"Password for {user} has been reset!")

    conn.commit()
    conn.close()
