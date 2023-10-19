# No need SQLite
from files_module import delete_files, display_files, docs_uploader
from kb_module import delete_vectorstores, display_vectorstores
import streamlit as st
from analytics_dashboard import pandas_ai, download_data
from streamlit_antd_components import menu, MenuItem
import streamlit_antd_components as sac
from main_bot import basebot_memory, basebot_qa_memory, clear_session_states, search_bot, basebot, basebot_qa
# from kb_module import display_files, docs_uploader, delete_files
# from vs_module import display_vectorstores, create_vectorstore, delete_vectorstores
from authenticate import login_function, check_password
from class_dash import download_data_table_csv
from lesson_plan import lesson_collaborator, lesson_commentator, lesson_bot
# New schema move function fom settings
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
    link_profiles_to_vectorstore_interface
)
from k_map import (
    map_prompter,
    generate_mindmap,
    map_creation_form,
    map_prompter_with_plantuml_form,
    generate_plantuml_mindmap,
    render_diagram,
    output_mermaid_diagram
)
from audio import record_myself, assessment_prompt
from bot_settings import bot_settings_interface, load_bot_settings
from PIL import Image
import configparser
import os
import ast
from metacog import science_feedback, reflective_peer


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
COTF = config_handler.get_value('constants', 'COTF')
META = config_handler.get_value('constants', 'META')
PANDAI = config_handler.get_value('constants', 'PANDAI')
MENU_FUNCS = config_handler.get_value('menu_lists', 'MENU_FUNCS')
META_BOT = config_handler.get_value('constants', 'META_BOT')
QA_BOT = config_handler.get_value('constants', 'QA_BOT')
LESSON_BOT = config_handler.get_value('constants', 'LESSON_BOT')
LESSON_COLLAB = config_handler.get_value('constants', 'LESSON_COLLAB')
LESSON_COMMENT = config_handler.get_value('constants', 'LESSON_COMMENT')
LESSON_MAP = config_handler.get_value('constants', 'LESSON_MAP')
REFLECTIVE = config_handler.get_value('constants', 'REFLECTIVE')
CONVERSATION = config_handler.get_value('constants', 'CONVERSATION')
MINDMAP = config_handler.get_value('constants', 'MINDMAP')
METACOG = config_handler.get_value('constants', 'METACOG')


def is_function_disabled(function_name):
    return st.session_state.func_options.get(function_name, True)


def initialize_session_state(menu_funcs, default_value):
    st.session_state.func_options = {
        key: default_value for key in menu_funcs.keys()}


