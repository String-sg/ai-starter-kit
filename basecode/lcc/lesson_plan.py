import streamlit as st
import streamlit_antd_components as sac
import configparser
import ast
import os
from langchain.memory import ConversationBufferWindowMemory
from ..users_module import vectorstore_selection_interface

import openai
from ..authenticate import return_api_key
from ..main_bot import insert_into_data_table

from datetime import datetime
from Markdown2docx import Markdown2docx

config = configparser.ConfigParser()
config.read("config.ini")

SUBJECTS_LIST = config.get("menu_lists", "SUBJECTS_SINGAPORE")
SUBJECTS_SINGAPORE = ast.literal_eval(SUBJECTS_LIST)
PRI_LEVELS = [f"Primary {i}" for i in range(1, 7)]
SEC_LEVELS = [f"Secondary {i}" for i in range(1, 6)]
JC_LEVELS = [f"Junior College {i}" for i in range(1, 4)]
EDUCATION_LEVELS = PRI_LEVELS + SEC_LEVELS + JC_LEVELS
LESSON_COLLAB = config["constants"]["LESSON_COLLAB"]


def commentator_rating():
    rating_value = sac.rate(
        label="Lesson Commentator Ratings:",
        position="left",
        clear=True,
        value=2.5,
        align="left",
        size=15,
        color="#25C3B0",
        half=True,
        key=1,
    )
    return rating_value


def generator_rating():
    rating_value = sac.rate(
        label="Lesson Generator Ratings:",
        position="left",
        clear=True,
        value=2.5,
        align="left",
        size=15,
        color="#25C3B0",
        half=True,
        key=2,
    )
    return rating_value


def lesson_bot(prompt, prompt_template, bot_name):
    try:
        if prompt:
            # st.write("I am inside", st.session_state.lesson_col_prompt)
            if "memory" not in st.session_state:
                st.session_state.memory = ConversationBufferWindowMemory(k=5)
            st.session_state.msg.append({"role": "user", "content": prompt})
            message_placeholder = st.empty()
            # check if there is any knowledge base
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
            if bot_name == LESSON_COLLAB:
                feedback_value = generator_rating()
            else:
                feedback_value = commentator_rating()
            message_placeholder.markdown(full_response)
            st.session_state.msg.append({"role": "assistant", "content": full_response})
            st.session_state["memory"].save_context(
                {"input": prompt}, {"output": full_response}
            )
            # This is to send the lesson_plan to the lesson design map
            st.session_state.lesson_plan = full_response
            # Insert data into the table
            now = datetime.now()  # Using ISO format for date
            num_tokens = len(full_response + prompt) * 1.3
            # st.write(num_tokens)
            insert_into_data_table(
                now.strftime("%d/%m/%Y %H:%M:%S"),
                full_response,
                prompt,
                num_tokens,
                bot_name,
                feedback_value,
            )
            st.session_state.data_doc = (
                st.session_state.data_doc + "\n\n" + full_response
            )
            md_filename = "lp" + st.session_state.user["username"] + ".md"
            md_filepath = os.path.join("lesson_plan", md_filename)
            if not os.path.exists("lesson_plan"):
                os.makedirs("lesson_plan")
            with open(md_filepath, "w", encoding="utf-8") as file:
                file.write(full_response)
            # Convert the markdown file to a docx
            base_filepath = os.path.join(
                "lesson_plan", "lp" + st.session_state.user["username"]
            )
            project = Markdown2docx(base_filepath)
            project.eat_soup()
            project.save()  # Assuming it saves the file with the same name but a .docx extension
            st.session_state.generated_flag = True

    except Exception as e:
        st.error(e)


def template_prompt(prompt, prompt_template):
    openai.api_key = return_api_key()
    os.environ["OPENAI_API_KEY"] = return_api_key()
    response = openai.ChatCompletion.create(
        model=st.session_state.openai_model,
        messages=[
            {"role": "system", "content": prompt_template},
            {"role": "user", "content": prompt},
        ],
        temperature=st.session_state.temp,  # settings option
        stream=True,  # settings option
    )
    return response


