import streamlit as st
import sqlite3
import streamlit_antd_components as sac
import openai
import os
import base64
import tempfile
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import LanceDB
import lancedb
import pickle

if "api_key" not in st.session_state:
	st.session_state.api_key = False

if st.session_state.api_key:
	os.environ["OPENAI_API_KEY"] = st.session_state.api_key
	openai.api_key = st.session_state.api_key
	embeddings = OpenAIEmbeddings()

# Create or check for the 'database' directory in the current working directory
cwd = os.getcwd()
database_path = os.path.join(cwd, "database")

if not os.path.exists(database_path):
    os.makedirs(database_path)

# Set DB_NAME to be within the 'database' directory
DB_NAME = os.path.join(database_path, st.secrets["default_db"])

def get_file_extension(file_name):
	return os.path.splitext(file_name)[1]

def fetch_file_data(file_name):
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	cursor.execute('SELECT data, metadata FROM files WHERE name=?;', (file_name,))
	data, metadata = cursor.fetchone()
	conn.close()
	return data, metadata


def save_file_to_db(username, name, data, metadata):
	# Get the extension and add it as a suffix to the filename
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	extension = get_file_extension(name)
	with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
		temp_file.write(data)
		temp_file.flush()
	# Save the original name, the path to the temporary file, and the metadata in the database
	cursor.execute('INSERT INTO files (username, name, data, metadata) VALUES (?, ?, ?, ?);', (username, name, temp_file.name, metadata))
	conn.commit()
	conn.close()

def fetch_all_files():
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	cursor.execute('SELECT name FROM files;')
	files = cursor.fetchall()
	conn.commit()
	conn.close()
	return files

def delete_files_from_db(file_names, username):
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()

	if username == 'administrator':
		# Delete files irrespective of the username associated with them
		for file_name in file_names:
			cursor.execute('DELETE FROM files WHERE name=?;', (file_name,))
	else:
		for file_name in file_names:
			cursor.execute('DELETE FROM files WHERE name=? AND username=?;', (file_name, username))
			
			# Check if the row was affected
			if cursor.rowcount == 0:
				st.error("Unable to delete files that are not owned by you")
				conn.close()  # Close the connection and exit the function
				return

	conn.commit()
	conn.close()

# def delete_files_from_db(file_names):
# 	conn = sqlite3.connect(DB_NAME)
# 	cursor = conn.cursor()
# 	for file_name in file_names:
# 		cursor.execute('DELETE FROM files WHERE name=?;', (file_name,))
# 	conn.commit()
# 	conn.close()

def docs_uploader():
	st.subheader("Upload Files to build your knowledge base")
	# Upload the file using Streamlit
	uploaded_file = st.file_uploader("Choose a file", type=['docx','txt','pdf'])
	meta = st.text_input("Please enter your document source: (Default is MOE)", max_chars=15)

	if uploaded_file:
		st.write("File:", uploaded_file.name, "uploaded!")
		if meta == "":
			meta = "MOE"
		# Read file content
		file_content = uploaded_file.read()
		
		# If you want to save the file, call the function
		if st.button("Save to Database"):
			save_file_to_db(st.session_state.user["username"],uploaded_file.name, file_content, meta)
			st.success("File saved to database!")

	# Remember to close the database connection when shutting down your app
	# Display list of files in the database
	st.subheader("Delete Files in Database:")
	files = fetch_all_files()
	if files:
		file_names = [file[0] for file in files]
		selected_files_to_delete = sac.transfer(items=file_names, label=None, index=None, titles=['Exisitng Files in db', 'Select Delete Files'], format_func='title', width='100%', height=None, search=True, pagination=False, oneway=False, reload=True, disabled=False, return_index=False)
		
		st.warning("Remove files from Database")
		#put form here to remove  files from database
		build = sac.buttons([
				dict(label='Delete Selected Files', icon='check-circle-fill', color = 'red'),
				dict(label='Cancel', icon='x-circle-fill', color='green'),
			], label=None, index=1, format_func='title', align='center', position='top', size='default', direction='horizontal', shape='round', type='default', compact=False, return_index=False)
		if build == 'Delete Selected Files':
			delete_files_from_db(selected_files_to_delete, st.session_state.user["username"])
			st.success(f"Deleted {len(selected_files_to_delete)} files.")

	else:
		st.write("No files found in the database.")



def create_lancedb_table(meta, table_name):
	lancedb_path = os.path.join(database_path, "lancedb")
	# LanceDB connection
	db = lancedb.connect(lancedb_path)
	table = db.create_table(
		f"{table_name}",
		data=[
			{
				"vector": embeddings.embed_query("Query Unsuccessful"),
				"text": "Query Unsuccessful",
				"id": "1",
				"source": f"{meta}"
			}
		],
		mode="overwrite",	
	)
	return table

