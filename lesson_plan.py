#No need database
import streamlit as st
import streamlit_antd_components as sac
import tempfile
from langchain.document_loaders import UnstructuredFileLoader
from langchain.memory import ConversationBufferWindowMemory
from main_bot import insert_into_data_table, rating_component
import openai
from datetime import datetime
import configparser
import os
import ast
config = configparser.ConfigParser()
config.read('config.ini')
DEFAULT_TEXT = config['constants']['DEFAULT_TEXT']
SUBJECTS_LIST = config.get('menu_lists','SUBJECTS_SINGAPORE')
SUBJECTS_SINGAPORE = ast.literal_eval(SUBJECTS_LIST )


if "api_key" not in st.session_state:
	st.session_state.api_key = False
	if st.secrets["openai_key"] != "None":
		st.session_state.api_key  = st.secrets["openai_key"]
		os.environ["OPENAI_API_KEY"] = st.secrets["openai_key"]

# Create or check for the 'database' directory in the current working directory
cwd = os.getcwd()
WORKING_DIRECTORY = os.path.join(cwd, "database")

if not os.path.exists(WORKING_DIRECTORY):
	os.makedirs(WORKING_DIRECTORY)

if st.secrets["sql_ext_path"] == "None":
	WORKING_DATABASE= os.path.join(WORKING_DIRECTORY , st.secrets["default_db"])
else:
	WORKING_DATABASE= st.secrets["sql_ext_path"]


#direct load into form 
def upload_lesson_plan():

	def get_file_extension(file_name):
		return os.path.splitext(file_name)[1]

	# Streamlit file uploader to accept file input
	uploaded_file = st.file_uploader("Upload a lesson plan file", type=['docx', 'txt', 'pdf'])

	if uploaded_file:

		# Reading file content
		file_content = uploaded_file.read()

		# Determine the suffix based on uploaded file's name
		file_suffix = get_file_extension(uploaded_file.name)

		# Saving the uploaded file temporarily to process it
		with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as temp_file:
			temp_file.write(file_content)
			temp_file.flush()  # Ensure the data is written to the file
			temp_file_path = temp_file.name

		# Process the temporary file using UnstructuredFileLoader (or any other method you need)
		#st.write(temp_file_path)
		loader = UnstructuredFileLoader(temp_file_path)
		docs = loader.load()

		st.success("File processed and added to form")

		# Removing the temporary file after processing
		os.remove(temp_file_path)
		return docs

def lesson_collaborator():
    st.subheader("1. Basic Lesson Information for Generator")
    subject = st.selectbox("Choose a Subject", SUBJECTS_SINGAPORE)
    age_or_grade = st.text_input("Age or Grade Level")
    duration = st.text_input("Duration (in minutes)")

    st.subheader("2. Lesson Details for Generator")
    topic = st.text_area("Topic", help="Describe the specific topic or theme for the lesson")
    skill_level = st.selectbox("Ability or Skill Level", ["Beginner", "Intermediate", "Advanced", "Mixed"])
    
    st.subheader("3. Lesson Details for Generator")
    prior_knowledge = st.text_area("Prior Knowledge")
    learners_info = st.text_input("Describe the learners for this lesson")
    incorporate_elements = st.text_area("Incorporate lesson elements")

    build = sac.buttons([
                dict(label='Generate', icon='check-circle-fill', color = 'green'),
                dict(label='Cancel', icon='x-circle-fill', color='red'),
            ], label=None, index=1, format_func='title', align='center', position='top', size='default', direction='horizontal', shape='round', type='default', compact=False)

    if build != 'Cancel':
        lesson_prompt = f"""Imagine you are an experienced teacher. Design and generate a lesson suitable for my learner based on:
                            Subject: {subject}
                            Topic: {topic}
                            Age or Grade Level: {age_or_grade}
                            Duration: {duration} minutes
                            Skill Level: {skill_level}
                            Description of Learners: {learners_info}
                            Student's prior knowledge: {prior_knowledge}
                            Incorporate the following lesson elements: {incorporate_elements}"""
        st.success("Your lesson generation information has been submitted!")
        return lesson_prompt

    return False


