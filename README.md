# CherGPT Starter Kit
Enabling teachers to experiment with LLM/ Generative AI in a Q&A chatbot
<img width="689" alt="chergpt-starter-kit" src="https://github.com/String-sg/chergpt-starter-kit/assets/44336310/3d8ce9e7-acf8-44e9-b28a-19156cc6dbe8">

The kit will 
 - Create a login page and all the features of a full stack application using ant_components 
 - Create an administrator account, password is pass1234 in a SQL Database
 - Automatically generate 5 teachers account and 40 students

Key Features:
 -  teachers can upload documents and build a knowledge base using the OpenAI embeddings
 -  use LanceDB to do a semantic search on uploaded documents
 -  use the chatbot to query over the results
 -  administrator can create custom prompt engineering for the non Q&A bot

Other features
 - admin can reset passwords of students and teachers
 - teachers can add and remove documents 
 - teachers can build and remove knowledge base (VectorStores)
 - administrator can edit knowledge base and documents
 - share documents among the 5 teachers
 - students can load their own knowledge base for their own chatbot

You can fork it at streamlit community cloud, it can be used straight away, just add the following to your streamlit secrets

> [!NOTE]
> The following env variables are required for setup. You can add this to the secrets.toml file in your streamlit deployment 
```
openai_key = "XXXXXXX_YOUR_API_KEY"
default_db = "chergpt.db"
default_temp = 0
default_model = "gpt-4"
```
