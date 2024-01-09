import sqlite3
import streamlit as st
import configparser
import os
import ast
from basecode.kb_module import load_vectorstore

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

def set_function_access_for_user(user_id):
    """
    Check the App_Functions_Link table to set the app functions accessible to the user.

    :param user_id: ID of the user who has logged in.
    """
    
    with sqlite3.connect(WORKING_DATABASE) as conn:
        cursor = conn.cursor()
        
        # Fetch app functions linked to the user
        query = """
            SELECT af.function_name 
            FROM App_Functions af 
            JOIN App_Functions_Link afl ON af.function_id = afl.app_function_id 
            WHERE afl.user_id = ?
        """
        cursor.execute(query, (user_id,))
        user_functions = [row[0] for row in cursor.fetchall()]

    # Check which functions the user has access to and update the session state
    for function in user_functions:
        if function in st.session_state.func_options:
            st.session_state.func_options[function] = False
            


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
        profile_choices = {profile[1]: profile[0] for profile in profiles if profile[0] != 1}
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
                # Remove all existing associations for this user_id
                cursor.execute("""
                    DELETE FROM App_Functions_Link
                    WHERE user_id = ?
                """, (user_id,))

                # Now, link the user to the selected app functions
                for function_name in selected_function_names:
                    selected_function_id = app_function_choices[function_name]
                    #st.write("Function ID:", selected_function_id)

                    # Link user to the selected app function
                    cursor.execute("""
                        INSERT INTO App_Functions_Link(app_function_id, user_id) 
                        VALUES (?, ?)
                    """, (selected_function_id, user_id))

            conn.commit()
            st.success(f"Users matching the filter have been linked to selected app functions successfully!")

def save_prompt_templates_for_user(user_id):
    with sqlite3.connect(WORKING_DATABASE) as conn:
        cursor = conn.cursor()

        for function_name in PROMPT_TEMPLATES_FUNCTIONS:
            cursor.execute('''
                SELECT id FROM Prompt_Templates WHERE prompt_template = ? AND user_id = ?
            ''', (function_name, user_id))
            if not cursor.fetchone():  # If not exists
                cursor.execute('''
                    INSERT INTO Prompt_Templates (prompt_template, prompt_description, user_id)
                    VALUES (?, ?, ?)
                ''', (function_name, DEFAULT_TEXT, user_id))

        conn.commit()