def main():
    try:
        if "title_page" not in st.session_state:
            st.session_state.title_page = DEFAULT_TITLE

        st.title(st.session_state.title_page)
        sac.divider(label='by educators, for educators', icon='house',
                    align='center', direction='horizontal', dashed=False, bold=False)

        if "api_key" not in st.session_state:
            st.session_state.api_key = ""

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

        if "rating" not in st.session_state:
            st.session_state.rating = False

        if "temp" not in st.session_state:
            st.session_state.temp = st.secrets["default_temp"]

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
            st.session_state.func_options = {}
            initialize_session_state(MENU_FUNCS, True)

        create_dbs()
        initialise_admin_account()
        with st.sidebar:
            # KH: let's refactor this to a physical toggle instead of manually switching - definitely will cause accidental styling changes
            # if st.session_state.login == False:
            # 	image = Image.open('cotf_logo.png')
            # 	st.image(image)
            # else:
            # 	image_function(st.session_state.user['school_id'])
            if st.session_state.login == False:
                image = Image.open('primary_green.png')
                st.image(image)
                st.session_state.option = menu([MenuItem('Users login', icon='people'), MenuItem(
                    'Application Info', icon='info-circle')])
            else:
                image = Image.open('primary_green.png')
                st.image(image)
                # super admin login feature
                if st.session_state.user['profile_id'] == SA:
                    # Initialize the session state for function options
                    initialize_session_state(MENU_FUNCS, False)
                else:
                    set_function_access_for_user(st.session_state.user['id'])
                    # Using the is_function_disabled function for setting the `disabled` attribute

                st.session_state.option = sac.menu([
                    sac.MenuItem('Home', icon='house', children=[
                        sac.MenuItem('Personal Dashboard', icon='person-circle',
                                     disabled=is_function_disabled('Personal Dashboard')),
                        sac.MenuItem('Analytics Dashboard', icon='clipboard-data',
                                     disabled=is_function_disabled('Analytics Dashboard')),
                    ]),
                    sac.MenuItem('Lesson Assistant', icon='person-fill-gear', children=[
                        sac.MenuItem('Lesson Generator', icon='pencil-square',
                                     disabled=is_function_disabled('Lesson Generator')),
                        sac.MenuItem('Lesson Feedback', icon='chat-left-dots',
                                     disabled=is_function_disabled('Lesson Feedback')),
                    ]),
                    sac.MenuItem('Learning Tools', icon='tools', children=[
                        sac.MenuItem('Knowledge Map Generator', icon='diagram-3-fill',
                                     disabled=is_function_disabled('Knowledge Map Generator')),
                        sac.MenuItem('Conversation Assistant', icon='people-fill',
                                     disabled=is_function_disabled('Conversation Assistant')),
                    ]),
                    sac.MenuItem("Remarks Co-Pilot", icon='link-45deg', href='https://remarkscopilot.vercel.app',
                                 disabled=is_function_disabled('Remarks Copilot')),
                    sac.MenuItem('Dialogic Agent', icon='robot', children=[
                        sac.MenuItem('Chatbot', icon='chat-square-dots',
                                     disabled=is_function_disabled('Chatbot')),
                        sac.MenuItem('Bot & Prompt Management', icon='wrench',
                                     disabled=is_function_disabled('Chatbot Management')),
                    ]),
                    sac.MenuItem('Knowledge Base Tools', icon='book', children=[
                        sac.MenuItem('Files Management', icon='file-arrow-up',
                                     disabled=is_function_disabled('Files management')),
                        sac.MenuItem('Knowledge Base Editor', icon='database-fill-up',
                                     disabled=is_function_disabled('KB management')),
                    ]),
                    sac.MenuItem('Organisation Tools', icon='buildings', children=[
                        sac.MenuItem('Org Management', icon='building-gear',
                                     disabled=is_function_disabled('Organisation Management')),
                        sac.MenuItem('Users Management', icon='house-gear',
                                     disabled=is_function_disabled('School Users Management')),
                    ]),
                    sac.MenuItem(type='divider'),
                    sac.MenuItem('Profile Settings', icon='gear'),
                    sac.MenuItem('Application Info', icon='info-circle'),
                    sac.MenuItem('Logout', icon='box-arrow-right'),
                ], index=1, format_func='title', open_all=False)

        if st.session_state.option == 'Users login':
            if login_function() == True:
                placeholder2.empty()
                st.session_state.login = True
                st.session_state.user = load_user_profile(
                    st.session_state.user)
                pre_load_variables(st.session_state.user['id'])
                load_and_fetch_vectorstore_for_user(
                    st.session_state.user['id'])
                load_bot_settings(st.session_state.user['id'])
                st.rerun()

        # Personal Dashboard
        elif st.session_state.option == 'Personal Dashboard':
            st.subheader(f":green[{st.session_state.option}]")
            if st.session_state.user['profile_id'] == SA:
                sch_id, msg = process_user_profile(
                    st.session_state.user["profile_id"])
                st.write(msg)
                download_data_table_csv(
                    st.session_state.user["id"], sch_id, st.session_state.user["profile_id"])
            else:
                download_data_table_csv(
                    st.session_state.user["id"], st.session_state.user["school_id"], st.session_state.user["profile_id"])
            display_vectorstores()
            vectorstore_selection_interface(st.session_state.user['id'])
        elif st.session_state.option == 'Analytics Dashboard':
            st.subheader(f":green[{st.session_state.option}]")
            pandas_ai(
                st.session_state.user['id'], st.session_state.user['school_id'], st.session_state.user['profile_id'])
            pass
        # Lesson Assistant
        elif st.session_state.option == "Lesson Generator":
            st.subheader(f":green[{st.session_state.option}]")
            prompt = lesson_collaborator()
            if prompt:
                lesson_bot(
                    prompt, st.session_state.lesson_generator, LESSON_COLLAB)

        elif st.session_state.option == "Lesson Feedback":
            st.subheader(f":green[{st.session_state.option}]")
            prompt = lesson_commentator()
            if prompt:
                lesson_bot(prompt, st.session_state.lesson_feedback,
                           LESSON_COMMENT)

        elif st.session_state.option == "Chatbot":
            st.subheader(f":green[{st.session_state.option}]")
            sac.divider(label='Chatbot Settings', icon='robot', align='center',
                        direction='horizontal', dashed=False, bold=False)
            # check if API key is entered
            with st.expander("Chatbot Settings"):
                vectorstore_selection_interface(st.session_state.user['id'])
                if st.session_state.vs:  # chatbot with knowledge base
                    raw_search = sac.switch(
                        label='Raw Search', value=False, align='start', position='left')
                clear = sac.switch(label='Clear Chat',
                                   value=False, align='start', position='left')
                if clear == True:
                    clear_session_states()
                mem = sac.switch(label='Enable Memory',
                                 value=True, align='start', position='left')
                if mem == True:
                    st.session_state.memoryless = False
                else:
                    st.session_state.memoryless = True
                rating = sac.switch(label='Rate Response',
                                    value=True, align='start', position='left')
                if rating == True:
                    st.session_state.rating = True
                else:
                    st.session_state.rating = False
                # vm = sac.switch(label='Visual Mapping', value=False, align='start', position='left', size='small')
                # if vm == True:
                # 	st.session_state.visuals = True
                # else:
                # 	st.session_state.visuals = False
            if st.session_state.vs:  # chatbot with knowledge base
                if raw_search == True:
                    search_bot()
                else:
                    if st.session_state.memoryless:  # memoryless chatbot with knowledge base but no memory
                        basebot_qa(QA_BOT)
                    else:
                        # chatbot with knowledge base and memory
                        basebot_qa_memory(QA_BOT)
            else:  # chatbot with no knowledge base
                if st.session_state.memoryless:  # memoryless chatbot with no knowledge base and no memory
                    basebot(QA_BOT)
                else:
                    # chatbot with no knowledge base but with memory
                    basebot_memory(QA_BOT)

        # Dialogic Agent

        # ensure that it is for administrator or super_admin
        elif st.session_state.option == 'Bot & Prompt Management':
            if st.session_state.user['profile_id'] == SA or st.session_state.user['profile_id'] == AD:
                st.subheader(f":green[{st.session_state.option}]")
                create_prompt_template(st.session_state.user['id'])
                update_prompt_template(st.session_state.user['profile_id'])
                st.subheader("OpenAI Chatbot Parameters Settings")
                bot_settings_interface(
                    st.session_state.user['profile_id'], st.session_state.user['school_id'])
            else:
                st.subheader(
                    f":red[This option is accessible only to administrators only]")

        # Knowledge Base Tools
        elif st.session_state.option == 'Files Management':
            st.subheader(f":green[{st.session_state.option}]")
            display_files()
            docs_uploader()
            delete_files()

        elif st.session_state.option == "Knowledge Base Editor":
            st.subheader(f":green[{st.session_state.option}]")
            options = sac.steps(
                items=[
                    sac.StepsItem(title='Step 1',
                                  description='Create a new knowledge base'),
                    sac.StepsItem(
                        title='Step 2', description='Assign a knowledge base to a user'),
                    sac.StepsItem(
                        title='Step 3', description='Delete a knowledge base (Optional)'),
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
                link_profiles_to_vectorstore_interface(
                    st.session_state.user['id'])

            elif options == "Step 3":
                st.subheader("KB created in the repository")
                display_vectorstores()
                delete_vectorstores()

        # Organisation Tools
        elif st.session_state.option == "Users Management":
            st.subheader(f":green[{st.session_state.option}]")
            sch_id, msg = process_user_profile(
                st.session_state.user["profile_id"])
            rows = has_at_least_two_rows()
            if rows >= 2:
                # Password Reset
                st.subheader("User accounts information")
                df = display_accounts(sch_id)
                st.warning("Password Management")
                st.subheader("Reset passwords of users")
                reset_passwords(df)

        elif st.session_state.option == "Org Management":
            if st.session_state.user['profile_id'] == SA:
                st.subheader(f":green[{st.session_state.option}]")
                # direct_vectorstore_function()

                if check_password(st.session_state.user["username"], SUPER_PWD):
                    st.write(
                        "To start creating your teachers account, please change the default password of your administrator account under profile settings")
                else:
                    sch_id, msg = process_user_profile(
                        st.session_state.user["profile_id"])
                    create_flag = False
                    rows = has_at_least_two_rows()
                    if rows >= 2:
                        create_flag = check_multiple_schools()
                    st.markdown("###")
                    st.write(msg)
                    st.markdown("###")
                    steps_options = sac.steps(
                        items=[
                            sac.StepsItem(
                                title='step 1', description='Create Students and Teachers account of a new school', disabled=create_flag),
                            sac.StepsItem(
                                title='step 2', description='Remove/Assign Teachers to Classes'),
                            sac.StepsItem(
                                title='step 3', description='Change Teachers Profile'),
                            sac.StepsItem(
                                title='step 4', description='Setting function access for profiles'),
                            sac.StepsItem(
                                title='step 5', description='Reassign Students to Classes(Optional)'),
                            sac.StepsItem(
                                title='step 6', description='Managing SQL Schema Tables', icon='radioactive'),
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
                        st.warning(
                            "Please do not use this function unless you know what you are doing")
                        if st.checkbox("I know how to manage SQL Tables"):
                            st.subheader(
                                ":red[Display and Edit Tables - please do so if you have knowledge of the current schema]")
                            manage_tables()
                            st.subheader(
                                ":red[Delete Table - Warning please use this function with extreme caution]")
                            delete_tables()
            else:
                st.subheader(
                    f":red[This option is accessible only to super administrators only]")

        elif st.session_state.option == "Knowledge Map Generator":
            st.subheader(f":green[{st.session_state.option}]")
            mode = sac.switch(label='Generative Mode :', value=True, checked='Coloured Map',
                              unchecked='Process Chart', align='center', position='left', size='default', disabled=False)
            subject, topic, levels = map_creation_form()
            prompt = False
            if subject and topic and levels:
                if mode:
                    prompt = map_prompter_with_plantuml_form(
                        subject, topic, levels)
                else:
                    prompt = map_prompter(subject, topic, levels)
            if prompt:
                with st.spinner("Generating mindmap"):
                    st.write(
                        f"Mindmap generated from the prompt: :orange[**{subject} {topic} {levels}**]")
                    if mode:
                        uml = generate_plantuml_mindmap(prompt)
                        image = render_diagram(uml)
                        st.image(image)
                    else:
                        syntax = generate_mindmap(prompt)
                        if syntax:
                            output_mermaid_diagram(syntax)

        elif st.session_state.option == "Conversation Assistant":
            st.subheader(f":green[{st.session_state.option}]")
            # Create form
            subject = st.text_input("Subject:")
            topic = st.text_input("Topic:")
            assessment_type = st.selectbox("Type of Assessment:", [
                                           "Oral Assessment", "Content Assessment", "Transcribing No Assessment"])
            transcript = record_myself()
            if transcript:
                if assessment_type == "Transcribing No Assessment":
                    st.write(f"Transcript: {transcript}")
                    st.session_state.msg.append(
                        {"role": "assistant", "content": transcript})
                else:
                    if subject and topic:
                        assessment_prompt(
                            transcript, assessment_type, subject, topic)
                    else:
                        st.warning(
                            "Please fill in all the fields in the oral submission form")

        elif st.session_state.option == "Profile Settings":
            st.subheader(f":green[{st.session_state.option}]")
            # direct_vectorstore_function()
            password_settings(st.session_state.user["username"])

        elif st.session_state.option == 'Application Info':
            st.subheader("About")
            st.markdown(
                "The problem is twofold: getting visibility to chatlogs for educators; and accelerating rapid prototyping in the Education sector.")
            st.markdown(
                "(1) We built this app to enable more educators to first enable educators to guide student interactions with AI chatbots. While there are ample AI chatbots present - OpenAI’s ChatGPT, Microsoft’s Bing, Anthropic's Claude among others - none of them provide visibility into backend out-of-the-box.")
            st.markdown(
                "(2) The second and more interesting problem that we want to solve is to eliminate redundancy for overlapping development work in creating basic AI-powered chatbots. [After various rounds of iteration](https://teachertech.beehiiv.com/p/chergpt-product-log) we know there are a number of base features that educators want.")
            st.subheader("Team")
            st.markdown("Main Developer: Joe Tay")
            st.markdown("Product: Kahhow")
            st.markdown("Product Ops: Lance, Adrian")
            pass
        elif st.session_state.option == 'Logout':
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
            pass
    except Exception as e:
        st.exception(e)


if __name__ == "__main__":
    main()

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
