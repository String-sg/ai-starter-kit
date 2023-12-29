import sqlite3
import streamlit as st
import os
#clear no error in creating schema

# Create or check for the 'database' directory in the current working directory
cwd = os.getcwd()
WORKING_DIRECTORY = os.path.join(cwd, "database")

if not os.path.exists(WORKING_DIRECTORY):
	os.makedirs(WORKING_DIRECTORY)

if st.secrets["sql_ext_path"] == "None":
	WORKING_DATABASE= os.path.join(WORKING_DIRECTORY , st.secrets["default_db"])
else:
	WORKING_DATABASE= st.secrets["sql_ext_path"]


def create_dbs():
    conn = sqlite3.connect(WORKING_DATABASE)
    cursor = conn.cursor()

    # Profile table each organization has a list of profiles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Profile (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_name TEXT NOT NULL UNIQUE
                   
        )
    ''')

    # Link Ogansiation to Profile as some profiles are shared across organizations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Profile_Link (
            profile_id INTEGER,
            org_id INTEGER,
            PRIMARY KEY (profile_id, org_id),
            FOREIGN KEY(profile_id) REFERENCES Profile(profile_id),
            FOREIGN KEY(org_id) REFERENCES Organizations(org_id)
        )
    ''')

    # Organizations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Organizations (
            org_id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_name TEXT NOT NULL UNIQUE
        )
    ''')

    # Schools table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Schools (
            school_id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL,
            school_name TEXT NOT NULL UNIQUE,
            FOREIGN KEY(org_id) REFERENCES Organizations(org_id)
        )
    ''')

    # Levels table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Levels (
            level_id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            level_name TEXT NOT NULL,
            FOREIGN KEY(school_id) REFERENCES Schools(school_id),
            FOREIGN KEY(org_id) REFERENCES Organizations(org_id)
        )
    ''')

    # Classes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Classes (
            class_id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            level_id INTEGER NOT NULL,
            class_name TEXT NOT NULL,
            FOREIGN KEY(level_id) REFERENCES Levels(level_id),
            FOREIGN KEY(school_id) REFERENCES Schools(school_id),
            FOREIGN KEY(org_id) REFERENCES Organizations(org_id)
        )
    ''')
    #Users table for both schools and agencies
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        profile_id INTEGER NOT NULL,
        school_id INTEGER,
        class_id INTEGER,
        org_id INTEGER NOT NULL,
        branch_id INTEGER,
        division_id INTEGER,
        level_id INTEGER,
        FOREIGN KEY(profile_id) REFERENCES Profile(profile_id),
        FOREIGN KEY(school_id) REFERENCES Schools(school_id),
        FOREIGN KEY(class_id) REFERENCES Classes(class_id),
        FOREIGN KEY(org_id) REFERENCES Organizations(org_id)

        )
    ''')

    # TeacherAssignments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Teacher_Assignments (
            teacher_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            level_id INTEGER NOT NULL,
            class_id INTEGER NOT NULL,
            PRIMARY KEY(teacher_id, class_id),
            FOREIGN KEY(teacher_id) REFERENCES Users(user_id),
            FOREIGN KEY(class_id) REFERENCES Classes(class_id),
            FOREIGN KEY(school_id) REFERENCES Schools(school_id),
            FOREIGN KEY(level_id) REFERENCES Levels(level_id)
        )
    ''')
    #Data table for chatbot
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Data_Table (
            data_id INTEGER PRIMARY KEY,
            date TEXT,
            user_id INTEGER NOT NULL,
            profile_id INTEGER NOT NULL,
            chatbot_ans TEXT,
            user_prompt TEXT,
			function_name TEXT,
            tokens INTEGER,
			response_rating INTEGER,
            FOREIGN KEY(user_id) REFERENCES Users(user_id),
            FOREIGN KEY(profile_id) REFERENCES Profile(profile_id)
        )
    ''')
    
    # Files table (modified to include subject, topic, and level columns)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Files (
            file_id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,		
            data BLOB NOT NULL,
            metadata TEXT NOT NULL,
            subject INTEGER,
            topic INTEGER,
            sharing_enabled BOOLEAN NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES Users(user_id),
            FOREIGN KEY(subject) REFERENCES Subject(id),
            FOREIGN KEY(topic) REFERENCES Topic(id)

        )
    ''')
    #Create Subject table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS Subject (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        org_id INTEGER NOT NULL,
                        subject_name TEXT NOT NULL UNIQUE,
                        FOREIGN KEY(org_id) REFERENCES Organizations(org_id)
                        )
                     ''')
    #Create Topic table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS Topic (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          org_id INTEGER NOT NULL,
                          topic_name TEXT NOT NULL UNIQUE,
                          FOREIGN KEY(org_id) REFERENCES Organizations(org_id)
                        )
                     ''')

    # Modified Vector stores table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Vector_Stores (
            vs_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vectorstore_name TEXT NOT NULL, 
            documents TEXT NOT NULL,
            subject INTEGER,
            topic INTEGER,
            sharing_enabled BOOLEAN NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES Users(user_id),
            FOREIGN KEY(subject) REFERENCES Subject(id),
            FOREIGN KEY(topic) REFERENCES Topic(id)

        )
    ''')

   
    # Prompt templates table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Prompt_Templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt_template TEXT NOT NULL,
        prompt_description TEXT NOT NULL,
        user_id INTEGER,
        app_function_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES Users(user_id),
        FOREIGN KEY(app_function_id) REFERENCES App_Functions(function_id)
        )
    ''')

    # App Functions table link to users table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS App_Functions_Link (
                       app_function_id INTEGER,
                       user_id INTEGER,
                       PRIMARY KEY (app_function_id, user_id),
                       FOREIGN KEY(app_function_id) REFERENCES App_Functions(function_id),
                       FOREIGN KEY(user_id) REFERENCES Users(user_id)
                   )
                ''')

    # App Functions table
    cursor.execute('''
       CREATE TABLE IF NOT EXISTS App_Functions (
            function_id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_name TEXT NOT NULL UNIQUE,
            function_description TEXT NOT NULL
        )
    ''')

    #Load vectorstores for users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS User_VectorStores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        vs_id INTEGER NOT NULL,
        FOREIGN KEY(user_id) REFERENCES Users(user_id),
        FOREIGN KEY(vs_id) REFERENCES Vector_Stores(vs_id)
        )
    ''')

    #Store Bot Settings for users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS BotSettings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            temp REAL,
            presence_penalty REAL,
            frequency_penalty REAL,
			chat_memory INTEGER,
            FOREIGN KEY(user_id) REFERENCES Users(user_id)
        )
        ''')
 #Link vectorestores to profiles
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Profile_VectorStores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER NOT NULL,
        vs_id INTEGER NOT NULL,
        FOREIGN KEY(profile_id) REFERENCES Profile(profile_id),
        FOREIGN KEY(vs_id) REFERENCES Vector_Stores(vs_id)
        )
    ''')
	
    #need to create vectorstores for each app function - new table


    conn.commit()
    conn.close()

