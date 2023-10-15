#No need database
import streamlit as st
import configparser
import os
import ast
config = configparser.ConfigParser()
config.read('config.ini')
NEW_PLAN  = config['constants']['NEW_PLAN']
FEEDBACK_PLAN = config['constants']['FEEDBACK_PLAN']
PERSONAL_PROMPT = config['constants']['PERSONAL_PROMPT']
DEFAULT_TEXT = config['constants']['DEFAULT_TEXT']
SUBJECTS_LIST = config.get('menu_lists','SUBJECTS_SINGAPORE')
SUBJECTS_SINGAPORE = ast.literal_eval(SUBJECTS_LIST )
GENERATE = "Lesson Generator"
FEEDBACK = "Lesson Feedback"




# Create or check for the 'database' directory in the current working directory
cwd = os.getcwd()
WORKING_DIRECTORY = os.path.join(cwd, "database")

if not os.path.exists(WORKING_DIRECTORY):
	os.makedirs(WORKING_DIRECTORY)

if st.secrets["sql_ext_path"] == "None":
	WORKING_DATABASE= os.path.join(WORKING_DIRECTORY , st.secrets["default_db"])
else:
	WORKING_DATABASE= st.secrets["sql_ext_path"]

def science_feedback():
	placeholder3 = st.empty()
	with placeholder3:
		with st.form("Metacognitive Feedback"):
			#st.subheader("Metacognitive Feedback")
			txt = st.text_area('Science text for analysis')
			submitted = st.form_submit_button("Submit Science text for feedback")
			if submitted:
				return txt


def reflective_peer():
	placeholder3 = st.empty()
	with placeholder3:
		with st.form("Reflective Peer"):
			#st.subheader("Reflective Peer")
			txt = st.text_area('Reflection Text')
			submitted = st.form_submit_button("Submit Reflection Text")
			if submitted:
				return txt