def create_prompt_template(user_id):
    st.subheader("Personalised Prompt Design Templates")
    st.warning("Changing the prompt templates will affect the results of your chatbot and other generative functions")
    # Ensure that the prompt templates for the functions are added
    save_prompt_templates_for_user(user_id)

    with sqlite3.connect(WORKING_DATABASE) as conn:
        cursor = conn.cursor()

        # Fetch username for the given user_id
        cursor.execute('''
            SELECT username FROM Users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        if result:
            username = result[0]
            st.write("Username:", username)
        else:
            st.write("Error: User not found!")
            return

        # Fetch all templates for the given user
        cursor.execute('''
            SELECT id, prompt_template, prompt_description FROM Prompt_Templates WHERE user_id = ?
        ''', (user_id,))
        templates = cursor.fetchall()
        template_names = [template[1] for template in templates]
        
        
        # Replace text_input with selectbox for prompt_name
        selected_template_name = st.selectbox("Select a template name", template_names)

        # Update current_template_description based on the selected prompt name
        current_template_description = next((template[2] for template in templates if template[1] == selected_template_name), '')

        new_prompt_description = st.text_area("Update Prompt Description", current_template_description, height=500)

        if st.button("Update Description"):
            if selected_template_name and new_prompt_description:
                # Update description if user_id and template name exists
                cursor.execute('''
                    UPDATE Prompt_Templates
                    SET prompt_description = ?
                    WHERE user_id = ? AND prompt_template = ?
                ''', (new_prompt_description, user_id, selected_template_name))

                conn.commit()

                 # Update st.session_state
                session_key = selected_template_name.replace(" ", "_").lower()
                st.session_state[session_key] = new_prompt_description
                
                # Inform the user of successful update
                st.write("Successfully updated the description.")
            else:
                st.write("Ensure that the description field is not blank!")
        return templates


def update_prompt_template(profile_id, templates):
    """
    Display the UI to update prompt templates in Streamlit based on filter.

    :param profile_id: Profile ID of the logged-in user.
    :param school_id_of_AD: If the profile_id is AD, this specifies the school ID of the AD.
    """
    st.subheader("Set Prompt Design Templates to users")
    st.warning("Update the prompt templates for all users in the organisation")

    with sqlite3.connect(WORKING_DATABASE) as conn:
        cursor = conn.cursor()

        selected_school_id = None
        if profile_id == SA:
            # Fetch all schools
            cursor.execute("SELECT school_id, school_name FROM Schools")
            schools = cursor.fetchall()
            # Check if there are no schools and exit if true
            if not schools:
                st.error("No schools available")
                return
            school_choices = {school[1]: school[0] for school in schools}
            selected_school_name = st.selectbox("Select School:", list(school_choices.keys()))
            selected_school_id = school_choices[selected_school_name]
        elif profile_id == AD:
            selected_school_id = st.session_state.user['school_id']

        # Fetch profiles except SA and AD
        cursor.execute("SELECT profile_id, profile_name FROM Profile WHERE profile_id NOT IN (?, ?)", (SA, AD))
        profiles = cursor.fetchall()
        profile_choices = {profile[1]: profile[0] for profile in profiles}
        #profile_choices["All Users"] = None  # Add "All Users" option
        #selected_profile_name = st.selectbox("Select Profile (Excludes SA & AD):", list(profile_choices.keys()))
        multiselect_profile_names = st.multiselect("Select Profiles (Excludes SA & AD):", list(profile_choices.keys()))
        #selected_profile_id = multiselect_profile_names
        # st.write("school id:", selected_school_id)
        # st.write("profile id:", multiselect_profile_names)
        # st.write("Profile choices:", profile_choices)
        btn_process = st.button("Update Templates for profile")
        st.divider()
        if btn_process:
            # Fetching user IDs based on filters
            for profile_name in multiselect_profile_names:
                if profile_name in profile_choices:
                    profile_id = profile_choices[profile_name]
                    query = """
                        SELECT user_id 
                        FROM Users 
                        WHERE (school_id = ?) 
                        AND (profile_id = ?)
                    """
                    cursor.execute(query, (selected_school_id, profile_id))
                    user_ids = [row[0] for row in cursor.fetchall()]
                    # st.write("User IDs:", user_ids)
                    for user_id in user_ids:
                        # Check if the user has an existing prompt template
                        for template_data in templates:
                            template_name = template_data[1]
                            template_description = template_data[2]
                            # Check if this template name exists for the current user
                            cursor.execute('''
                                SELECT COUNT(1) 
                                FROM Prompt_Templates 
                                WHERE user_id = ? AND prompt_template = ?
                            ''', (user_id, template_name))
                            exists = cursor.fetchone()[0]

                            if exists:
                                # Update the existing row with the current description
                                cursor.execute('''
                                    UPDATE Prompt_Templates 
                                    SET prompt_description = ? 
                                    WHERE user_id = ? AND prompt_template = ?
                                ''', (template_description, user_id, template_name))
                            else:
                                # Insert a new row if it doesn't exist for this user
                                cursor.execute('''
                                    INSERT INTO Prompt_Templates (user_id, prompt_description, prompt_template) 
                                    VALUES (?, ?, ?)
                                ''', (user_id, template_description, template_name))
                        conn.commit()
                    st.success(f"Prompt templates for users matching the filter have been updated successfully!")
            
#not in use part of the preload 
def load_prompt_templates(user_id):
    """
    Load prompt templates for the user.
    """
    with sqlite3.connect(WORKING_DATABASE) as conn:
        cursor = conn.cursor()

        # Fetching existing templates and their descriptions for the user
        cursor.execute('''
            SELECT prompt_template, prompt_description FROM Prompt_Templates WHERE user_id = ?
        ''', (user_id,))
        existing_templates = {row[0]: row[1] for row in cursor.fetchall()}

        # Setting session state for templates
        for function_name in PROMPT_TEMPLATES_FUNCTIONS:
            session_key = function_name.replace(" ", "_").lower()
            if session_key not in st.session_state:
                st.session_state[session_key] = existing_templates.get(function_name, DEFAULT_TEXT)

        conn.commit()

#loading of variables is completed and done
def pre_load_variables(user_id):
    with sqlite3.connect(WORKING_DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT prompt_template, prompt_description FROM Prompt_Templates WHERE user_id = ?
        ''', (user_id,))
        existing_templates = {row[0]: row[1] for row in cursor.fetchall()}

        # Setting session state for templates
        for function_name in PROMPT_TEMPLATES_FUNCTIONS:
            session_key = function_name.replace(" ", "_").lower()
            if session_key not in st.session_state:
                st.session_state[session_key] = existing_templates.get(function_name, DEFAULT_TEXT)

        conn.commit()

        # Fetch user_id and profile_id using user_id
        cursor.execute('''
            SELECT u.user_id, u.username, p.profile_id, p.profile_name 
            FROM Users u
            INNER JOIN Profile p ON u.profile_id = p.profile_id 
            WHERE u.user_id = ?
        ''', (user_id,))
        user_data = cursor.fetchone()

        if not user_data:
            raise ValueError(f"No user found with user ID: {user_id}")
        
        if "data_profile" not in st.session_state:
            # Assign values to Streamlit's session state
            st.session_state.data_profile = {
                "user_id": user_data[0],
                "username": user_data[1],
                "profile_id": user_data[2],
                "profile_name": user_data[3]
            }


