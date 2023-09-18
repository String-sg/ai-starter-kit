import streamlit as st
import openai
import sqlite3
from datetime import datetime
from langchain.memory import ConversationSummaryBufferMemory
from langchain.memory import ConversationBufferWindowMemory
from langchain.chat_models import ChatOpenAI
import os

# Create or check for the 'database' directory in the current working directory
cwd = os.getcwd()
database_path = os.path.join(cwd, "database")

if not os.path.exists(database_path):
    os.makedirs(database_path)

# Set DB_NAME to be within the 'database' directory
DB_NAME = os.path.join(database_path, st.secrets["default_db"])

def insert_into_data_table(date, username, profile, chatbot, prompt, tokens):
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	cursor.execute('''
		INSERT INTO data_table (date, username, profile, chatbot_ans, user_prompt, tokens)
		VALUES (?, ?, ?, ?, ?, ?)
	''', (date, username, profile, chatbot, prompt, tokens))
	conn.commit()
	conn.close()


#below ------------------------------ QA  base bot , K=5 memory for short term memory---------------------------------------------
#using the query from lanceDB and vector store , combine with memory
def memory_buffer_qa_component(prompt):
	#st.write(type(st.session_state.vs))
	if st.session_state.vs:
		docs = st.session_state.vs.similarity_search(prompt)
		ans = docs[0].page_content
		source = docs[0].metadata
	if "memory" not in st.session_state:
		st.session_state.memory = ConversationBufferWindowMemory(k=5)
	data = st.session_state.memory.load_memory_variables({})
	#st.write(ans)
	prompt_template = st.session_state.prompt_template + f"""
						Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. 
						Search Result:
						{ans}
						{source}
						History of conversation:
						{data}
						You must quote the source of the Search Result if you are using the search result as part of the answer"""
	
	return prompt_template


#chat completion memory for streamlit using memory buffer
def chat_completion_qa_memory(prompt):
	prompt_template = memory_buffer_qa_component(prompt)
	response = openai.ChatCompletion.create(
		model=st.session_state.openai_model,
		messages=[
			{"role": "system", "content":prompt_template },
			{"role": "user", "content": prompt},
		],
		temperature=st.session_state.temp, #settings option
		stream=True #settings option
	)
	return response

#integration API call into streamlit chat components with memory and qa
def basebot_qa_memory():
	for message in st.session_state.msg:
		with st.chat_message(message["role"]):
			st.markdown(message["content"])
	try:
		if prompt := st.chat_input("What is up?"):
			st.session_state.msg.append({"role": "user", "content": prompt})
			with st.chat_message("user"):
				st.markdown(prompt)

			with st.chat_message("assistant"):
				message_placeholder = st.empty()
				full_response = ""
				for response in chat_completion_qa_memory(prompt):
					full_response += response.choices[0].delta.get("content", "")
					message_placeholder.markdown(full_response + "▌")
				message_placeholder.markdown(full_response)
			st.session_state.msg.append({"role": "assistant", "content": full_response})
			st.session_state["memory"].save_context({"input": prompt},{"output": full_response})
			 # Insert data into the table
			now = datetime.now() # Using ISO format for date
			num_tokens = len(full_response)*1.3
			#st.write(num_tokens)
			insert_into_data_table(now.strftime("%d/%m/%Y %H:%M:%S"), st.session_state.user["username"], st.session_state.user["profile"], full_response, prompt, num_tokens)
	except Exception as e:
		st.error(e)
#below ------------------------------ base bot , K=5 memory for short term memory---------------------------------------------
#faster and more precise but no summary
def memory_buffer_component(prompt):
	if "memory" not in st.session_state:
		st.session_state.memory = ConversationBufferWindowMemory(k=5)
	#st.write("Messages ", messages)
	data = st.session_state.memory.load_memory_variables({})
	#change the template here 
	prompt_template = st.session_state.prompt_profile["prompt_data"]+ f""" 
						History of conversation:
						{data}
						Last line:
						Human: {prompt}"""
	
	return prompt_template
#below ------------------------------ base bot , summary memory for long conversation---------------------------------------------
#summary of conversation , requires another LLM call for every input, useful for feedback and summarising what was spoken
def memory_summary_component(prompt): #currently not in use
	if "memory" not in st.session_state:
		llm = ChatOpenAI(model_name=st.session_state.openai_model,temperature=st.session_state.temp)
		st.session_state.memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=1000)
	messages = st.session_state["memory"].chat_memory.messages
	#st.write("Messages ", messages)
	previous_summary = ""
	data = st.session_state["memory"].predict_new_summary(messages, previous_summary)

	st.session_state.summary  = data
	prompt_template = st.session_state.prompt_template + f"""
						Summary of current conversation:
						{data}
						Last line:
						Human: {prompt}"""
	
	return prompt_template 

#chat completion memory for streamlit using memory buffer
def chat_completion_memory(prompt):
	prompt_template = memory_buffer_component(prompt)
	response = openai.ChatCompletion.create(
		model=st.session_state.openai_model,
		messages=[
			{"role": "system", "content":prompt_template },
			{"role": "user", "content": prompt},
		],
		temperature=st.session_state.temp, #settings option
		stream=True #settings option
	)
	return response

#integration API call into streamlit chat components with memory
def basebot_memory():
	for message in st.session_state.msg:
		with st.chat_message(message["role"]):
			st.markdown(message["content"])
	try:
		if prompt := st.chat_input("What is up?"):
			st.session_state.msg.append({"role": "user", "content": prompt})
			with st.chat_message("user"):
				st.markdown(prompt)

			with st.chat_message("assistant"):
				message_placeholder = st.empty()
				full_response = ""
				for response in chat_completion_memory(prompt):
					full_response += response.choices[0].delta.get("content", "")
					message_placeholder.markdown(full_response + "▌")
				message_placeholder.markdown(full_response)
			st.session_state.msg.append({"role": "assistant", "content": full_response})
			st.session_state["memory"].save_context({"input": prompt},{"output": full_response})
			 # Insert data into the table
			now = datetime.now() # Using ISO format for date
			num_tokens = len(full_response)*1.3
			#st.write(num_tokens)
			insert_into_data_table(now.strftime("%d/%m/%Y %H:%M:%S"), st.session_state.user["username"], st.session_state.user["profile"], full_response, prompt, num_tokens)
	except Exception as e:
		st.error(e)

#below ------------------------------ base bot , no memory ---------------------------------------------
#chat completion for streamlit function
def chat_completion(prompt):
	response = openai.ChatCompletion.create(
		model=st.session_state.openai_model,
		messages=[
			{"role": "system", "content": st.session_state.prompt_template},
			{"role": "user", "content": prompt},
		],
		temperature=st.session_state.temp, #settings option
		stream=True #settings option
	)
	return response

#integration API call into streamlit chat components
def basebot():
	for message in st.session_state.msg:
		with st.chat_message(message["role"]):
			st.markdown(message["content"])
	try:
		if prompt := st.chat_input("What is up?"):
			st.session_state.msg.append({"role": "user", "content": prompt})
			with st.chat_message("user"):
				st.markdown(prompt)

			with st.chat_message("assistant"):
				message_placeholder = st.empty()
				full_response = ""
				for response in chat_completion(prompt):
					full_response += response.choices[0].delta.get("content", "")
					message_placeholder.markdown(full_response + "▌")
				message_placeholder.markdown(full_response)
			st.session_state.msg.append({"role": "assistant", "content": full_response})
			

	except Exception as e:
		st.error(e)