def delete_lancedb_table(table_name):
	lancedb_path = os.path.join(database_path, "lancedb")
	# LanceDB connection
	db = lancedb.connect(lancedb_path)
	db.drop_table(f"{table_name}")

def check_underscore(s):
    return '_' not in s

def reset_vecstores():
	st.session_state.msg = []
	st.session_state.vs = False
	st.session_state.current_model = "No VectorStore loaded"
	if "memory" not in st.session_state:
		pass
	else:
		del st.session_state["memory"]


def create_vectorstores():
	#subjects = ["General", "English", "Math", "Science", "Mother Tongue"]
	full_docs = []
	st.subheader("Select the files to build your knowledge base")
	subject = st.text_input("Please type in a name for your subject bot (Do not use underscore _)", "General Subject")
	if subject and check_underscore(subject):
		#show the current build of files for the latest database
		files = fetch_all_files()
		if files:
			file_names = [file[0] for file in files]
			selected_files = sac.transfer(items=file_names, label=None, index=None, titles=['Uploaded files', 'Select files for KB'], format_func='title', width='100%', height=None, search=True, pagination=False, oneway=False, reload=True, disabled=False, return_index=False)
			#st.write(selected_files)
			#store selected files in mongodb so that students who log in can access this function and create their VectorStore
			st.warning("Click on Confirmed to build your knowledge base or click Cancel to delete existing VectorStores")
			#put form here to remove  files from database
			build = sac.buttons([
				dict(label='Confirmed', icon='check-circle-fill', color = 'green'),
				dict(label='Cancel', icon='x-circle-fill', color='red'),
			], label=None, index=1, format_func='title', align='center', position='top', size='default', direction='horizontal', shape='round', type='default', compact=False, return_index=False)
			if build == 'Confirmed' and selected_files:
				reset_vecstores() #reset conversation
				for s_file in selected_files:
					file_data, meta = fetch_file_data(s_file)
					docs = split_docs(file_data, meta)
					full_docs.extend(docs)
				if entry_exists(subject, st.session_state.user["username"]):
					st.error("A Knowledge Base with the same name exists, please choose a different name")
					return
				st.session_state.current_model = subject + "_" + st.session_state.user["username"]
				db = LanceDB.from_documents(full_docs, OpenAIEmbeddings(), connection=create_lancedb_table(meta, st.session_state.current_model)) #generating of vectorstore 
				st.session_state.vs = db #loading of vectorstore
				save_db_instance(subject, st.session_state.user["username"])
				#st.session_state.current_model = subject + "_" + st.session_state.user["username"]
				# Save this as the user's default bot
				save_default_vectorstore_for_user(st.session_state.user["username"], st.session_state.current_model)
				st.success("Knowledge Base loaded")
			else:
				dbs_deleter()
		else:
			st.write("No files found in the database.")
	else:
		st.write("Input a subject or remove the _ if any")

def split_docs(file_path,meta):
#def split_meta_docs(file, source, tch_code):
	loader = UnstructuredFileLoader(file_path)
	documents = loader.load()
	text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
	docs = text_splitter.split_documents(documents)
	metadata = {"source": meta}
	for doc in docs:
		doc.metadata.update(metadata)
	return docs