#loading and selecting of vectorestore is completed and done

# def load_available_shared_owned_vector_stores(user_id):
#     """
#     Query the database for shared vector stores and those created by the user.
#     Return their names and associated IDs.
#     """
#     with sqlite3.connect(WORKING_DATABASE) as conn:
#         cursor = conn.cursor()
        
#         # Modified the SQL query to select both vectorstore_name and vs_id
#         cursor.execute('''
#             SELECT vs_id, vectorstore_name 
#             FROM Vector_Stores 
#             WHERE sharing_enabled = 1 OR user_id = ?
#         ''', (user_id,))
        
#         # Store the results as a list of dictionaries
#         vectorstores = [{"vs_id": row[0], "vectorstore_name": row[1]} for row in cursor.fetchall()]
#         st.write(vectorstores)
        
#     return vectorstores


def associate_vectorstore_with_user(user_id, vs_id):
    with sqlite3.connect(WORKING_DATABASE) as conn:
        cursor = conn.cursor()
        
        # Remove any previous association
        cursor.execute('''
            DELETE FROM User_VectorStores WHERE user_id = ?
        ''', (user_id,))
        
        # Add the new association
        cursor.execute('''
            INSERT INTO User_VectorStores (user_id, vs_id)
            VALUES (?, ?)
        ''', (user_id, vs_id))
        
        conn.commit()
        
        # Set the chosen vector store ID to the session state
        
        st.success(f"VectorStore ID {vs_id} associated with user ID {user_id}.")


# # Need change this
# def chat_bot_vectorstore_selection_interface(user_id, c1, c2):
#     """
#     Display Streamlit interface for vectorstore selection.
#     """
#     available_vectorstores = load_available_shared_owned_vector_stores(user_id)

#     if available_vectorstores:
#         #
#         with c1:
#             # Construct selectbox options
#             options = [vs['vectorstore_name'] for vs in available_vectorstores]
            