def lesson_collaborator():
    st.subheader("1. Basic Lesson Information for Generator")
    subject = st.selectbox("Choose a Subject", SUBJECTS_SINGAPORE)
    level = st.selectbox("Grade Level", EDUCATION_LEVELS)
    # lessons = st.number_input(
    # 	"Number of lessons/ periods", min_value=1.0, step=0.5, format='%.2f')
    # duration = st.number_input(
    # 	"How long is a period/ lesson (in minutes)", min_value=30, step=5, format='%i')
    # total_duration = lessons * duration
    duration = st.text_input(
        "Duration (in minutes)",
        help="Estimated duration of one lesson or over a few lessons",
    )
    st.subheader("2. Lesson Details for Generator")
    topic = st.text_area(
        "Topic", help="Describe the specific topic or theme for the lesson"
    )
    skill_level = st.text_input(
        "Readiness Level", help="Beginner, Intermediate, Advanced ..."
    )
    st.subheader("3. Learners Information for Generator")
    prior_knowledge = st.text_area("Prior Knowledge")
    learners_info = st.text_input("Describe the learners for this lesson")
    st.subheader("4. Skills Application")
    kat_options = [
        "Support Assessment for Learning",
        "Foster Conceptual Change",
        "Provide Differentiation",
        "Facilitate Learning Together",
        "Develop Metacognition",
        "Enable Personalisation",
        "Scaffold the learning",
    ]
    kat = st.multiselect(
        "Which Key Application of Technology (KAT) is your lesson focused on?",
        kat_options,
    )
    cc_21 = ""
    incorporate_elements = ""
    if st.checkbox(
        "I would like to incorporate 21CC (including New Media Literacies) in my lesson"
    ):
        cc_21 = st.text_input(
            "What are the 21CC (including New Media Literacies) that are important for my students to develop? "
        )
    if st.checkbox(
        "I would like to incorporate certain lesson elements in my lesson plan"
    ):
        st.subheader("5. Lesson Structure")
        incorporate_elements = st.text_area(
            "Incoporate lesson elements (e.g. lesson should be fun and include pair work)",
            help="Describe lesson elements that you would like to have",
        )
    # pedagogy = [" Blended Learning", "Concrete-Pictorial-Abstract",
    # 			"Flipped Learning", "Others"]
    # # Create the multiselect component
    # selected_options = st.multiselect(
    # 	"What teaching pedagogy will you use for your lesson ?", pedagogy)
    # other_option = ''  # Initialize the variable
    # Others probably should be a custom component - Kahhow to refactor down the line
    # if "Others" in selected_options:
    # 	other_option = st.text_input("Please specify the 'Other' option:")
    # if other_option and "Others" in selected_options:  # Ensure "Others" exists before removing
    # 	selected_options.remove("Others")
    # 	selected_options.append(other_option)
    st.write(st.session_state.lesson_col_option)
    vectorstore_selection_interface(st.session_state.user["id"])
    # if st.button("Submit for Feedback", key=1):
    st.session_state.lesson_col_option = sac.buttons(
        [
            sac.ButtonsItem(
                label="Generate",
                icon="check-circle-fill",
                color="green",
                disabled=st.session_state.generated_flag,
            ),
            sac.ButtonsItem(
                label=st.session_state.button_text, icon="x-circle-fill", color="red"
            ),
        ],
        label=None,
        index=1,
        format_func="title",
        align="center",
        position="top",
        size="default",
        direction="horizontal",
        shape="round",
        type="default",
        compact=False,
    )

    if st.session_state.lesson_col_option == "Generate":
        lesson_prompt = f"""Help me design a lesson on this information
							Subject: {subject}
							Topic: {topic}
							Grade Level: {level}
							Duration: {duration} minutes
							Readiness Level: {skill_level}
							Description of Learners: {learners_info}
							Student's prior knowledge: {prior_knowledge}
							Key Application of Technology (KAT): {kat}"""
        if cc_21 != "":
            lesson_prompt + f"""21CC (including New Media Literacies): {cc_21}"""
        if incorporate_elements != "":
            (
                lesson_prompt
                + f"""Incorporate the following lesson elements (if any): {incorporate_elements}"""
            )

        st.success("Your lesson generation information has been submitted!")

        return lesson_prompt
    elif (
        st.session_state.lesson_col_option == "Cancel"
        or st.session_state.lesson_col_option == "Reset"
    ):
        st.session_state.generated_flag = False
        st.session_state.button_text = "Cancel"
        return False


def lesson_design_options():
    docx_name = "lp" + st.session_state.user["username"] + ".docx"
    docx_path = os.path.join("lesson_plan", docx_name)

    if os.path.exists(docx_path):
        # Provide the docx for download via Streamlit
        with open(docx_path, "rb") as docx_file:
            docx_bytes = docx_file.read()
            st.success("File is ready for downloading")
            st.download_button(
                label="Download document as DOCX",
                data=docx_bytes,
                file_name=docx_name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        os.remove(docx_path)
        st.session_state.button_text = "Reset"
    else:
        st.warning("There is no lesson plan available for download.")
