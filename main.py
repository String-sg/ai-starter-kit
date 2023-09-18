import streamlit as st
import openai
from streamlit_antd_components import menu, MenuItem
import streamlit_antd_components as sac
from qa_doc import docs_uploader, create_vectorstores, dbs_deleter, select_vectorstores, load_default_vectorstore_for_user, reset_vecstores
from main_bot import basebot_memory, basebot_qa_memory
from settings import check_setup, create_admin_account, create_dbs, password_settings, load_current_template, create_prompt_template
from authenticate import login_function
from class_dash import download_data_table_csv
from PIL import Image


def main():
	st.title("CherGPT Starter Kit")
	sac.divider(label='A String Initiative', icon='house', align='center', direction='horizontal', dashed=False, bold=False)
	if st.secrets["openai_key"] != "None":
		st.session_state.api_key  = st.secrets["openai_key"]
		openai.api_key = st.secrets["openai_key"]

	create_dbs()
	create_admin_account()
		
	if "option" not in st.session_state:
		st.session_state.option = False
	
	if "login" not in st.session_state:
		st.session_state.login = False
	
	if "user" not in st.session_state:
		st.session_state.user = ""
	
	if "openai_model" not in st.session_state:
		st.session_state.openai_model = st.secrets["default_model"]

	if "msg" not in st.session_state:
		st.session_state.msg = []

	if "temp" not in st.session_state:
		st.session_state.temp = st.secrets["default_temp"]

	if "vs" not in st.session_state:
		st.session_state.vs = False
	
	if "current_model" not in st.session_state:
		st.session_state.current_model = "No VectorStore loaded"
	
	if "prompt_template" not in st.session_state:
		st.session_state.prompt_template = "You are a helpful assistant."

	if "prompt_profile" not in st.session_state:
		st.session_state.prompt_profile = False
	
	with st.sidebar: #options for sidebar

		#Menu using antd components
		image = Image.open('string.png')
		st.image(image)

		if st.session_state.login == False:
			st.session_state.option = menu([MenuItem('Users login', icon='people'), MenuItem('Application Info', icon='info-circle'), MenuItem('OpenAI API Key', icon='key-fill')])
	
		else:

			if st.session_state.user['profile'] == "administrator": #teacher login features
				st.session_state.option = menu([MenuItem('Class Information', icon='clipboard-data'),
								MenuItem('Chatbot', icon='chat-dots'),
								MenuItem('Chatbot Management', icon='robot'),
								MenuItem('Docs Management', icon='box-fill'),
								MenuItem('Knowledge Base Management', icon='database-add'),
								MenuItem('User Management', icon='people'),
								MenuItem('Profile Settings', icon='gear'),
								MenuItem(type='divider'),
								MenuItem('Logout', icon='box-arrow-right'),],open_all=True)
			elif st.session_state.user['profile'] == "teacher": #teacher login features
				st.session_state.option = menu([MenuItem('Class Information', icon='clipboard-data'),
								MenuItem('Chatbot', icon='chat-dots'),
								MenuItem('Chatbot Management', icon='robot'),
								MenuItem('Docs Management', icon='box-fill'),
								MenuItem('Knowledge Base Management', icon='database-add'),
								MenuItem('Profile Settings', icon='gear'),
								MenuItem(type='divider'),
								MenuItem('Logout', icon='box-arrow-right'),],open_all=True)
			else: #student login features
				st.session_state.option = menu([MenuItem('Class Information', icon='clipboard-data'),
							MenuItem('Chatbot', icon='chat-dots'),
							MenuItem('Chatbot Management', icon='robot'),
							MenuItem('Profile Settings', icon='gear'),
							MenuItem(type='divider'),
							MenuItem('Logout', icon='box-arrow-right'),],open_all=True)

	if st.session_state.option == 'Users login':
			col1, col2 = st.columns([3,4])
			placeholder2 = st.empty()
			with placeholder2:
				with col1:
					if login_function() == True:
						placeholder2.empty()
						st.session_state.login = True
						vectorstore_instance, model = load_default_vectorstore_for_user(st.session_state.user["username"])
						if vectorstore_instance and st.session_state.current_model:
							st.session_state.vs = vectorstore_instance
							st.session_state.current_model = model
						st.session_state.prompt_profile = load_current_template(st.session_state.user["username"])
						st.experimental_rerun()
			
	elif st.session_state.option == 'OpenAI API Key':
		if st.secrets["openai_key"] != "None":
			st.success("OpenAI API key is deployed in this application")
		else:
			API_KEY = st.text_input("Please enter your OpenAI API KEY",type="password")
			if API_KEY:
				st.session_state.api_key = API_KEY 
				openai.api_key = st.session_state.api_key

	elif st.session_state.option == 'Application Info':
		st.markdown("Application Information here")
		pass
	
	elif st.session_state.option == 'Class Information':
		download_data_table_csv(st.session_state.user["username"], st.session_state.user["profile"])
	elif st.session_state.option == 'Docs Management':
		docs_uploader()
	elif st.session_state.option == 'Chatbot Management':
		st.warning("Select Knowledge Base for you chatbot to interact or remove for normal Chatbot")
		select_vectorstores()
		st.warning("Clear current messages and unload knowledge base of the chatbot")
		if st.button("Clear Messages"):
			reset_vecstores()
		if st.session_state.user["profile"] == "administrator":
			st.warning("Prompt Settings for non-KB bot - it will affect all users")
			create_prompt_template(st.session_state.prompt_profile["username"], st.session_state.prompt_profile["template_name"], st.session_state.prompt_profile["prompt_data"])

	elif st.session_state.option == "Chatbot":
		#query = "What is the cause of World War 3?"
		#st.write(type(st.session_state.vs))
		
		if st.session_state.vs:
			st.success(f"Current knowledge base : {st.session_state.current_model}",icon="✅")
			basebot_qa_memory()
		else:
			sac.alert(message='**The Chatbot is not linked to any knowledge base**', description=None, type='warning', height=None, icon=True, closable=True, banner=True)
			#basebot()
			basebot_memory()

	elif st.session_state.option == "Knowledge Base Management":
		#direct_vectorstore_function()
		create_vectorstores()
		#dbs_deleter()
	elif st.session_state.option == "User Management":
		#direct_vectorstore_function()
		check_setup()
	elif st.session_state.option == "Profile Settings":
		#direct_vectorstore_function()
		password_settings(st.session_state.user["username"])

	elif st.session_state.option == 'Logout':
		for key in st.session_state.keys():
			del st.session_state[key]
		st.experimental_rerun()
		pass

if __name__ == "__main__":
	main()