#             # Use the constructed options in Streamlit's selectbox
#             selected_vs_name = st.selectbox("Select Knowledge Base:", options, index=0, label_visibility="collapsed")
#         with c2:
#             if st.button("Save KB"):
#                 if selected_vs_name:
#                     # Retrieve the selected vs_id
#                     selected_vs_id = next((vs['vs_id'] for vs in available_vectorstores if vs['vectorstore_name'] == selected_vs_name), None)
                    
#                     if selected_vs_id:
#                         associate_vectorstore_with_user(user_id, selected_vs_id)
#                         load_and_use_vectorstore(selected_vs_id)
#                         st.success("Preference saved successfully!")
#                     else:
#                         st.error("Error in retrieving the selected VectorStore ID.")
#                 st.rerun()()     
#     else:
#         with c1:
#             st.write("No KB available.")

#loading and selecting of vectorestore is completed and done

# def load_available_vector_stores(user_id):
#     """
#     Query the database for shared vector stores and those created by the user.
#     Return their names and associated IDs.
#     """
#     with sqlite3.connect(WORKING_DATABASE) as conn:
#         cursor = conn.cursor()
        
#         # Modified the SQL query to select both vectorstore_name and vs_id
#         cursor.execute('''
#             SELECT vs_id, vectorstore_name 
#             FROM Vector_Stores 
#             WHERE sharing_enabled = 1 AND user_id = ?
#         ''', (user_id,))
        
#         # Store the results as a list of dictionaries
#         vectorstores = [{"vs_id": row[0], "vectorstore_name": row[1]} for row in cursor.fetchall()]
        
#     return vectorstores


def link_profiles_to_vectorstore_interface(user_id):
    """
    Display Streamlit interface for linking profiles to a specific vector store.
    """

    with sqlite3.connect(WORKING_DATABASE) as conn:
        cursor = conn.cursor()

        # Fetch available vector stores for the user
        available_vectorstores = load_available_shared_owned_vector_stores(user_id)
        
        # Fetch profiles
        profiles = fetch_all_profiles(cursor)
        profile_options = {name: id for id, name in profiles}

        st.subheader("Link Profiles to a Knowledge Base(KB):")
        
        if available_vectorstores:
            # Construct selectbox options for vector stores
            vs_options = [vs['vectorstore_name'] for vs in available_vectorstores]
            
            # Use the constructed options in Streamlit's selectbox
            selected_vs_name = st.selectbox("Select KB:", vs_options, index=0)
            selected_vs_id = next((vs['vs_id'] for vs in available_vectorstores if vs['vectorstore_name'] == selected_vs_name), None)
            
           # Display current associations
            cursor.execute('''
                SELECT p.profile_name 
                FROM Profile_VectorStores pvs
                JOIN Profile p ON pvs.profile_id = p.profile_id
                WHERE pvs.vs_id = ?
            ''', (selected_vs_id,))
            current_profiles_names = [row[0] for row in cursor.fetchall()]

            if not current_profiles_names:
                st.write(f"Knowledge Base: **:blue[{selected_vs_name}]** is only associated to its :green[current owner.]")
            else:
                st.write(f"Knowledge Base: **:blue[{selected_vs_name}]** is currently associated with profiles: **:green[{', '.join(current_profiles_names)}]**")
            #set options to all or remove profiles
            col1, col2, col3 = st.columns([1,2,4])
            with col1:
                set_all = st.button("Link KB to All Profiles")
                if set_all:
                    for profile_name in profile_options.keys():
                        profile_id = profile_options[profile_name]
                        add_access_to_vectorstore(cursor, profile_id, selected_vs_id)
                    conn.commit()
                    st.success(f"All profiles set to KB: {selected_vs_name}")
            with col2:
                remove_all = st.button("Remove KB links from All Profiles")
                if remove_all:
                    cursor.execute('DELETE FROM Profile_VectorStores WHERE vs_id = ?', (selected_vs_id,))
                    conn.commit()
                    st.success(f"All profile links removed from KB: {selected_vs_name}")

            # Multi-select for profiles
            selected_profiles = st.multiselect('Select profiles that can access the KB:', list(profile_options.keys()))

            
            if st.button("Link Selected Profiles to KB"):
                for profile_name in selected_profiles:
                    profile_id = profile_options[profile_name]
                    add_access_to_vectorstore(cursor, profile_id, selected_vs_id)
                conn.commit()
                st.success(f"Set Selected Profiles to KB: {selected_vs_name}")

        else:
            st.write("No KB available for the user.")

