# File: utils/chain_processor.py

import streamlit as st
from typing import List, Dict, Any, Union
from utils.my_langchain_tools import *
#from utils.message_handler import store_ai_message

def process_chain_response(query: str, tool: str, tool_call_id: str, prompt: str) -> None:
    """
    Process the response from the LangChain generation process and handle
    different tool executions appropriately.
    
    Args:
        response (List[Dict[str, Any]]): The response from generate_query_chain
        prompt (str): The original user prompt
    """
    #print ("I am in process_chain_response, response", response)
    # if not isinstance(response, list) or len(response) == 0:
    #     st.error("Invalid response from chain. Please try again.")
    #     return
    
    # tool_call = response[0]
    
    # # Store tool information in session state
    # st.session_state.tool_name = tool_call["name"]


    # setup_confirmation_state(tool_call, prompt)
    
    st.session_state.awaiting_confirmation = True
    st.session_state.current_query = query
    st.session_state.tool_name = tool
    st.session_state.current_chain_input = prompt
    st.session_state.tool_call_id = tool_call_id


