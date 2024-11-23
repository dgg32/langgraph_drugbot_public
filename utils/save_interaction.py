import json
import os

def save_interaction(question: str, query: str, filename: str = "interaction.jsonl"):
    """
    Save the interaction to a JSONL file.
    
    Args:
        question (str): The user's question
        query (str): The generated and confirmed query
        filename (str): The name of the JSONL file to save to
    """
    interaction = {
        "input": question,
        "query": query
    }

    with open(filename, "a", encoding='utf-8') as myfile:
        myfile.write(json.dumps({"input": question, "query": query}) + "\n")