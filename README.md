> [!WARNING]  
> We are in the process of a major cleanup. Feel free to test as it is but expect changes/ post cleanup! <:

# AI Starter Kit

Enabling teachers to experiment with LLM/ Generative AI 

## Key Features:

1 **Text GenAI**:
- a) **Chat Assistant** (Visibility into backend)
- b) **Lesson Plan Generator**/ Collaborator (Scaffolding to create lesson plans)
- c) **[Remarks Co-Pilot](https://remarkscopilot.vercel.app/)** (Draft student remarks); 
- d) **Semantic search** on uploaded documents via [LanceDB](https://lancedb.com/)

2 **Voice GenAI**:
- a) **Oral coach** (Personalized feedback based on audio input)
- b) **Transcription** (Speech-to-text)

3 [WIP] **Image GenAI**
- a) **Create comic strips** (Creating reasonably consistent images across panels for composition writing)
- b) **Historic stylistic art reimagination** (Superimposing art styles/ palettes over uploaded images)

---

You can fork it at streamlit community cloud for immediate use. Please configure the env variables accordingly:

> [!IMPORTANT]  
> The following env variables are required for setup. You can add this to the `secrets.toml` file in your streamlit deployment

```

openai_key = "YOUR_OPEN_API_KEY"
default_db = "chergpt.db"
default_temp = 0.0
default_frequency_penalty = 0.0
default_presence_penalty = 0.0
default_k_memory = 4
default_model = "gpt-4-1106-preview"
default_password = "default_password"
student_password = "studentp@sswrd"
teacher_password = "teacherp@sswrd"
super_admin_password = "pass1234"
super_admin = "super_admin"
default_title = "GenAI Workshop Framework V2"
sql_ext_path = "None"
```

*Note, While GPT-4 is the default model, you can also change models by modifying this setting:<br>
`default_model = gpt-3.5-turbo`
<br><br>

## Setting up local dev env

To run this locally, first clone it to your local computer via Git. See [here](https://teachertech.beehiiv.com/p/git-for-beginners) for a crash course to git.
<br><br>
Prior to running locally, you will need to install required dependencies via this command
`pip install -r requirements.txt`

To run this locally
`streamlit run main.py`
<br><br>
**Questions?** Ask them on [WhatsApp](https://chat.whatsapp.com/LTNrg30pSil6vuq4zpnhc2) | [Discord](https://discord.gg/dYKVqzfdNH)