def fetch_all_profiles(cursor):
    cursor.execute("SELECT profile_id, profile_name FROM Profile")
    return cursor.fetchall()

def add_access_to_vectorstore(cursor, profile_id, vs_id):
    cursor.execute("INSERT INTO Profile_VectorStores (profile_id, vs_id) VALUES (?, ?)", (profile_id, vs_id))

def load_available_shared_owned_vector_stores(user_id):
    """
    Query the database for shared vector stores that are created by the user and accessible to associated profiles.
    Also, if the user has profile_id 'SA', return all vector stores. If profile_id is 'AD', return vector stores from the same organization.
    Return their names and associated IDs.
    """
    accessible_vectorstores = []

    with sqlite3.connect(WORKING_DATABASE) as conn:
        cursor = conn.cursor()
        
        # Get user's profile_id and org_id
        cursor.execute('''
            SELECT profile_id, org_id
            FROM Users
            WHERE user_id = ?
        ''', (user_id,))
        profile_data = cursor.fetchone()
        if not profile_data:
            return accessible_vectorstores

        profile_id, org_id = profile_data
        
        # If profile_id is SA, return all vector stores
        if profile_id == SA:
            cursor.execute('''
                SELECT vs_id, vectorstore_name 
                FROM Vector_Stores
            ''')
            return [{"vs_id": row[0], "vectorstore_name": row[1]} for row in cursor.fetchall()]

        # If profile_id is AD, return all vector stores from the same organization
        elif profile_id == AD:
            cursor.execute('''
                SELECT vs_id, vectorstore_name 
                FROM Vector_Stores
                WHERE user_id IN (SELECT user_id FROM Users WHERE org_id = ?)
            ''', (org_id,))
            return [{"vs_id": row[0], "vectorstore_name": row[1]} for row in cursor.fetchall()]
        
        # For other profiles
        else:
            # Vector stores owned by the user
            cursor.execute('''
                SELECT vs_id, vectorstore_name 
                FROM Vector_Stores 
                WHERE user_id = ?
            ''', (user_id,))
            accessible_vectorstores.extend([{"vs_id": row[0], "vectorstore_name": row[1]} for row in cursor.fetchall()])
            
            # Vector stores shareable and match the user's profile
            cursor.execute('''
                SELECT vs.vs_id, vs.vectorstore_name 
                FROM Vector_Stores vs
                INNER JOIN Profile_VectorStores pvs ON vs.vs_id = pvs.vs_id
                WHERE vs.sharing_enabled = 1 AND pvs.profile_id = ?
            ''', (profile_id,))
            accessible_vectorstores.extend([{"vs_id": row[0], "vectorstore_name": row[1]} for row in cursor.fetchall()])

    return accessible_vectorstores

def remove_duplicates_from_vector_stores(vectorstores):
    seen_vs_ids = set()
    unique_vectorstores = []
    for vs in vectorstores:
        if vs['vs_id'] not in seen_vs_ids:
            seen_vs_ids.add(vs['vs_id'])
            unique_vectorstores.append(vs)
    return unique_vectorstores

