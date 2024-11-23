
  
  

# Introduction

  

This repository contains code and data for my article "[From LangChain to LangGraph: Making the Multi-Model DrugBot Simple, Personal, and Teachable](https://dgg32.medium.com/from-langchain-to-langgraph-making-the-multi-model-drugbot-personal-and-teachable-9ef20055efb4)".



# Prerequisite

OpenAI API 

Python and its DuckDB API

Streamlit


# Run

1. Fill in the token in config.yaml for vector embedding and vector search

>  openai_token: [YOUR_OPENAI_TOKEN]
>  vector_embedding_model: [text-embedding-3-small]
>  drugdb_path: drug.db

2. Run streamlit run app.py to start the chatbot

3. Play with the chatbot

## Authors



*  **Sixing Huang** - *Concept and Coding*

  

  

## License

  

  

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
