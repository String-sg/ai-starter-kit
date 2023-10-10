#No need SQLite
import streamlit as st
import openai
from streamlit_antd_components import menu, MenuItem
import streamlit_antd_components as sac
from main_bot import basebot_memory, basebot_qa_memory, clear_session_states, search_bot, basebot_qa, basebot
from kb_module import display_files,docs_uploader, delete_files
from vs_module import display_vectorstores, create_vectorstore, delete_vectorstores
from authenticate import login_function,check_password
from class_dash import download_data_table_csv
from lesson_plan import lesson_collaborator, lesson_commentator, lesson_bot
#New schema move function fom settings
from database_schema import create_dbs
from database_module import manage_tables, delete_tables
from org_module import (
	has_at_least_two_rows,
	initialise_admin_account,
	load_user_profile,
	display_accounts,
	create_org_structure,
	check_multiple_schools,
	process_user_profile,
	remove_or_reassign_teacher_ui,
	reassign_student_ui,
	change_teacher_profile_ui
)
from pwd_module import reset_passwords, password_settings
from users_module import (
	link_users_to_app_function_ui,
	set_function_access_for_user,
	create_prompt_template,
	update_prompt_template,
	vectorstore_selection_interface,
	pre_load_variables,
	load_and_fetch_vectorstore_for_user,
	chat_bot_vectorstore_selection_interface,
	link_profiles_to_vectorstore_interface
	
)
from k_map import (
    map_prompter, 
    generate_mindmap,
    map_creation_form, 
    map_prompter_with_plantuml_form, 
    generate_plantuml_mindmap, 
    render_diagram
)
from audio import record_myself,assessment_prompt
from bot_settings import bot_settings_interface, load_bot_settings
from PIL import Image
import configparser
import ast

class ConfigHandler:
	def __init__(self):
		self.config = configparser.ConfigParser()
		self.config.read('config.ini')

	def get_value(self, section, key):
		value = self.config.get(section, key)
		try:
			# Convert string value to a Python data structure
			return ast.literal_eval(value)
		except (SyntaxError, ValueError):
			# If not a data structure, return the plain string
			return value

# Initialization
config_handler = ConfigHandler()

# Setting Streamlit configurations
st.set_page_config(layout="wide")

# Fetching secrets from Streamlit
DEFAULT_TITLE = st.secrets["default_title"]
SUPER_PWD = st.secrets["super_admin_password"]
SUPER = st.secrets["super_admin"]

# Fetching values from config.ini
DEFAULT_TEXT = config_handler.get_value('constants', 'DEFAULT_TEXT')
TCH = config_handler.get_value('constants', 'TCH')
STU = config_handler.get_value('constants', 'STU')
SA = config_handler.get_value('constants', 'SA')
AD = config_handler.get_value('constants', 'AD')

def is_function_disabled(function_name):
	return st.session_state.func_options.get(function_name, True)