#check if vectorstore with same name and classname exist
def entry_exists(subject, username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM vector_dbs WHERE class_name = ? AND username = ?
    ''', (subject, username))

    # Check if a result is found
    if cursor.fetchone():
        conn.close()
        return True
    else:
        conn.close()
        return False

#if vectorstore with same name and classname exist then exit
def save_db_instance(subject, username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check if the entry already exists using the new function
    if entry_exists(subject, username):
        st.error("Error: An entry with the same class_name and username already exists.")
        return

    if 'vs' in st.session_state:
        serialized_db = pickle.dumps(st.session_state.vs)
        
        # Insert the new row
        cursor.execute('''
            INSERT INTO vector_dbs (class_name, data, username)
            VALUES (?, ?, ?)
        ''', (subject, serialized_db, username))
        conn.commit()

    conn.close()

def fetch_vector_instance_keys():
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	cursor.execute('SELECT class_name, username FROM vector_dbs')
	keys = cursor.fetchall()
	conn.close()
	return [f"{key[0]}_{key[1]}" for key in keys]

# def delete_vector_instances_from_db(selected_keys):
# 	conn = sqlite3.connect(DB_NAME)
# 	cursor = conn.cursor()
# 	for key in selected_keys:
# 		class_name, username = key.split('_')
# 		cursor.execute('DELETE FROM vector_dbs WHERE class_name=? AND username=?;', (class_name, username))
# 	conn.commit()
# 	conn.close()

def delete_vector_instances_from_db(selected_keys, current_username):
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	
	for key in selected_keys:
		class_name, username = key.split('_')
		
		# Check if the current user is an administrator
		if current_username == 'administrator':
			cursor.execute('DELETE FROM vector_dbs WHERE class_name=?;', (class_name,))
			delete_lancedb_table(key)
			if key == st.session_state.current_model:
				reset_vecstores()
		else:
			cursor.execute('DELETE FROM vector_dbs WHERE class_name=? AND username=?;', (class_name, current_username))
			
			# Check if the row was affected
			if cursor.rowcount == 0:
				st.error("Unable to delete vector instances that are not owned by you")
				conn.close()  # Close the connection and exit the function
				return
			else:
				delete_lancedb_table(key)
				if key == st.session_state.current_model:
					reset_vecstores()

	conn.commit()
	conn.close()


def dbs_deleter():
	st.subheader("Delete Vector Instances in Database:")
	vector_instance_keys = fetch_vector_instance_keys()
	if vector_instance_keys:
		selected_keys_to_delete = sac.transfer(items=vector_instance_keys, label=None, index=None, titles=['Existing Vector Instances in db', 'Select Vector Instances to Delete'], format_func='title', width='100%', height=None, search=True, pagination=False, oneway=False, reload=True, disabled=False, return_index=False)
		
		st.warning("Remove Vector Instances from Database")
		#put form here to remove vector instances from database
		build = sac.buttons([
			dict(label='Delete Selected Vector Instances', icon='check-circle-fill', color = 'red'),
			dict(label='Cancel', icon='x-circle-fill', color='green'),
		], label=None, index=1, format_func='title', align='center', position='top', size='default', direction='horizontal', shape='round', type='default', compact=False, return_index=False)
		if build == 'Delete Selected Vector Instances':
			delete_vector_instances_from_db(selected_keys_to_delete, st.session_state.user["username"])
			st.success(f"Deleted {len(selected_keys_to_delete)} vector instances.")
	else:
		st.write("No vector instances found in the database.")
		reset_vecstores()

def fetch_vector_instance_data(class_name, username):
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	cursor.execute('SELECT data FROM vector_dbs WHERE class_name=? AND username=?', (class_name, username))
	#print(class_name, username)
	data = cursor.fetchone()
	conn.close()
	if data:
		return pickle.loads(data[0])
	else:
		return None

def get_index(value, values_list):
	try:
		return values_list.index(value)
	except ValueError:
		return False
	
#selecting of vectorstore knowledge base 
def select_vectorstores():
	vector_instance_keys = fetch_vector_instance_keys()
	# Add an option to remove the vector store.
	vector_instance_keys.insert(0, "Remove VectorStore")

	if vector_instance_keys:
		# Check if a vectorstore is already loaded.
		if hasattr(st.session_state, 'current_model') and st.session_state.current_model:
			idx = get_index(st.session_state.current_model, vector_instance_keys)
		else:
			idx = 0
			st.write("No VectorStore Loaded")

		selected_key = st.selectbox('Choose a vectorstore:', vector_instance_keys, index=idx)

		if st.button('Load/Remove vectorstore'):
			#reset_vecstores() #reset conversations
			# If the user selects "Remove VectorStore"
			if selected_key == "Remove VectorStore":
				st.warning("VectorStore has been removed!")
				st.session_state.vs = False
				st.session_state.current_model = "No VectorStore loaded"
				# Set default VectorStore to "No VectorStore loaded"
				save_default_vectorstore_for_user(st.session_state.user["username"], "")
				
				return
			else:
				class_name, username = selected_key.split('_')
				vectorstore_instance = fetch_vector_instance_data(class_name, username)
				if vectorstore_instance:
					st.session_state.vs = vectorstore_instance
					st.success("Vectorstore loaded successfully!")
					st.session_state.current_model = selected_key
					# Save this as the user's default bot
					save_default_vectorstore_for_user(st.session_state.user["username"], selected_key)
					return
				else:
					st.error("Failed to load the selected vectorstore.")
	else:
		st.warning("No vectorstores available.")




#save the default vectore for users 
def save_default_vectorstore_for_user(username, vectorstore_class_name):
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()

	cursor.execute('UPDATE user_accounts SET default_bot=? WHERE username=?', (vectorstore_class_name, username))
	
	conn.commit()
	conn.close()



def load_default_vectorstore_for_user(username):
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()

	cursor.execute('SELECT default_bot FROM user_accounts WHERE username=?', (username,))
	vectorstore_class_name = cursor.fetchone()

	conn.close()

	# Check if a result was found
	if vectorstore_class_name and vectorstore_class_name[0]:
		# Since the stored vectorstore_class_name is a combination of subject and username (like "Math_johndoe"), 
		# you'll need to split it to fetch the vectorstore data
		class_name, dbs_user = vectorstore_class_name[0].split('_')
		vectorstore_instance = fetch_vector_instance_data(class_name, dbs_user)

		if vectorstore_instance:
			return vectorstore_instance, vectorstore_class_name[0]
	return None, None
