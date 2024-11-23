# File: utils/message_handler.py

from langchain.schema import AIMessage
from typing import Union, Dict, Any
import streamlit as st

def store_ai_message(query_response: Union[str, AIMessage, Any], executed_query: str) -> None:
    """
    Store an AI message in the session state with proper formatting and tool information.
    
    Args:
        query_response: The response from the query execution, can be:
            - str: A simple string response
            - AIMessage: A pre-formatted AI message
            - Any: Any other type of response that will be converted to string
        executed_query: The actual query that was executed
    """
    # Create tool call information
    tool_call = {
        "name": st.session_state.tool_name,
        "args": create_tool_args(executed_query),
        "id": generate_tool_call_id()
    }

    # Handle different types of responses
    if isinstance(query_response, str):
        ai_message = AIMessage(
            content=query_response,
            tool_calls=[tool_call]
        )
    elif isinstance(query_response, AIMessage):
        # If it's already an AIMessage, ensure it has tool calls
        if not hasattr(query_response, 'tool_calls'):
            query_response.tool_calls = [tool_call]
        ai_message = query_response
    else:
        # For any other type of response, convert to string
        ai_message = AIMessage(
            content=str(query_response),
            tool_calls=[tool_call]
        )

    # Store the message in session state
    st.session_state.messages.append(ai_message)

def create_tool_args(executed_query: str) -> Dict[str, str]:
    """
    Create the arguments dictionary for a tool call.
    
    Args:
        executed_query: The query that was executed
        
    Returns:
        Dict containing the query information and context
    """
    return {
        "query": st.session_state.current_query,
        "executed_query": executed_query,
        "my_question": st.session_state.current_chain_input,
        "original_query": st.session_state.current_chain_input
    }

def generate_tool_call_id() -> str:
    """
    Generate a unique ID for a tool call.
    
    Returns:
        str: A unique identifier for the tool call
    """
    # Get the current number of messages
    message_count = len(st.session_state.messages)
    return f"call_{message_count + 1}"

# def format_query_response(response: Any, tool_name: str) -> str:
#     """
#     Format a query response based on the tool type.
    
#     Args:
#         response: The raw response from the tool
#         tool_name: The name of the tool that generated the response
        
#     Returns:
#         str: Formatted response string
#     """
#     if tool_name == "SQL_QueryTool":
#         return format_sql_response(response)
#     elif tool_name == "Graph_QueryTool":
#         return format_graph_response(response)
#     elif tool_name == "Vector_QueryTool":
#         return format_vector_response(response)
#     elif tool_name == "Fulltext_QueryTool":
#         return format_fulltext_response(response)
#     else:
#         return str(response)

# def format_sql_response(response: Any) -> str:
#     """Format SQL query results"""
#     if not response:
#         return "No results found."
    
#     if isinstance(response, list):
#         # Convert list of results to markdown table
#         if not response[0]:
#             return "No results found."
            
#         headers = response[0].keys()
#         table = "| " + " | ".join(headers) + " |\n"
#         table += "| " + " | ".join(["---" for _ in headers]) + " |\n"
        
#         for row in response:
#             table += "| " + " | ".join(str(row[col]) for col in headers) + " |\n"
#         return table
    
#     return str(response)

# def format_graph_response(response: Any) -> str:
#     """Format graph query results"""
#     if not response:
#         return "No graph relationships found."
    
#     if isinstance(response, list):
#         # Format graph relationships
#         formatted = "Found the following relationships:\n\n"
#         for rel in response:
#             formatted += f"- {rel['start']} → {rel['type']} → {rel['end']}\n"
#         return formatted
    
#     return str(response)

# def format_vector_response(response: Any) -> str:
#     """Format vector query results"""
#     if not response:
#         return "No similar items found."
    
#     if isinstance(response, list):
#         # Format similarity results
#         formatted = "Found similar items (with similarity scores):\n\n"
#         for item in response:
#             score = item.get('similarity', 0)
#             formatted += f"- {item['content']} (similarity: {score:.2f})\n"
#         return formatted
    
#     return str(response)

# def format_fulltext_response(response: Any) -> str:
#     """Format fulltext search results"""
#     if not response:
#         return "No matching documents found."
    
#     if isinstance(response, list):
#         # Format text search results
#         formatted = "Found the following matches:\n\n"
#         for doc in response:
#             score = doc.get('score', 0)
#             formatted += f"- [{score:.2f}] {doc['content']}\n"
#         return formatted
    
#     return str(response)

# Example usage:
"""
def process_confirmed_query(query: str) -> None:
    with st.spinner("Processing response..."):
        # Execute the query
        query_response = langchain_tools.execute_query(
            st.session_state.current_chain_input, 
            query
        )
        
        # Store the response
        store_ai_message(query_response, query)
        
        # Clear states
        clear_confirmation_state()
"""