def main():
	try:
		if "title_page"	not in st.session_state:
			st.session_state.title_page = DEFAULT_TITLE 

		st.title(st.session_state.title_page)
		sac.divider(label='A String Initiative', icon='house', align='center', direction='horizontal', dashed=False, bold=False)
		
		if "api_key" not in st.session_state:
			st.session_state.api_key = False
			if st.secrets["openai_key"] != "None":
				st.session_state.api_key  = st.secrets["openai_key"]

		if "option" not in st.session_state:
			st.session_state.option = False
		
		if "login" not in st.session_state:
			st.session_state.login = False
		
		if "user" not in st.session_state:
			st.session_state.user = None
		
		if "openai_model" not in st.session_state:
			st.session_state.openai_model = st.secrets["default_model"]

		if "msg" not in st.session_state:
			st.session_state.msg = []

		if "temp" not in st.session_state:
			st.session_state.temp = st.secrets["default_temp"]
		
		if "rating" not in st.session_state:
			st.session_state.rating = True
		
		if "frequency_penalty" not in st.session_state:
			st.session_state.frequency_penalty = st.secrets["default_frequency_penalty"]

		if "presence_penalty" not in st.session_state:
			st.session_state.presence_penalty = st.secrets["default_presence_penalty"]
		
		if "memoryless" not in st.session_state:
			st.session_state.memoryless = False

		if "vs" not in st.session_state:
			st.session_state.vs = False
		
		if "visuals" not in st.session_state:
			st.session_state.visuals = False
		
		if "svg_height" not in st.session_state:
			st.session_state["svg_height"] = 1000

		if "previous_mermaid" not in st.session_state:
			st.session_state["previous_mermaid"] = ""
			
		if "current_model" not in st.session_state:
			st.session_state.current_model = "No KB loaded"

		if "func_options" not in st.session_state:
			st.session_state.func_options = {
				'Personal Dashboard': True,
				'Class Dashboard': True,
				'Lesson Collaborator': True,
				'Lesson Commentator': True,
				'Mindmap Generator': True,
				'Conversation feedback': True,
				'Chatbot': True,
				'Chatbot Management': True,
				'Files management': True,
				'KB management': True,
				'Organisation Management': True,
				'School Users Management': True
			}

		create_dbs()
		initialise_admin_account()
		#PLEASE REMOVE THIS 
		#st.write("User Profile: ", st.session_state.user)
		
		#PLEASE REMOVE ABOVE
		with st.sidebar: #options for sidebar

			#Menu using antd components
			image = Image.open('primary_green.png')
			st.image(image)

			if st.session_state.login == False:
				st.session_state.title_page = DEFAULT_TITLE
				st.session_state.option = menu([MenuItem('Users login', icon='people'), MenuItem('Application Info', icon='info-circle')])
		
			else:
				if st.session_state.user['profile_id'] == SA: #super admin login feature
					# Initialize the session state for function options
					st.session_state.func_options = {
						'Personal Dashboard': False,
						'Class Dashboard': False,
						'Lesson Collaborator': False,
						'Lesson Commentator': False,
						'Mindmap Generator': False,
						'Conversation feedback': False,
						'Chatbot': False,
						'Chatbot Management': False,
						'Files management': False,
						'KB management': False,
						'Organisation Management': False,
						'School Users Management': False
					}
				else:
					set_function_access_for_user(st.session_state.user['id'])
				
					# Using the is_function_disabled function for setting the `disabled` attribute
				st.session_state.option = sac.menu([
					sac.MenuItem('Home', icon='house', children=[
						sac.MenuItem('Personal Dashboard', icon='person-circle', disabled=is_function_disabled('Personal Dashboard')),
						sac.MenuItem('Class Dashboard', icon='clipboard-data', disabled=is_function_disabled('Class Dashboard')),
					]),
					sac.MenuItem('Lesson Assistant', icon='person-fill-gear', children=[
						sac.MenuItem('Lesson Collaborator', icon='pencil-square', disabled=is_function_disabled('Lesson Collaborator')),
						sac.MenuItem('Lesson Commentator', icon='chat-left-dots', disabled=is_function_disabled('Lesson Commentator')),
					]),
					sac.MenuItem('Learning Tools', icon='tools', children=[
						sac.MenuItem('Knowledge Map Generator', icon='diagram-3-fill', disabled=is_function_disabled('Mindmap Generator')),
						sac.MenuItem('Conversation Assistant', icon='people-fill', disabled=is_function_disabled('Conversation feedback')),
					]),
					sac.MenuItem('Dialogic Agent', icon='robot', children=[
						sac.MenuItem('Chatbot', icon='chat-dots', disabled=is_function_disabled('Chatbot')),
						sac.MenuItem('Bot & Prompt Management', icon='wrench', disabled=is_function_disabled('Chatbot Management')),
					]),
					sac.MenuItem('Knowledge Base Tools', icon='book', children=[
						sac.MenuItem('Files Management', icon='file-arrow-up', disabled=is_function_disabled('Files management')),
						sac.MenuItem('Knowledge Base Editor', icon='database-fill-up',disabled=is_function_disabled('KB management')),
					]),
					sac.MenuItem('Organisation Tools', icon='buildings', children=[
						sac.MenuItem('Org Management', icon='building-gear', disabled=is_function_disabled('Organisation Management')),
						sac.MenuItem('Users Management', icon='house-gear', disabled=is_function_disabled('School Users Management')),
					]),
					sac.MenuItem(type='divider'),
					sac.MenuItem('OpenAI API Key', icon='key-fill'),  # Assuming these are always available
					sac.MenuItem('Profile Settings', icon='gear'),
					sac.MenuItem('Application Info', icon='info-circle'),
					sac.MenuItem('Logout', icon='box-arrow-right'),
				], index=1, format_func='title', open_all=False)

		if st.session_state.option == 'Users login':
				col1, col2 = st.columns([3,4])
				placeholder2 = st.empty()
				with placeholder2:
					with col1:
						if login_function() == True:
							placeholder2.empty()
							st.session_state.login = True
							st.session_state.user = load_user_profile(st.session_state.user)
							pre_load_variables(st.session_state.user['id'])
							load_and_fetch_vectorstore_for_user(st.session_state.user['id'])
							load_bot_settings(st.session_state.user['id'])
							st.experimental_rerun()
					with col2:
						st.write("Please read.me before using or forking this application")
				
		
		#Personal Dashboard
		elif st.session_state.option == 'Personal Dashboard':
			st.subheader(f":green[{st.session_state.option}]")
			if st.session_state.user['profile_id'] == SA:
				sch_id, msg = process_user_profile(st.session_state.user["profile_id"])
				st.write(msg)
				download_data_table_csv(st.session_state.user["id"], sch_id, st.session_state.user["profile_id"])
			else:
				download_data_table_csv(st.session_state.user["id"], st.session_state.user["school_id"], st.session_state.user["profile_id"])
			display_vectorstores()
			vectorstore_selection_interface(st.session_state.user['id'])
		elif st.session_state.option == 'Class Dashboard':
			st.subheader(f":green[{st.session_state.option}]") 
			pass
		#Lesson Assistant
		elif st.session_state.option == "Lesson Collaborator":
			st.subheader(f":green[{st.session_state.option}]") 
			prompt = lesson_collaborator()
			if prompt:
				lesson_bot(prompt, st.session_state.lesson_collaborator)	
					
		elif st.session_state.option == "Lesson Commentator":
			st.subheader(f":green[{st.session_state.option}]") 
			prompt = lesson_commentator()
			if prompt:
				lesson_bot(prompt, st.session_state.lesson_commentator)

		#Dialogic Agent
		elif st.session_state.option == "Chatbot":
			st.subheader(f":green[{st.session_state.option}]") 
			#check if api key is entered
			if st.session_state.api_key == False:
				sac.alert(message='**OpenAPI API Key not found, enter an API key for the chatbot to function**', description=None, type='error', height=None, icon=True, closable=True, banner=True)
			
			#customise chatbot remove config ini chatbot in prompt template as chatbot is redundant, use default as the chatbot template  if you want to add buttons
			# choice = sac.buttons([
			# 					sac.ButtonsItem(label='Support', icon='person-hearts',color='green'),
			# 					sac.ButtonsItem(label='Default', icon='person-fill',color='blue'),
			# 					sac.ButtonsItem(label='Creative', icon='person-plus-fill',color='red'),
			# 				], index=1,format_func='title', align='center', size='small', type='primary')
			# sac.divider(label='Chabot Settings', icon='robot', align='center', direction='horizontal', dashed=False, bold=False)
			# if choice == "Support":
			# 	st.session_state.chatbot = st.session_state.support
			# elif choice == "Default":
			# 	st.session_state.chatbot = st.session_state.default
			# elif choice == "Creative":
			# 	st.session_state.chatbot = st.session_state.creative
			
			col1, col3, col4, col5, col6, col7 = st.columns([2,1,1,1,1,1]) #column separation
			with col1:
				st.write(f"Knowledge Base: :green[{st.session_state.current_model}]")
				
			# with col2:
			# 	vm = sac.switch(label='Visual Mapping', value=False, align='start', position='left', size='small')
			# 	if vm == True:	
			# 		st.session_state.visuals = True
			# 	else:
			# 		st.session_state.visuals = False
			with col3:
				clear = sac.switch(label='Clear Chat', value=False, align='start', position='left', size='default')
				if clear == True:	
					clear_session_states()
			with col4:
				mem = sac.switch(label='Enable Memory', value=True, align='start', position='left', size='default')
				if mem == True:	
					st.session_state.memoryless = False
				else:
					st.session_state.memoryless = True
			with col5:
				rating = sac.switch(label='Rate Response', value=True, align='start', position='left', size='default')
				if rating == True:	
					st.session_state.rating = True
				else:
					st.session_state.rating = False
			if st.session_state.vs:#chatbot with knowledge base
				with col6:
					raw_search = sac.switch(label='Raw Search', value=False, align='start', position='left', size='default')
				with col7:
					unload = sac.switch(label='Unload KB', value=False, align='start', position='left', size='default')
					if unload == True:	
						st.session_state.vs = False
						st.session_state.current_model = "No KB loaded"
						st.experimental_rerun()
	
				if raw_search == True and st.session_state.vs:
					search_bot()
				else:
					if st.session_state.memoryless: #memoryless chatbot with knowledge base but no memory
						basebot_qa()
					else:
						basebot_qa_memory() #chatbot with knowledge base and memory
			else:#chatbot with no knowledge base
				
				chat_bot_vectorstore_selection_interface(st.session_state.user['id'], col6, col7)
				if st.session_state.memoryless: #memoryless chatbot with no knowledge base and no memory
					basebot()
				else:
					basebot_memory() #chatbot with no knowledge base but with memory
		elif st.session_state.option == 'Bot & Prompt Management':
			st.subheader(f":green[{st.session_state.option}]") 
			#st.warning("Select Knowledge Base for you chatbot to interact or remove for normal Chatbot")
			#select_vectorstores()
			#st.warning("Clear current messages and unload knowledge base of the chatbot")
			#if st.button("Clear Messages"):
				#reset_vecstores()
			#st.write(st.session_state.chatbot,st.session_state.lesson_collaborator ,st.session_state.lesson_commentator)
			create_prompt_template(st.session_state.user['id'])
			update_prompt_template(st.session_state.user['profile_id'])
			st.subheader("OpenAI Chatbot Parameters Settings")
			bot_settings_interface(st.session_state.user['profile_id'], st.session_state.user['school_id'])
		
		#Knowledge Base Tools
		elif st.session_state.option == 'Files Management':
			st.subheader(f":green[{st.session_state.option}]") 
			display_files()
			docs_uploader()
			delete_files()

		elif st.session_state.option == "Knowledge Base Editor":
			st.subheader(f":green[{st.session_state.option}]")
			if st.session_state.api_key == False:
				sac.alert(message='**OpenAPI API Key not found, enter an API key to create the vectorstores**', description=None, type='error', height=None, icon=True, closable=True, banner=True)
			options = sac.steps(
				items=[
					sac.StepsItem(title='Step 1', description='Create a new knowledge base'),
					sac.StepsItem(title='Step 2', description='Assign a knowledge base to a user'),
					sac.StepsItem(title='Step 3', description='Delete a knowledge base (Optional)'),
				],
				format_func='title',
				placement='vertical',
				size='small'
			)
			if options == "Step 1":
				st.subheader("KB created in the repository")
				display_vectorstores()
				st.subheader("Files available in the repository")
				display_files()
				create_vectorstore()
			elif options == "Step 2":
				st.subheader("KB created in the repository")
				display_vectorstores()
				vectorstore_selection_interface(st.session_state.user['id'])
				link_profiles_to_vectorstore_interface(st.session_state.user['id'])
	
			elif options == "Step 3":
				st.subheader("KB created in the repository")
				display_vectorstores()
				delete_vectorstores()
		
		#Organisation Tools
		elif st.session_state.option == "Users Management":
			st.subheader(f":green[{st.session_state.option}]") 
			sch_id, msg = process_user_profile(st.session_state.user["profile_id"])
			rows = has_at_least_two_rows()
			if rows >= 2:
				#Password Reset
				st.subheader("User accounts information")
				df = display_accounts(sch_id)
				st.warning("Password Management")
				st.subheader("Reset passwords of users")
				reset_passwords(df)
		
		elif st.session_state.option == "Org Management":
			st.subheader(f":green[{st.session_state.option}]") 
			#direct_vectorstore_function()
			
			if check_password(st.session_state.user["username"], SUPER_PWD):
					st.write("To start creating your teachers account, please change the default password of your administrator account under profile settings")
			else:
				sch_id, msg = process_user_profile(st.session_state.user["profile_id"])
				create_flag = False
				rows = has_at_least_two_rows()
				if rows >= 2:
					create_flag = check_multiple_schools()
				st.markdown("###")
				st.write(msg)
				st.markdown("###")
				steps_options = sac.steps(
							items=[
								sac.StepsItem(title='step 1', description='Create Students and Teachers account of a new school', disabled=create_flag),
								sac.StepsItem(title='step 2', description='Remove/Assign Teachers to Classes'),
								sac.StepsItem(title='step 3', description='Change Teachers Profile'),
								sac.StepsItem(title='step 4', description='Setting function access for profiles'),
								sac.StepsItem(title='step 5', description='Reassign Students to Classes(Optional)'),
								sac.StepsItem(title='step 6', description='Managing SQL Schema Tables',icon='radioactive'),
							], format_func='title', placement='vertical', size='small'
						)
				if steps_options == "step 1":
					if create_flag:
						st.write("School created, click on Step 2")
					else:
						create_org_structure()
				elif steps_options == "step 2":
					remove_or_reassign_teacher_ui(sch_id)
				elif steps_options == "step 3":
					change_teacher_profile_ui(sch_id)
				elif steps_options == "step 4":
					link_users_to_app_function_ui(sch_id)
				elif steps_options == "step 5":
					reassign_student_ui(sch_id)
				elif steps_options == "step 6":
					st.subheader(":red[Managing SQL Schema Tables]")
					st.warning("Please do not use this function unless you know what you are doing")
					if st.checkbox("I know how to manage SQL Tables"):
						st.subheader(":red[Display and Edit Tables - please do so if you have knowledge of the current schema]")
						manage_tables()
						st.subheader(":red[Delete Table - Warning please use this function with extreme caution]")
						delete_tables()
		elif st.session_state.option == "Knowledge Map Generator":
			st.subheader(f":green[{st.session_state.option}]") 
			mode = sac.switch(label='Generative Mode: ', value=True, checked='Coloured Map', unchecked='Process Chart', align='center', position='left', size='default', disabled=False)
			subject, topic, levels = map_creation_form()
			prompt = False
			if subject and topic and levels:
				if mode:
					prompt = map_prompter_with_plantuml_form(subject, topic, levels)
				else:
					prompt = map_prompter(subject, topic, levels)
			if prompt:
				with st.spinner("Generating mindmap"):
					st.write(f"Mindmap generated from the prompt: :orange[**{subject} {topic} {levels}**]")
					if mode:
						uml = generate_plantuml_mindmap(prompt)
						image = render_diagram(uml)
						st.image(image)
					else:
						generate_mindmap(prompt)
					
		elif st.session_state.option == "Conversation Assistant":
			st.subheader(f":green[{st.session_state.option}]") 
			# Create form
			subject = st.text_input("Subject:")
			topic = st.text_input("Topic:")
			language = st.selectbox("Language:", ["English", "Chinese", "Malay", "Tamil"])
			assessment_type = st.selectbox("Type of Assessment:", ["Oral Assessment", "Content Assessment", "Transcribing No Assessment"])
			transcript = record_myself()
			if transcript:
				if assessment_type == "Transcribing No Assessment":
					st.write(f"Transcript: {transcript}")
				else:
					if subject and topic and language:
						assessment_prompt(transcript, assessment_type, subject, topic, language)
					else:
						st.warning("Please fill in all the fields in the oral submission form")

		#Settings Menu
		elif st.session_state.option == 'OpenAI API Key':
			st.subheader(f":green[{st.session_state.option}]") 
			if st.secrets["openai_key"] != "None":
				st.success("OpenAI API key is deployed in this application")
			else:
				API_KEY = st.text_input("Please enter your OpenAI API KEY",type="password")
				if API_KEY:
					st.session_state.api_key = API_KEY 
					openai.api_key = st.session_state.api_key
				else:
					st.session_state.api_key = False
						
		
		elif st.session_state.option == "Profile Settings":
			st.subheader(f":green[{st.session_state.option}]") 
			#direct_vectorstore_function()
			password_settings(st.session_state.user["username"])
		
		

		elif st.session_state.option == 'Application Info':
			st.subheader(f":green[{st.session_state.option}]") 
			st.markdown("Application Information here")
			pass

		elif st.session_state.option == 'Logout':
			for key in st.session_state.keys():
				del st.session_state[key]
			st.experimental_rerun()
			pass
	except Exception as e:
		st.exception(e)

if __name__ == "__main__":
	main()
