# File: utils/error_handler.py

import streamlit as st
#from typing import Optional

def handle_query_error(error: Exception) -> None:
    """
    Handle errors that occur during query execution, managing retry attempts
    and error states.
    
    Args:
        error (Exception): The error that occurred during query execution
    """
    # Store the error message in session state
    st.session_state.last_error = str(error)
    st.session_state.retry_count += 1
    
    # If we've had too many retries, auto-reject and reset state
    if st.session_state.retry_count >= 3:
        st.error("Maximum retry attempts reached. Moving to next question.")
        clear_error_state()
        clear_confirmation_state()
    else:
        # Keep the confirmation UI open for another try
        st.session_state.awaiting_confirmation = True
        
def clear_error_state() -> None:
    """
    Reset error-related session state variables.
    """
    st.session_state.last_error = None
    st.session_state.retry_count = 0

def clear_confirmation_state() -> None:
    """
    Reset all confirmation-related session state variables.
    """
    st.session_state.awaiting_confirmation = False
    st.session_state.current_query = None
    st.session_state.current_chain_input = None
    st.session_state.tool_name = None

# def get_friendly_error_message(error: Exception) -> str:
#     """
#     Convert technical error messages into user-friendly messages.
    
#     Args:
#         error (Exception): The original error

#     Returns:
#         str: A user-friendly error message
#     """
#     error_str = str(error)
    
#     # Common SQL errors
#     if "syntax error" in error_str.lower():
#         return "There appears to be a syntax error in the SQL query. Please check the query structure."
#     elif "permission denied" in error_str.lower():
#         return "The query doesn't have permission to access this data. Please try a different approach."
#     elif "relation does not exist" in error_str.lower():
#         return "The table or view referenced in the query doesn't exist. Please verify the table names."
#     elif "column does not exist" in error_str.lower():
#         return "One of the columns referenced in the query doesn't exist. Please check the column names."
#     elif "division by zero" in error_str.lower():
#         return "The query attempted to divide by zero. Please check any calculations in the query."
    
#     # Graph query errors
#     elif "cycle detected" in error_str.lower():
#         return "The graph query contains a circular reference. Please modify the query to avoid cycles."
#     elif "depth limit exceeded" in error_str.lower():
#         return "The graph query is too deep. Please reduce the number of relationship levels."
    
#     # Vector query errors
#     elif "dimension mismatch" in error_str.lower():
#         return "The vector dimensions don't match. Please ensure you're using the correct embedding size."
#     elif "invalid vector format" in error_str.lower():
#         return "The vector format is invalid. Please check the vector representation."
    
#     # Fulltext query errors
#     elif "invalid text query" in error_str.lower():
#         return "The text search query is invalid. Please check the search syntax."
    
#     # Default case
#     return f"An error occurred while executing the query: {error_str}"

# def handle_tool_specific_error(error: Exception, tool_name: str) -> Optional[str]:
#     """
#     Handle tool-specific errors and provide appropriate suggestions.
    
#     Args:
#         error (Exception): The error that occurred
#         tool_name (str): The name of the tool that caused the error

#     Returns:
#         Optional[str]: A suggestion for fixing the error, if available
#     """
#     error_str = str(error).lower()
    
#     if tool_name == "SQL_QueryTool":
#         if "syntax error" in error_str:
#             return """
#                 Try the following:
#                 1. Check for missing or extra commas
#                 2. Verify table and column names
#                 3. Ensure all SQL keywords are properly used
#                 4. Check that parentheses are properly closed
#                 """
                
#     elif tool_name == "Graph_QueryTool":
#         if "depth limit" in error_str:
#             return """
#                 Try to simplify the query by:
#                 1. Reducing the number of relationship levels
#                 2. Using LIMIT to restrict the result set
#                 3. Adding more specific filters
#                 """
                
#     elif tool_name == "Vector_QueryTool":
#         if "dimension" in error_str:
#             return """
#                 Ensure your vector query:
#                 1. Uses 1536-dimensional vectors
#                 2. Has proper array syntax
#                 3. Includes all required vector components
#                 """
                
#     elif tool_name == "Fulltext_QueryTool":
#         if "invalid" in error_str:
#             return """
#                 Check your text search query:
#                 1. Use proper text search operators
#                 2. Ensure search terms are properly quoted
#                 3. Verify language settings if applicable
#                 """
    
#     return None

# Example usage in the main app:
"""
try:
    process_confirmed_query(confirmation_result)
except Exception as e:
    handle_query_error(e)
    
    # Get user-friendly error message
    friendly_message = get_friendly_error_message(e)
    st.error(friendly_message)
    
    # Get tool-specific suggestions if available
    if suggestion := handle_tool_specific_error(e, st.session_state.tool_name):
        st.info("Suggestions for fixing the error:" + suggestion)
"""