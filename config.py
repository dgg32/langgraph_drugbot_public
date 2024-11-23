import streamlit as st

def init_session_state():
    """Initialize session state variables"""
    session_vars = {
        "messages": [],
        "awaiting_confirmation": False,
        "current_query": None,
        "current_chain_input": None,
        "tool_name": None,
        "last_error": None,
        "retry_count": 0,
        "tool_call_id": "dummy_id"
    }
    
    for var, default in session_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default


def add_button_styles():
    """Add custom CSS styles to the interface"""
    st.markdown("""
        <style>
        /* Hide default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #f8f9fa;
            padding: 1rem;
            z-index: 1000000;
        }
        
        /* Sidebar header */
        [data-testid="stSidebar"] [data-testid="stMarkdown"] > h3 {
            color: #0078D4;
            font-size: 1rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #dee2e6;
        }
        
        /* Example query buttons styling */
        [data-testid="stSidebar"] .stButton > button {
            height: auto !important;
            white-space: normal !important;
            text-align: left !important;
            padding: 0.75rem 1rem !important;
            background-color: white !important;
            border: 1px solid #dee2e6 !important;
            margin-bottom: 0.5rem !important;
            font-size: 0.9rem !important;
            line-height: 1.4 !important;
            color: #0078D4 !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
        }
        
        /* Add icon to example queries */
        [data-testid="stSidebar"] .stButton > button::before {
            content: "💡";
            margin-right: 0.5rem;
        }
        
        /* Add hover effect to example buttons */
        [data-testid="stSidebar"] .stButton > button {
            position: relative !important;
        }
        
        [data-testid="stSidebar"] .stButton > button::after {
            content: "→";
            position: absolute;
            right: 1rem;
            opacity: 0;
            transition: all 0.2s ease;
        }
        
        [data-testid="stSidebar"] .stButton > button:hover::after {
            opacity: 1;
            right: 0.5rem;
        }
        
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: #e9ecef !important;
            border-color: #0078D4 !important;
            transform: translateX(3px) !important;
        }
        
        /* Chat input container - lower z-index */
        div[data-testid="stHorizontalBlock"]:has([data-testid="stChatInput"]) {
            position: fixed !important;
            bottom: 0 !important;
            left: calc(20.5rem + 50px) !important;
            right: 20px !important;
            background: white !important;
            padding: 20px !important;
            z-index: 100 !important;
            border-radius: 12px 12px 0 0 !important;
            box-shadow: 0 -4px 20px rgba(0,0,0,0.1) !important;
            backdrop-filter: blur(8px) !important;
            border: 1px solid rgba(230, 230, 230, 0.9) !important;
            margin: 0 !important;
            display: flex !important;
            align-items: center !important;
            gap: 20px !important;
        }
        
        /* Make sure main content doesn't overlap with fixed input */
        .main .block-container {
            padding-bottom: 100px;
        }
        
        /* Style columns within the container */
        div[data-testid="column"] {
            padding: 0 !important;
            margin: 0 !important;
        }
        
        /* Chat input styling */
        [data-testid="stChatInput"] {
            margin: 0 !important;
        }
        
        /* Dropdown styling */
        [data-testid="stSelectbox"] {
            margin: 0 !important;
        }
        
        /* Enhance dropdown appearance */
        .stSelectbox > div > div {
            background: white;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        
        /* Ensure proper spacing for chat messages */
        [data-testid="stChatMessageContainer"] {
            margin-bottom: 120px !important;
            overflow-y: auto !important;
        }
        
        /* Add gradient fade effect */
        .main .block-container::after {
            content: "";
            position: fixed;
            bottom: 80px;
            left: 0;
            right: 0;
            height: 40px;
            background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,1));
            pointer-events: none;
            z-index: 98;
        }
        
        /* Confirmation button styling */
        [data-testid="element-container"]:has([data-testid="baseButton-primary"]) button,
        [data-testid="element-container"]:has([data-testid="baseButton-secondary"]) button {
            width: 100% !important;
            padding: 0.5rem 1rem !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
            min-height: 40px !important;
            z-index: 1001 !important;
            position: relative !important;
        }
        
        /* Primary button (Confirm) */
        [data-testid="baseButton-primary"] {
            background-color: #0078D4 !important;
            color: white !important;
            border: none !important;
        }
        
        [data-testid="baseButton-primary"]:hover {
            background-color: #006abe !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        }
        
        /* Secondary button (Reject) */
        [data-testid="baseButton-secondary"] {
            background-color: white !important;
            color: #dc3545 !important;
            border: 1px solid #dc3545 !important;
        }
        
        [data-testid="baseButton-secondary"]:hover {
            background-color: #fff5f5 !important;
            border-color: #dc3545 !important;
        }

        /* Code editor container */
        .code-editor-container {
            margin-bottom: 20px !important;
        }
        
        /* Code editor specific styling */
        .streamlit-expanderHeader {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        /* Error message styling */
        .stAlert {
            margin-bottom: 1rem !important;
        }
                
        /* Add space between Q&A rounds */
        .qa-separator {
            border: none;
            height: 1px;
            background: linear-gradient(to right, transparent, #0078D4, transparent);
            margin: 2rem 0;
            opacity: 0.2;
        }
                

            /* Ensure the chat container is scrollable */
        [data-testid="stChatMessageContainer"] {
            overflow-y: auto !important;
            margin-bottom: 120px !important;
            flex: 1 1 auto;
        }

        /* Add smooth scrolling behavior */
        .main {
            scroll-behavior: smooth;
        }
        
        /* Save interaction button styling */
        .save-interaction-button {
            margin-top: 10px !important;
            margin-bottom: 20px !important;
        }
        
        .save-hint {
            color: #666;
            font-style: italic;
            margin-bottom: 10px;
        }
        </style>
        
        
    """, unsafe_allow_html=True)