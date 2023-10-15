import streamlit as st
from st_audiorec import st_audiorec
import openai
import whisper
import tempfile
from authenticate import return_api_key
import io
import os
# Create or check for the 'database' directory in the current working directory
cwd = os.getcwd()
WORKING_DIRECTORY = os.path.join(cwd, "database")

if not os.path.exists(WORKING_DIRECTORY):
	os.makedirs(WORKING_DIRECTORY)

if st.secrets["sql_ext_path"] == "None":
	WORKING_DATABASE= os.path.join(WORKING_DIRECTORY , st.secrets["default_db"])
else:
	WORKING_DATABASE= st.secrets["sql_ext_path"]

if "svg_height" not in st.session_state:
	st.session_state["svg_height"] = 200

if "previous_mermaid" not in st.session_state:
	st.session_state["previous_mermaid"] = ""



def audio_feedback_bot(prompt, feedback):
	openai.api_key = return_api_key()
	os.environ["OPENAI_API_KEY"] = return_api_key()
	response = openai.ChatCompletion.create(
		model=st.session_state.openai_model,
		messages=[
			{"role": "system", "content": feedback},
			{"role": "assistant", "content": st.session_state.oral_rubrics},
			{"role": "user", "content": prompt},
		],
		temperature=st.session_state.temp, #settings option
		presence_penalty=st.session_state.presence_penalty, #settings option
		frequency_penalty=st.session_state.frequency_penalty, #settings option
		stream=True #settings option
	)
	return response         

def record_myself():
	# Create a button to start recording
	#if st.button("Record"):
	wav_audio_data = st_audiorec()
	#with st.status("Transcribing..."):
	if st.button("Transcribe (Maximum: 30 Seconds)") and wav_audio_data is not None:
		memory_file = io.BytesIO(wav_audio_data)
		memory_file.name = "test.wav"
	
		with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:  # change delete to False
			tmpfile.write(wav_audio_data)
		
		with st.spinner("Transcribing..."):
			model = whisper.load_model("base")
			audio = whisper.load_audio(tmpfile.name)
			audio = whisper.pad_or_trim(audio)
			mel = whisper.log_mel_spectrogram(audio).to(model.device)
			_, probs = model.detect_language(mel)
			st.write(f"Detected language: {max(probs, key=probs.get)}")
			options = whisper.DecodingOptions(fp16 = False)
			result = whisper.decode(model, mel, options)
			os.remove(tmpfile.name)  # Delete the temporary file manually after processing
			return result.text


def assessment_prompt(transcript, assessment_type, subject, topic, language):
	
	prompt = f"Find relevant sources for {subject} and {topic}."
	if st.session_state.vs:
		docs = st.session_state.vs.similarity_search(prompt)
		ans = docs[0].page_content
		source = docs[0].metadata.get('source', None)

		search_results = f"""{ans} \n\n Source: ({source})"""
	# Generate GPT response and feedback based on prompt and assessment type
	if assessment_type == "Oral Assessment":
		feedback = f"Provide feedback as a mentor based on the subject {subject} and topic {topic} in {language} on sentence structure and phrasing to help the user sound more proper. You may refer to this {search_results} for reference."
	elif assessment_type == "Content Assessment":
		feedback = f"Provide feedback based as a mentor on the subject {subject} and topic {topic} in {language} on the accuracy and completeness of the content explanation, and correct any errors or misconceptions.You may refer to this {search_results} for reference."
	
	message_placeholder = st.empty()
	full_response = ""
	for response in audio_feedback_bot(transcript, feedback + st.session_state.oral_rubrics):
		full_response += response.choices[0].delta.get("content", "")
		message_placeholder.markdown(full_response + "▌")
	message_placeholder.markdown(full_response)
	st.session_state.msg.append({"role": "assistant", "content": full_response})