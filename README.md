# CherGPT Starter Kit
Enabling teachers to experiment with LLM/ Generative AI in a Q&A chatbot
<img width="689" alt="chergpt-starter-kit" src="https://github.com/String-sg/chergpt-starter-kit/assets/44336310/3d8ce9e7-acf8-44e9-b28a-19156cc6dbe8">

This kit will automatically:
 - Create a login page and all the features of a full stack application using ant_components 
 - Create an administrator account, password is pass1234 in a SQL Database
 - Generate 5 teachers account and 40 students

## Key Features:
 -  Upload documents and build a knowledge base using the OpenAI embeddings
 -  Enable semantic search on uploaded documents via [LanceDB](https://lancedb.com/)
 -  Preset custom prompt engineering to guide interactions for Q&A


## User-role specific features
> [!NOTE]  
> This app comes with the following user roles: admins, teachers, and students
 - **Admins** can reset passwords of students and teachers
 - **Teachers** can add and remove documents 
 - **Teachers** can build and remove knowledge base (VectorStores)
 - **Admins** can edit knowledge base and documents
 - **Admins** share documents among the 5 teachers
 - **Students** can load their own knowledge base for their own chatbot

You can fork it at streamlit community cloud, it can be used straight away, just add the following to your streamlit secrets

> [!IMPORTANT]  
> The following env variables are required for setup. You can add this to the secrets.toml file in your streamlit deployment 
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
# etd_itd_prototype
# lesson_support
