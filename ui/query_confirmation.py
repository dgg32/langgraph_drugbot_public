import streamlit as st
from ui.icons import TOOL_DESCRIPTIONS, TOOL_ICONS, svg_to_base64
#from streamlit_ace import st_ace
from streamlit_monaco import st_monaco
import sqlparse

def create_query_confirmation_ui() -> str | None:
    """
    Create the query confirmation UI and return the confirmed query.
    Returns:
    str | None: Returns either:
    - "waiting" if no button was pressed
    - the confirmed/edited query if Confirm was pressed
    - None if Reject was pressed
    """
    container = st.container()
    with container:
        # Get the SVG icon for the current tool

        tool_icon = TOOL_ICONS.get(st.session_state.tool_name, TOOL_ICONS["default"])
        icon_b64 = svg_to_base64(tool_icon.strip())
        description = TOOL_DESCRIPTIONS.get(st.session_state.tool_name, "")
        
        print ("st.session_state.tool_name", st.session_state.tool_name)
        
        
        ###### AI cannot answer the question without some claification
        if st.session_state.tool_name == "clarifying":
            print ("in clarifying")
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px;">
                    <img src="{icon_b64}" style="width: 30px; height: 30px; background: #f0f2f6; padding: 5px; border-radius: 5px;">
                    <h3 style="margin: 0;">{st.session_state.current_query}</h3>
                </div>
                                        
            """, unsafe_allow_html=True)
            st.markdown('<hr class="qa-separator">', unsafe_allow_html=True)
        elif st.session_state.tool_name == "memory":
            print ("in memory")
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px;">
                    <img src="{icon_b64}" style="width: 30px; height: 30px; background: #f0f2f6; padding: 5px; border-radius: 5px;">
                    <h3 style="margin: 0;">Updated the memory</h3>
                </div>                                   
            """, unsafe_allow_html=True)
            st.markdown('<hr class="qa-separator">', unsafe_allow_html=True)
        #Enough information to answer the question
        else:
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px;">
                    <img src="{icon_b64}" style="width: 30px; height: 30px; background: #f0f2f6; padding: 5px; border-radius: 5px;">
                    <h3 style="margin: 0;">This query uses the {st.session_state.tool_name.replace("_", " ")}</h3>
                </div>
            """, unsafe_allow_html=True)
        
            st.markdown(f"*{description}*")
            st.markdown(f"**Review and edit the query if needed, press Confirm to proceed:**")
            
            # If there was an error in the previous attempt, show it
            if st.session_state.last_error:
                st.error(f"Error in previous query: {st.session_state.last_error}")
                st.markdown("Please fix the query and try again, or reject to move to the next question.")
            
            # Code editor
            #editor_response = st_ace(language='sql', value=st.session_state.current_query)
            query_to_edit = sqlparse.format(st.session_state.current_query, reindent=True, keyword_case='upper')
            if st.session_state.tool_name == "graph":
                query_to_edit = st.session_state.current_query
            editor_response = st_monaco(value=query_to_edit, height="150px", language="sql")
            
            # Add spacing after code editor
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            
            # Create a container for buttons with padding bottom to avoid overlap
            button_container = st.container()
            with button_container:
                # Create two columns for the buttons
                col1, col2 = st.columns([1, 1])
                
                # Confirm button in first column
                with col1:
                    confirm = st.button(
                        "✓ Confirm",
                        use_container_width=True,
                        type="primary",
                        key="confirm_button"
                    )
                    if confirm:
                        st.session_state.awaiting_confirmation = False                    
                        return editor_response
                
                # Reject button in second column
                with col2:
                    reject = st.button(
                        "✕ Reject",
                        use_container_width=True,
                        type="secondary",
                        key="reject_button"
                    )
                    if reject:
                        st.session_state.awaiting_confirmation = False
                        st.session_state.last_error = None
                        st.session_state.retry_count = 0
                        return None
        
        # Add spacing at the bottom to prevent overlap with chat input
        st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
    
    return "waiting"