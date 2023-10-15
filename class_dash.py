import sqlite3
import csv
import streamlit as st
import pandas as pd
import os
import configparser
import os
import ast
# Create or check for the 'database' directory in the current working directory
cwd = os.getcwd()
WORKING_DIRECTORY = os.path.join(cwd, "database")

if not os.path.exists(WORKING_DIRECTORY):
	os.makedirs(WORKING_DIRECTORY)

if st.secrets["sql_ext_path"] == "None":
	WORKING_DATABASE= os.path.join(WORKING_DIRECTORY , st.secrets["default_db"])
else:
	WORKING_DATABASE= st.secrets["sql_ext_path"]
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
TCH = config_handler.get_config_values('constants', 'TCH')
STU = config_handler.get_config_values('constants', 'STU')
SA = config_handler.get_config_values('constants', 'SA')
AD = config_handler.get_config_values('constants', 'AD')

def display_data(data, columns):
    df = pd.DataFrame(data, columns=columns)
    st.dataframe(df)

def fetch_all_data():
    # Connect to the specified database
    conn = sqlite3.connect(WORKING_DATABASE)
    cursor = conn.cursor()

    # Fetch all data from data_table
    cursor.execute("SELECT * FROM Data_Table")
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    
    conn.close()
    return rows, column_names

def fetch_data_by_username(user_id):
    # Connect to the specified database
    conn = sqlite3.connect(WORKING_DATABASE)
    cursor = conn.cursor()

    # Fetch data from data_table based on the given username
    cursor.execute("SELECT * FROM Data_Table WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    
    conn.close()
    return rows, column_names

def diagnose_issue(sch_id):
    with sqlite3.connect(WORKING_DATABASE) as conn:
        cursor = conn.cursor()

        # Check for users of the given school
        cursor.execute("SELECT user_id FROM Users WHERE school_id=?", (sch_id,))
        user_ids = [row[0] for row in cursor.fetchall()]

        if not user_ids:
            return f"No users found for school_id {sch_id}"

        # Check data for these users
        cursor.execute('''
            SELECT Data_Table.data_id 
            FROM Data_Table
            WHERE Data_Table.user_id IN ({})
        '''.format(','.join('?' for _ in user_ids)), user_ids)

        data_ids = [row[0] for row in cursor.fetchall()]

        if not data_ids:
            return f"No data entries found for users {user_ids}"
        
        return f"Data entries found for the users: {data_ids}"

def fetch_data_by_school(sch_id):
    # Connect to the specified database
    conn = sqlite3.connect(WORKING_DATABASE)
    cursor = conn.cursor()
    # Fetch data from Data_Table for all users of the given school using JOIN
    cursor.execute('''
            SELECT Data_Table.* 
            FROM Data_Table
            JOIN Users ON Data_Table.user_id = Users.user_id
            WHERE Users.school_id=?
        ''', (sch_id,))
    
    data_rows = cursor.fetchall()
    data_column_names = [description[0] for description in cursor.description]
    conn.close()
    
    return data_rows, data_column_names

def fetch_data_by_sa(sch_id):
    # Connect to the specified database
    conn = sqlite3.connect(WORKING_DATABASE)
    cursor = conn.cursor()
    # Fetch data from Data_Table for all users of the given school using JOIN
    cursor.execute('''
            SELECT Data_Table.* 
            FROM Data_Table
            JOIN Users ON Data_Table.user_id = Users.user_id
            WHERE Users.school_id=? OR Users.school_id IS NULL
        ''', (sch_id,))
    
    data_rows = cursor.fetchall()
    data_column_names = [description[0] for description in cursor.description]
    conn.close()
    
    return data_rows, data_column_names

def fetch_data_by_school(sch_id):
    # Connect to the specified database
    conn = sqlite3.connect(WORKING_DATABASE)
    cursor = conn.cursor()
    # Fetch data from Data_Table for all users of the given school using JOIN
    cursor.execute('''
            SELECT Data_Table.* 
            FROM Data_Table
            JOIN Users ON Data_Table.user_id = Users.user_id
            WHERE Users.school_id=?
        ''', (sch_id,))
    
    data_rows = cursor.fetchall()
    data_column_names = [description[0] for description in cursor.description]
    conn.close()
    
    return data_rows, data_column_names


def download_data_table_csv(user_id, sch_id, profile):
    if profile == SA:#super admin
        data, columns = fetch_data_by_sa(sch_id)
        
    elif profile == AD:#administrator or super admin
        data, columns = fetch_data_by_school(sch_id)
    else: 
        data, columns = fetch_data_by_username(user_id)
        
    st.write("Conversation data")
    display_data(data, columns)
    # Write the data to a CSV file
    filename = 'data_table_records.csv'
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        for row in data:
            writer.writerow(dict(zip(columns, row)))

    # Check if the file was written successfully
    try:
        with open(filename, "r") as file:
            data_csv = file.read()
    except:
        st.error("Failed to export records, please try again")
    else:
        st.success("File is ready for downloading")
        st.download_button(
            label="Download data table as CSV",
            data=data_csv,
            file_name=filename,
            mime='text/csv',
        )

# In your Streamlit app:
# display_data()
# download_data_table_csv()