def lesson_commentator():
    st.subheader("1. Basic Lesson Information for Feedback")
    subject = st.selectbox("Choose a Subject", SUBJECTS_SINGAPORE)
    age_or_grade = st.text_input("Age or Grade Level")
    duration = st.text_input("Duration (in minutes)")

    st.subheader("2. Lesson Details for Feedback")
    topic = st.text_area("Topic", help="Describe the specific topic or theme for the lesson")
    skill_level = st.selectbox("Ability or Skill Level", ["Beginner", "Intermediate", "Advanced", "Mixed"])
    
    st.subheader("3. Lesson Plan upload or key in manually")
    lesson_plan_content = upload_lesson_plan()
    lesson_plan = st.text_area("Please provide your lesson plan either upload or type into this text box, including details such as learning objectives, activities, assessment tasks, and any use of educational technology tools.", height=500, value=lesson_plan_content)
    
    st.subheader("4. Specific questions that I would like feedback on")
    feedback = st.text_area("Include specific information from your lesson plan that you want feedback on.")
    
    st.subheader("5. Learners Profile")
    learners_info = st.text_input("Describe the learners for this lesson ")

    build = sac.buttons([
                dict(label='Feedback', icon='check-circle-fill', color = 'green'),
                dict(label='Cancel', icon='x-circle-fill', color='red'),
            ], label=None, index=1, format_func='title', align='center', position='top', size='default', direction='horizontal', shape='round', type='default', compact=False)

    if build != 'Cancel':
        feedback_template = f"""Imagine you are an experienced teacher. I'd like feedback on the lesson I've uploaded:
            Subject: {subject}
            Topic: {topic}
            Age or Grade Level: {age_or_grade}
            Duration: {duration} minutes
            Skill Level: {skill_level}
            Lesson Plan Content: {lesson_plan}
            Specific Feedback Areas: {feedback}
            Description of Learners: {learners_info}
            Please provide feedback to enhance this lesson plan."""
        st.success("Your lesson plan has been submitted for feedback!")
        return feedback_template

    return False

#chat completion memory for streamlit using memory buffer
def template_prompt(prompt, prompt_template):
	response = openai.ChatCompletion.create(
		model=st.session_state.openai_model,
		messages=[
			{"role": "system", "content":prompt_template},
			{"role": "user", "content": prompt},
		],
		temperature=st.session_state.temp, #settings option
		stream=True #settings option
	)
	return response


def lesson_bot(prompt, prompt_template):
	try:
		if prompt:
			if "memory" not in st.session_state:
				st.session_state.memory = ConversationBufferWindowMemory(k=5)
			st.session_state.msg.append({"role": "user", "content": prompt})
			message_placeholder = st.empty()
			#check if there is any knowledge base
			if st.session_state.vs:
				docs = st.session_state.vs.similarity_search(prompt)
				resources = docs[0].page_content
				reference_prompt = f"""You may refer to this resources to improve or design the lesson
										{resources}
									"""
			else:
				st.warning("There is no knowledge base linked to this generative AI form")
				reference_prompt = ""
			full_response = ""
			for response in template_prompt(prompt, reference_prompt + prompt_template):
				full_response += response.choices[0].delta.get("content", "")
				message_placeholder.markdown(full_response + "▌")
			message_placeholder.markdown(full_response)
			if st.session_state.rating == True:
				feedback_value = rating_component()
			else:
				feedback_value = 0
			st.session_state.msg.append({"role": "assistant", "content": full_response})
			st.session_state["memory"].save_context({"input": prompt},{"output": full_response})
			 # Insert data into the table
			now = datetime.now() # Using ISO format for date
			num_tokens = len(full_response)*1.3
			#st.write(num_tokens)
			insert_into_data_table(now.strftime("%d/%m/%Y %H:%M:%S"),  full_response, prompt, num_tokens, feedback_value)
	except Exception as e:
		st.error(e)


