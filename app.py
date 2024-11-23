# File: app.py

from config import init_session_state, add_button_styles
from ui.chat_display import display_chat_messages
from ui.query_confirmation import create_query_confirmation_ui
from langchain.schema import HumanMessage
import streamlit as st
from utils.my_langchain_tools import *
from utils.error_handler import handle_query_error, clear_error_state, clear_confirmation_state
from utils.message_handler import store_ai_message
from utils.chain_processor import process_chain_response
import my_db_specifics
from langchain_core.messages import ToolMessage, AIMessage
import graph_definition as gd


config = {"configurable": {"thread_id": "1", "user_id": "sixing"}}

# Example queries that can be used via buttons
EXAMPLE_QUERIES = []

def load_examples():
    for example_list in [
        (my_db_specifics.sql_examples),
        (my_db_specifics.graph_examples),
        (my_db_specifics.full_text_search_examples),
        (my_db_specifics.vector_search_examples)
    ]:
        for example in example_list:
            EXAMPLE_QUERIES.append(example)

    with open("interaction.jsonl", "r") as file:
        for line in file:
            example = json.loads(line)
            EXAMPLE_QUERIES.append(example)

load_examples()

def create_example_buttons():
    """Create buttons for example queries in a single column"""
    for idx, example in enumerate(EXAMPLE_QUERIES):
        if st.button(
            example["input"], 
            key=f"example_{idx}",
            use_container_width=True,
        ):
            handle_example_query(example)
            st.rerun()


def handle_example_query(example):
    """Handle when an example query button is clicked"""
    # Add the user's "question" to the chat
    st.session_state.messages.append(AIMessage(content=example["input"], additional_kwargs={"function": {"arguments": str({"question": example["input"], "top_k": 5})}}))
    st.session_state.messages.append(HumanMessage(content=example["input"]))
    
    # Set up the confirmation state as if the bot generated this query
    st.session_state.awaiting_confirmation = True
    st.session_state.current_query = example["query"]
    st.session_state.current_chain_input = example["input"]
    st.session_state.tool_name = example["tool_name"]


def process_confirmed_query(query):
    """Process a confirmed query and store the response"""
    with st.spinner("Processing confirmed query..."):
        #print ("I am in process_confirmed_query. curre_chain_input", st.session_state.current_chain_input)
        #print ("hello", query)

        #print ("in if prompt", app.get_state(config))

        tool_name = st.session_state.tool_name

        tool_message = [
            {   
                
                "name": tool_name, 
                "type": "user",
                "content": query
            }
        ]

        #print ("tool_message", tool_message)
        gd.app.update_state(config, {"messages": tool_message}, as_node="human_feedback")
        print ("I am in process_confirmed_query. curre_chain_input")
        print ("process_confirmed_query", gd.app.get_state(config))
        #app.stream(None, config, stream_mode="values")
        print ("run")
        events = list(gd.app.stream(None, config, stream_mode="values"))
        #print ("events", events)
        last_event = events[-1]
        #print (last_event)
        #print ("state", event)
        #print (event["messages"][-1].content)

        print ("----question-----")
        print (last_event["messages"][-1].additional_kwargs.get("question"))
        print ("----final_query-----")
        print (last_event["messages"][-1].additional_kwargs.get("query"))

        print ("----query_result-----")
        print (last_event["messages"][-1].additional_kwargs.get("execute_result"))

        print ("----answer-----")
        print (last_event["messages"][-1].content)

        store_ai_message(last_event["messages"][-1].content, last_event["messages"][-1].additional_kwargs.get("query"))
        
        clear_confirmation_state()

def handle_confirmation_result(confirmation_result):
    """Handle the result of query confirmation"""
    
    if confirmation_result == "waiting":
        return False
        
    if confirmation_result is not None:
        try:
            process_confirmed_query(confirmation_result)
            return True
        except Exception as e:
            handle_query_error(e)
            return True
    else:
        st.warning("Query rejected. Please try a different question.")
        clear_error_state()
        return True

def run_chatbot():
    """Main function to run the chatbot interface"""
    # Configure the sidebar
    with st.sidebar:
        st.markdown("### Example queries you can try:")
        create_example_buttons()
    
    # Main chat interface
    st.title("DrugBot 💊")
    
    # Initialize session state
    init_session_state()
    
    # Display chat messages in main area
    display_chat_messages()
    
    # Handle confirmation UI if needed
    if st.session_state.awaiting_confirmation:
        #print ("in awaiting_confirmation", app.get_state(config))
        confirmation_result = create_query_confirmation_ui()
        
        if handle_confirmation_result(confirmation_result):
            st.rerun()
    
    # Create columns for chat input and dropdown
    input_col, dropdown_col = st.columns([5, 1])
    
    with input_col:
        prompt = st.chat_input(
            "What would you like to know about the drugs database?",
            key="chat_input"
        )
    
    with dropdown_col:
        user_tool = st.selectbox(
            "",
            options=["Automatic", "SQL", "Graph", "Vector", "Fulltext", "Mimicking"],
            key="tool_selector",
            label_visibility="collapsed"
        )
    
    if prompt:
        input_message = HumanMessage(content=prompt, tool_choice=user_tool.lower())
        
        try:
            with st.spinner("Processing response..."):
                for event in gd.app.stream({"messages": [input_message]}, config, stream_mode="values"):
                    print ("len:", len(event["messages"]))
                
                #print ("in try if prompt", app.get_state(config).values["messages"])

                st.session_state.messages.append(HumanMessage(content=input_message.content))
                #st.session_state.tool_name = "clarifying"
                #print ("!!!!!!!!!!!!!!!!!!!!!!gd.app.get_state(config).values", gd.app.get_state(config).values)
                generated_message = gd.app.get_state(config).values["messages"][-1]
                #print ("!!!!!!!!!!!!!!!!!!!!!!generated_message", generated_message)
                #### AI needs to ask a clarifying question
                if isinstance(generated_message, AIMessage):
                    tool_name = "clarifying"
                    tool_call_id = "dummy_tool_id"
                    
                    print ("=================================================tool_name", tool_name, "tool_call_id", tool_call_id)
                    process_chain_response(generated_message.content, tool_name, tool_call_id, prompt)
                elif isinstance(generated_message, ToolMessage):
                    print ("============================ in prompt, toolmessage, generated_message",  generated_message)
                    generated_query = generated_message.content
                    #print ("generated_query\n", type(app.get_state(config).values["messages"][-1]), app.get_state(config).values["messages"][-1])
                    tool_name = generated_message.name
                    tool_call_id = generated_message.tool_call_id
                
                    process_chain_response(generated_query, tool_name, tool_call_id, prompt)
        except Exception as e:
            st.error(f"Error: {str(e)}")
        st.rerun()

if __name__ == "__main__":
    st.set_page_config(
        page_title="DrugBot",
        page_icon="💊",
        layout="wide",  # Make better use of screen width
        initial_sidebar_state="expanded"  # Start with sidebar visible
    )
    add_button_styles()
    run_chatbot()