def vectorstore_selection_interface(user_id):
    """
    Display Streamlit interface for vectorstore selection.
    """
    vectorstores = load_available_shared_owned_vector_stores(user_id)
    #st.write(vectorstores)
    available_vectorstores = remove_duplicates_from_vector_stores(vectorstores)
    #st.write(available_vectorstores)

    st.subheader("Select knowledge base for the Bot:")
    st.write(f"Current loaded Knowledge Base: **:blue[{st.session_state.current_model}]**")

    if available_vectorstores:
        # Construct selectbox options
        options = ["Unload KB"] + [vs['vectorstore_name'] for vs in available_vectorstores]
        
        # Use the constructed options in Streamlit's selectbox
        selected_vs_name = st.selectbox("Select Knowledge Base:", options, index=0)
        
        if st.button("Load/Unload KB"):
            if selected_vs_name != "Unload KB":
                # Retrieve the selected vs_id
                selected_vs_id = next((vs['vs_id'] for vs in available_vectorstores if vs['vectorstore_name'] == selected_vs_name), None)
                
                if selected_vs_id:
                    # Load the vectorstore data or process it as needed here
                    associate_vectorstore_with_user(user_id, selected_vs_id)
                    # For instance, you might want a function that does something with the selected vectorstore
                    load_and_use_vectorstore(selected_vs_id)
                    
                    st.success("Preference saved successfully!")
                else:
                    st.error("Error in retrieving the selected VectorStore ID.")
            else:
                st.warning("Knowledge Base unloaded.")
                st.session_state.vs = False
                st.session_state.current_model = "No KB loaded"
                
    else:
        st.write("No KB available.")

def load_and_use_vectorstore(vs_id):
    """
    Load the vector store data into the session state for the given vector store ID.
    """
    with sqlite3.connect(WORKING_DATABASE) as conn:
        cursor = conn.cursor()
        
        # Fetch the vectorstore_name and data for the provided vs_id
        cursor.execute('''
            SELECT vectorstore_name, documents
            FROM Vector_Stores 
            WHERE vs_id = ?
        ''', (vs_id,))
        
        vectorstore_data = cursor.fetchone()
        
        if not vectorstore_data:
            st.warning("Vectorstore not found for the given ID.")
            return

        vectorstore_name, documents = vectorstore_data

        if not documents:
            st.warning("Vectorstore documents not found.")
            return

        #convert the documents json to document objects
        

        # Set the data and the associated name to Streamlit's session state
        st.session_state.vs = load_vectorstore(documents, vectorstore_name)
        st.session_state.current_model = vectorstore_name


def load_and_fetch_vectorstore_for_user(user_id):
    """
    Load the associated vector store ID and data into the session state for the logged-in user.
    """
    try:
        with sqlite3.connect(WORKING_DATABASE) as conn:
            cursor = conn.cursor()
            
            # Fetch associated vs_id and vectorstore_name for the user
            cursor.execute('''
                SELECT uvs.vs_id, vs.vectorstore_name
                FROM User_VectorStores uvs
                INNER JOIN Vector_Stores vs ON uvs.vs_id = vs.vs_id
                WHERE uvs.user_id = ?
            ''', (user_id,))
            
            vectorstore_data = cursor.fetchone()
            
            if not vectorstore_data:
                st.warning("No vectorstore associated with the user.")
                return None

            vs_id, vectorstore_name = vectorstore_data

            # Fetch the actual vector data using the vs_id
            cursor.execute('''
                SELECT documents FROM Vector_Stores WHERE vs_id=?''', 
                (vs_id,)
            )

            documents = cursor.fetchone()

            if not documents:
                st.warning("Vectorstore data not found.")
                return None

            vs = load_vectorstore(documents[0], vectorstore_name)

            # Set data to Streamlit's session state
            st.session_state['vs'] = vs
            st.session_state['current_model'] = vectorstore_name

            return vs
    except sqlite3.DatabaseError as e:
        st.error(f"An error occurred while accessing the database: {e}")
        return None