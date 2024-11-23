import streamlit as st
from langchain.schema import HumanMessage, AIMessage
from ui.icons import get_tool_icon_and_description
import utils.save_interaction as save_interaction

def display_user_message(message: HumanMessage) -> None:
    """
    Display a user message in the chat interface with appropriate styling and icon.
    
    Args:
        message (HumanMessage): The user's message to display
    """
    icon, _ = get_tool_icon_and_description(message)
    
    with st.chat_message("user", avatar=icon):
        st.markdown(message.content)

def display_assistant_message(message: AIMessage, user_question: str = None) -> None:
    """
    Display an assistant message in the chat interface with appropriate styling,
    icon, and any tool information.
    
    Args:
        message (AIMessage): The assistant's message to display
        user_question (str): The corresponding user question for save functionality
    """
    tool_name = (message.tool_calls[0]["name"] 
                if hasattr(message, 'tool_calls') and message.tool_calls 
                else "default")
    
    icon, description = get_tool_icon_and_description(message)
    
    with st.chat_message("assistant", avatar=icon):
        st.markdown(message.content)
        
        if hasattr(message, 'tool_calls') and message.tool_calls:
            with st.expander("See query details"):
                st.markdown(f"**Tool Used:** {tool_name.replace('_', ' ')}")
                if description:
                    st.markdown(f"**Description:** {description}")
                
                if 'args' in message.tool_calls[0]:
                    args = message.tool_calls[0]['args']
                    query = None
                    
                    if isinstance(args, dict):
                        query = (args.get('executed_query') or 
                               args.get('query') or 
                               args.get('my_question'))
                    elif isinstance(args, str):
                        query = args
                    
                    if query:
                        st.markdown("**Query Used:**")
                        st.code(query, language='sql')
                        

                        st.markdown('<p class="save-hint">Would you like to save this interaction?</p>', 
                                  unsafe_allow_html=True)
                        
                        if st.button("💾 Save Interaction", 
                                   key=f"save_{id(message)}",
                                   help="Save this question and query to the examples file",
                                   type="primary"):
                            if query:
                                save_interaction.save_interaction(user_question, query)
                                st.success("Interaction saved successfully!")

def display_message_pair(messages: list, i: int) -> bool:
    """
    Display a pair of user and assistant messages, if they exist.
    
    Args:
        messages (list): List of all messages
        i (int): Current index in the message list
        
    Returns:
        bool: True if an assistant message was displayed after the user message
    """

    #print ("messages[i],", i, messages[i])

    question = ""
    if isinstance(messages[i], HumanMessage):
        question = messages[i].content
        display_user_message(messages[i])
    
    if i + 1 < len(messages) and isinstance(messages[i + 1], AIMessage):
        
        display_assistant_message(messages[i + 1], question)
        st.markdown('<hr class="qa-separator">', unsafe_allow_html=True)
        return True
    return False

def display_chat_messages() -> None:
    """
    Display all chat messages with appropriate styling and separation.
    """
    messages = st.session_state.messages

    #print ("+++++++display_chat_messages+++++++++", messages)
    i = 0
    while i < len(messages):
        assistant_displayed = display_message_pair(messages, i)
        i += 2 if assistant_displayed else 1