import streamlit as st
from streamlit.components.v1 import html
import re
import openai
from openai import OpenAI


def mermaid(code: str) -> None:
    html(
        f"""
        <pre class="mermaid">
            {code}
        </pre>

        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true }});
        </script>
        """,
        height=st.session_state["svg_height"] + 50,
    )


def extract_mermaid_syntax(text):
    # st.text(text)
    pattern = r"```\s*mermaid\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    else:
        pattern = r"\*\(&\s*([\s\S]*?)\s*&\)\*"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
        else:
            return "Mermaid syntax not found in the provided text."


def output_mermaid_diagram(mermaid_code):
    """
    Outputs the mermaid diagram in a Streamlit app.

    Args:
        mermaid_code (str): Mermaid code to be rendered.
    """

    if mermaid_code:
        mermaid(mermaid_code)
    else:
        st.error("Please type in a new topic or change the words of your topic again")
        return False


def generate_mindmap(prompt):
    try:
        client = OpenAI(api_key=st.secrets["openai_key"])

        response = client.chat.completions.create(
            model=st.session_state.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=st.session_state.temp,  # settings option
            presence_penalty=st.session_state.presence_penalty,  # settings option
            frequency_penalty=st.session_state.frequency_penalty,  # settings option
        )

        if response["choices"][0]["message"]["content"] != None:
            msg = response["choices"][0]["message"]["content"]
            st.text(msg)

            extracted_code = extract_mermaid_syntax(msg)
            st.write(extracted_code)
            return extracted_code

    except openai.APIError as e:
        st.error(e)
        st.error("Please type in a new topic or change the words of your topic again")
        return False

    except Exception as e:
        st.error(e)
        st.error("Please type in a new topic or change the words of your topic again")
        return False
