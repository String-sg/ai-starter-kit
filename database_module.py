import sqlite3
import streamlit as st
import pandas as pd
import os


# Create or check for the 'database' directory in the current working directory
cwd = os.getcwd()
WORKING_DIRECTORY = os.path.join(cwd, "database")

if not os.path.exists(WORKING_DIRECTORY):
	os.makedirs(WORKING_DIRECTORY)

if st.secrets["sql_ext_path"] == "None":
	WORKING_DATABASE= os.path.join(WORKING_DIRECTORY , st.secrets["default_db"])
else:
	WORKING_DATABASE= st.secrets["sql_ext_path"]

def delete_tables():
	# Connect to the SQLite database
	conn = sqlite3.connect(WORKING_DATABASE)
	cursor = conn.cursor()

	# Fetch all table names from the database
	cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
	tables = cursor.fetchall()
	table_names = [table[0] for table in tables if table[0] != "sqlite_sequence"]  # "sqlite_sequence" is a system table

	# Display tables and allow selection
	selected_tables = st.multiselect("Select tables you want to drop", table_names)

	# Display caution message and confirmation button
	st.warning("**Warning:** Dropping tables will remove all their data permanently!")
	confirm_drop = st.checkbox("I understand the consequences. Proceed to drop selected tables.")
	drop_button = st.button("Drop Tables")

	if drop_button and confirm_drop:
		for table_name in selected_tables:
			cursor.execute(f"DROP TABLE {table_name};")
			st.write(f"Table {table_name} dropped successfully!")
		conn.commit()

	conn.close()
	

def manage_tables():
    # Connect to the SQLite database
    conn = sqlite3.connect(WORKING_DATABASE)

    # Fetch all table names in the database
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = [table[0] for table in cursor.fetchall()]

    # Dropdown for table selection
    selected_table = st.selectbox("Select a table:", table_names)

    # Fetch data from the selected table
    query = f"SELECT * FROM {selected_table}"
    df = pd.read_sql_query(query, conn)

    # Allow the user to edit data
    edited_df = st.data_editor(df, num_rows="dynamic")

    # Button to sync changes back to the database
    if st.button("Sync changes to database"):
        # Clear the existing data from the selected table
        cursor.execute(f"DELETE FROM {selected_table}")

        # Insert the edited data back into the table
        edited_df.to_sql(selected_table, conn, if_exists='append', index=False)

        st.write("Data successfully synced to the database!")

    conn.close()

    return edited_df

def populate_functions(descriptions_dict):
    # Connect to the SQLite database
    conn = sqlite3.connect(WORKING_DATABASE)
    cursor = conn.cursor()

    # Populate App_Functions table
    for func, description in descriptions_dict.items():
        cursor.execute('''
            INSERT INTO App_Functions (function_name, function_description) 
            VALUES (?, ?)
        ''', (func, description))

    # Commit and close the database connection
    conn.commit()
    conn.close()

def link_users_to_app_function_ui(school_id):
    """
    Display the UI for linking users to specific app functions in Streamlit based on filter.

    :param school_id: The ID of the school to filter the users.
    """

    st.title("Link Users to App Functions Based on Filter")

    with sqlite3.connect(WORKING_DATABASE) as conn:
        cursor = conn.cursor()

        # Fetch all the app functions available
        cursor.execute("SELECT function_id, function_name FROM App_Functions")
        app_functions = cursor.fetchall()
        app_function_choices = {func[1]: func[0] for func in app_functions}
        selected_function_names = st.multiselect("Select App Functions:", list(app_function_choices.keys()))

        # Fetch actual names for levels
        cursor.execute("SELECT level_id, level_name FROM Levels WHERE school_id = ?", (school_id,))
        levels = cursor.fetchall()
        level_choices = {level[1]: level[0] for level in levels}
        selected_level_name = st.selectbox("Select Level (Optional, leave blank for all levels):", [""] + list(level_choices.keys()))
        selected_level_id = level_choices.get(selected_level_name)

        # Fetch actual names for classes
        cursor.execute("SELECT class_id, class_name FROM Classes WHERE school_id = ? AND (level_id = ? OR ? IS NULL)", (school_id, selected_level_id, selected_level_id))
        classes = cursor.fetchall()
        class_choices = {cls[1]: cls[0] for cls in classes}
        selected_class_name = st.selectbox("Select Class (Optional, leave blank for all classes):", [""] + list(class_choices.keys()))
        selected_class_id = class_choices.get(selected_class_name)

        # Fetch actual names for profiles
        cursor.execute("""
            SELECT p.profile_id, p.profile_name 
            FROM Profile p 
            JOIN Profile_Link pl ON p.profile_id = pl.profile_id 
            WHERE pl.org_id IN (SELECT org_id FROM Users WHERE school_id = ?)
        """, (school_id,))
        profiles = cursor.fetchall()
        profile_choices = {profile[1]: profile[0] for profile in profiles}
        selected_profile_name = st.selectbox("Select Profile (Optional, leave blank for all profiles):", [""] + list(profile_choices.keys()))
        selected_profile_id = profile_choices.get(selected_profile_name)

        st.markdown("---")
        btn_process = st.button("Process Users Based on Filter")

        if btn_process:
            # Fetching user IDs based on filters
            query = """
                SELECT user_id 
                FROM Users 
                WHERE school_id = ? 
                AND (level_id = ? OR ? IS NULL) 
                AND (class_id = ? OR ? IS NULL) 
                AND (profile_id = ? OR ? IS NULL)
            """
            cursor.execute(query, (school_id, selected_level_id, selected_level_id, selected_class_id, selected_class_id, selected_profile_id, selected_profile_id))
            user_ids = [row[0] for row in cursor.fetchall()]

            for user_id in user_ids:
                for function_name in selected_function_names:
                    selected_function_id = app_function_choices[function_name]

                    # Check if the user-function link already exists
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM App_Functions_Link
                        WHERE user_id = ? AND app_function_id = ?
                    """, (user_id, selected_function_id))
                    already_linked = cursor.fetchone()[0] > 0

                    # If link exists, skip (or you can choose to update if needed)
                    if already_linked:
                        continue

                    # Link user to the selected app function
                    cursor.execute("INSERT INTO App_Functions_Link(app_function_id, user_id) VALUES (?, ?)", (selected_function_id, user_id))

            conn.commit()
            st.success(f"Users matching the filter have been linked to selected app functions successfully!")