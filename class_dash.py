import sqlite3
import csv
import streamlit as st
import pandas as pd
import os

# Create or check for the 'database' directory in the current working directory
cwd = os.getcwd()
database_path = os.path.join(cwd, "database")

if not os.path.exists(database_path):
    os.makedirs(database_path)

# Set DB_NAME to be within the 'database' directory
DB_NAME = os.path.join(database_path, st.secrets["default_db"])

def display_data(data, columns):
    df = pd.DataFrame(data, columns=columns)
    st.dataframe(df)


def fetch_all_data():
    # Connect to the specified database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch all data from data_table
    cursor.execute("SELECT * FROM data_table")
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    
    conn.close()
    return rows, column_names

def fetch_vectors_by_username(username):
    # Connect to the specified database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch data from data_table based on the given username
    cursor.execute("SELECT * FROM vector_dbs WHERE username=?", (username,))
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    
    conn.close()
    return rows, column_names

def fetch_all_vectors():
    # Connect to the specified database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch data from data_table based on the given username
    cursor.execute("SELECT * FROM vector_dbs")
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    
    conn.close()
    return rows, column_names

def fetch_data_by_username(username):
    # Connect to the specified database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch data from data_table based on the given username
    cursor.execute("SELECT * FROM data_table WHERE username=?", (username,))
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    
    conn.close()
    return rows, column_names

def fetch_data_by_username_and_profile(username, profile):
    # Connect to the specified database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch data from data_table based on the given username and profile
    cursor.execute("SELECT * FROM data_table WHERE username=? AND profile=?", (username, profile))
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    
    conn.close()
    return rows, column_names

def download_data_table_csv(username, profile, db_name=DB_NAME):
    d = False
    c = False
    if profile == "student":
        data, columns = fetch_data_by_username(username)
    elif profile == "teacher":
        data, columns = fetch_data_by_username_and_profile(username, profile)
    else: #administrator
        data, columns = fetch_all_data()
        d,c =fetch_all_vectors()
    if d and c: 
        st.write("Knowledge Base Databases")
        display_data(d,c)
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
