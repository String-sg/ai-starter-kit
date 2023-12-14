import streamlit as st
import openai
from basecode.authenticate import return_api_key
from langchain.tools import YouTubeSearchTool
from basecode.kb_module import display_vectorstores
from basecode.users_module import vectorstore_selection_interface
import os

from langchain.agents import ConversationalChatAgent, AgentExecutor
from langchain.callbacks import StreamlitCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain.tools import DuckDuckGoSearchRun
from langchain.tools import WikipediaQueryRun
from langchain.utilities import WikipediaAPIWrapper
from langchain.agents import tool
import json


# smart agents accessing the internet for free
# https://github.com/langchain-ai/streamlit-agent/blob/main/streamlit_agent/search_and_chat.py
@tool("Document search")
def document_search(query: str) -> str:
	# this is the prompt to the tool itself
	"Use this function first to search for documents pertaining to the query before going into the internet"
	docs = st.session_state.vs.similarity_search(query)
	docs = docs[0].page_content
	json_string = json.dumps(docs, ensure_ascii=False, indent=4)
	return json_string

@tool("Wiki search")
def wiki_search(query: str) -> str:
	"Use this function to search for documents in Wikipedia"
	wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
	results = wikipedia.run(query)
	return results

@tool("Image Generator")
def dalle_image_generator(query):
	"Use this function to generate images from text"
	response = openai.Image.create(
	prompt=query,                  
	n=1,
	size="1024x1024"
	)
	image_url = response['data'][0]['url']
	return image_url


#customise more tools for your agent

def agent_bot():
	st.subheader("Smart Bot with Tools")
	openai.api_key = return_api_key()
	os.environ["OPENAI_API_KEY"] = return_api_key()
	msgs = StreamlitChatMessageHistory()
	memory = ConversationBufferMemory(
		chat_memory=msgs,
		return_messages=True,
		memory_key="chat_history",
		output_key="output",
	)
	if len(msgs.messages) == 0 or st.sidebar.button("Reset chat history"):
		msgs.clear()
		msgs.add_ai_message("How can I help you?")
		st.session_state.steps = {}

	avatars = {"human": "user", "ai": "assistant"}
	for idx, msg in enumerate(msgs.messages):
		with st.chat_message(avatars[msg.type]):
			# Render intermediate steps if any were saved
			for step in st.session_state.steps.get(str(idx), []):
				if step[0].tool == "_Exception":
					continue
				with st.status(
					f"**{step[0].tool}**: {step[0].tool_input}", state="complete"
				):
					st.write(step[0].log)
					st.write(step[1])
			st.write(msg.content)

	if prompt := st.chat_input(placeholder="Enter a query on the Internet"):
		st.chat_message("user").write(prompt)

		llm = ChatOpenAI(
			model_name=st.secrets['default_model'], openai_api_key=return_api_key(), streaming=True
		)
		tools = st.session_state.tools
		chat_agent = ConversationalChatAgent.from_llm_and_tools(llm=llm, tools=tools)
		executor = AgentExecutor.from_agent_and_tools(
			agent=chat_agent,
			tools=tools,
			memory=memory,
			return_intermediate_steps=True,
			handle_parsing_errors=True,
			
		)
		with st.chat_message("assistant"):
			st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
			response = executor(prompt, callbacks=[st_cb])
			st.write(response["output"])
			st.session_state.steps[str(len(msgs.messages) - 1)] = response[
				"intermediate_steps"
			]
			
#create more tools for your agent here
def agent_management():
	display_vectorstores()
	vectorstore_selection_interface(st.session_state.user['id'])

	if st.session_state.vs:
		all_tools = {
			"Document Search": document_search,
			"Wiki Search": wiki_search,
			"Internet Search": DuckDuckGoSearchRun(name="Internet Search"),
			"YouTube Search": YouTubeSearchTool(),
		
			}
	else:
		all_tools = {
			"Wiki Search": wiki_search,
			"Internet Search": DuckDuckGoSearchRun(name="Internet Search"),
			"YouTube Search": YouTubeSearchTool(),
		
		}
	
	# Create a Streamlit multiselect widget
	st.write("Select Tools (Note: Image Generator tool will set to a memoryless agent)")
	selected_tool_names = st.multiselect(
		"Select up to 3 tools:", list(all_tools.keys()), default=list(all_tools.keys())[:3]
	)
	if len(selected_tool_names) == 0:
		st.write("Please select at least one tool.")	
	else:
		# Map selected tool names to their respective functions
		tools = [all_tools[name] for name in selected_tool_names]
		st.session_state.tools = tools
		#st.write("Selected Tools:", st.session_state.tools)
		