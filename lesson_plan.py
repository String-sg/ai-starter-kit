#No need database
import streamlit as st
import streamlit_antd_components as sac
import tempfile
from langchain.document_loaders import UnstructuredFileLoader
from langchain.memory import ConversationBufferWindowMemory
from main_bot import insert_into_data_table
import openai
from authenticate import return_api_key
from datetime import datetime
from k_map import generate_mindmap, output_mermaid_diagram
import configparser
import os
import ast
from users_module import vectorstore_selection_interface
from main_bot import rating_component
config = configparser.ConfigParser()
config.read('config.ini')

DEFAULT_TEXT = config['constants']['DEFAULT_TEXT']
SUBJECTS_LIST = config.get('menu_lists','SUBJECTS_SINGAPORE')
SUBJECTS_SINGAPORE = ast.literal_eval(SUBJECTS_LIST )
PRI_LEVELS = [f"Primary {i}" for i in range(1, 7)]
SEC_LEVELS = [f"Secondary {i}" for i in range(1, 6)]
JC_LEVELS = [f"Junior College {i}" for i in range(1, 4)]
EDUCATION_LEVELS = PRI_LEVELS + SEC_LEVELS + JC_LEVELS



if "lesson_plan" not in st.session_state:
	st.session_state.lesson_plan = ""

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
	level = st.selectbox("Grade Level", EDUCATION_LEVELS)
	lessons = st.number_input(
		"Number of lessons/ periods", min_value=1.0, step=0.5, format='%.2f')
	duration = st.number_input(
		"How long is a period/ lesson (in minutes)", min_value=30, step=5, format='%i')
	total_duration = lessons * duration

	st.subheader("2. Lesson Details for Generator")
	topic = st.text_area(
		"Topic", help="Describe the specific topic or theme for the lesson")
	skill_level = st.selectbox("Ability or Skill Level", [
		"Beginner", "Intermediate", "Advanced", "Mixed"])

	st.subheader("3. Learners Information for Generator")
	prior_knowledge = st.text_area("Prior Knowledge")
	learners_info = st.text_input("Describe the learners for this lesson")
	success_criteria = st.text_input("What are the success criteria that can inform me that my students are learning?")
	st.subheader("4. Skills Application")
	kat_options = ["Support Assessment for Learning", "Foster Conceptual Change", "Provide Differentiation", "Facilitate Learning Together", "Develop Metacognition", "Enable Personalisation", "Scaffold the learning"]
	kat =st.multiselect("Which Key Application of Technology (KAT) is your lesson focused on?", kat_options)
	cc_21 = st.text_input("What are the 21CC (including New Media Literacies) that are important for my students to develop? ")
	st.subheader("5. Pedagogy")
	pedagogy = [" Blended Learning", "Concrete-Pictorial-Abstract",
				"Flipped Learning", "Others"]
	# Create the multiselect component
	selected_options = st.multiselect(
		"What teaching pedagogy will you use for your lesson ?", pedagogy)
	other_option = ''  # Initialize the variable
	# Others probably should be a custom component - Kahhow to refactor down the line
	if "Others" in selected_options:
		other_option = st.text_input("Please specify the 'Other' option:")
	if other_option and "Others" in selected_options:  # Ensure "Others" exists before removing
		selected_options.remove("Others")
		selected_options.append(other_option)

	vectorstore_selection_interface(st.session_state.user['id'])

	build = sac.buttons([
				dict(label='Generate', icon='check-circle-fill', color = 'green'),
				dict(label='Cancel', icon='x-circle-fill', color='red'),
			], label=None, index=1, format_func='title', align='center', position='top', size='default', direction='horizontal', shape='round', type='default', compact=False)

	if build != 'Cancel':
		lesson_prompt = f"""You must act as an expert teacher teaching in Singapore. I will provide you with details about my lesson, and it will be your job to think deeply and write a detailed lesson plan. I want you to design a lesson where students make sense of information and knowledge to achieve deep understanding through interacting with content, their peers or teachers and reflecting on their learning. The lesson plan should be simple yet detailed enough for any teacher to understand and carry out the lesson. At the top of the lesson plan, display the following information:
							Subject: {subject}
							Topic: {topic}
							Grade Level: {level}
							Duration: {total_duration} minutes spread across {lessons} of lessons
							Skill Level: {skill_level}
							Success Crtieria: {success_criteria}
							Key Application of Technology (KAT): {kat}
							2st Century Competencies (21CC) (New Media Literacies): {cc_21}
							Description of Learners: {learners_info}
							Student's prior knowledge: {prior_knowledge}
							Incorporate the following lesson elements: {pedagogy}."""
		st.success("Your lesson generation information has been submitted!")
		return lesson_prompt

	return False


def lesson_commentator():
	st.subheader("1. Basic Lesson Information for Feedback")
	subject = st.selectbox("Choose a Subject", SUBJECTS_SINGAPORE)
	level = st.selectbox("Choose a level", EDUCATION_LEVELS)
	duration = st.text_input("Duration (in minutes)")

	st.subheader("2. Lesson Details for Feedback")
	topic = st.text_area(
		"Topic", help="Describe the specific topic or theme for the lesson")
	skill_level = st.selectbox("Ability or Skill Level", [
		"Beginner", "Intermediate", "Advanced", "Mixed"])

	st.subheader("3. Lesson Plan upload or key in manually")
	lesson_plan_content = upload_lesson_plan()
	lesson_plan = st.text_area(
		"Please provide your lesson plan either upload or type into this text box, including details such as learning objectives, activities, assessment tasks, and any use of educational technology tools.", height=500, value=lesson_plan_content)

	st.subheader("4. Specific questions that I would like feedback on")
	feedback = st.text_area(
		"Include specific information from your lesson plan that you want feedback on.")

	st.subheader("5. Learners Profile")
	learners_info = st.text_input("Describe the learners for this lesson ")

	vectorstore_selection_interface(st.session_state.user['id'])

	build = sac.buttons([
				dict(label='Feedback', icon='check-circle-fill', color = 'green'),
				dict(label='Cancel', icon='x-circle-fill', color='red'),
			], label=None, index=1, format_func='title', align='center', position='top', size='default', direction='horizontal', shape='round', type='default', compact=False)

	if build != 'Cancel':
		feedback_template = f"""Imagine you are an experienced teacher. I'd like feedback on the lesson I've uploaded:
			Subject: {subject}
			Topic: {topic}
			Level: {level}
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
	openai.api_key = return_api_key()
	os.environ["OPENAI_API_KEY"] = return_api_key()
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


def lesson_bot(prompt, prompt_template, bot_name):
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
				reference_prompt = ""
			full_response = ""
			for response in template_prompt(prompt, reference_prompt + prompt_template):
				full_response += response.choices[0].delta.get("content", "")
				message_placeholder.markdown(full_response + "▌")
				if st.session_state.rating == True:
					feedback_value = rating_component()
				else:
					feedback_value = 0
			message_placeholder.markdown(full_response)
			st.session_state.msg.append({"role": "assistant", "content": full_response})
			st.session_state["memory"].save_context({"input": prompt},{"output": full_response})
			# This is to send the lesson_plan to the lesson design map
			st.session_state.lesson_plan  = full_response
			 # Insert data into the table
			now = datetime.now() # Using ISO format for date
			num_tokens = len(full_response + prompt)*1.3
			#st.write(num_tokens)
			insert_into_data_table(now.strftime("%d/%m/%Y %H:%M:%S"),  full_response, prompt, num_tokens, bot_name, feedback_value)
	except Exception as e:
		st.error(e)






