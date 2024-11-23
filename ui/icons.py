import base64
from langchain.schema import HumanMessage, AIMessage

# Tool icons mapping
TOOL_ICONS = {
    "sql": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" width="36" height="36">
            <rect width="36" height="36" fill="#f0f2f6" rx="5"/>
            <text x="18" y="23" font-family="Arial, sans-serif" font-size="18" 
                  font-weight="bold" fill="#0078D4" text-anchor="middle">
                SQL
            </text>
        </svg>
    """,
    
    "graph": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" width="36" height="36">
            <rect width="36" height="36" fill="#f0f2f6" rx="5"/>
            <!-- Central node -->
            <circle cx="18" cy="18" r="4" fill="#0078D4"/>
            <!-- Surrounding nodes -->
            <circle cx="8" cy="12" r="4" fill="#0078D4" opacity="0.8"/>
            <circle cx="28" cy="12" r="3.5" fill="#0078D4" opacity="0.9"/>
            <circle cx="7" cy="28" r="3.5" fill="#0078D4" opacity="0.7"/>
            <circle cx="26" cy="26" r="3" fill="#0078D4" opacity="0.85"/>
            <!-- Modified top-right node -->
            <circle cx="23" cy="6" r="3" fill="#0078D4" opacity="0.75"/>
            <!-- Connecting lines -->
            <line x1="18" y1="18" x2="8" y2="12" stroke="#0078D4" stroke-width="1.5"/>
            <line x1="18" y1="18" x2="28" y2="12" stroke="#0078D4" stroke-width="1.5"/>
            <line x1="18" y1="18" x2="7" y2="28" stroke="#0078D4" stroke-width="1.5"/>
            <line x1="18" y1="18" x2="26" y2="26" stroke="#0078D4" stroke-width="1.5"/>
            <!-- Modified connection line -->
            <line x1="28" y1="12" x2="23" y2="6" stroke="#0078D4" stroke-width="1.5"/>
        </svg>
    """,
    
    "vector": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" width="36" height="36">
            <rect width="36" height="36" fill="#f0f2f6" rx="5"/>
            <!-- Coordinate axes (without arrow tips) -->
            <line x1="8" y1="28" x2="28" y2="28" stroke="#0078D4" stroke-width="1.5"/>
            <line x1="8" y1="28" x2="8" y2="8" stroke="#0078D4" stroke-width="1.5"/>
            
            <!-- Vector arrows -->
            <line x1="8" y1="28" x2="20" y2="10" stroke="#0078D4" stroke-width="2"/>
            <path d="M20 10l-3 0m3 0l0 3" stroke="#0078D4" stroke-width="2" stroke-linecap="round"/>
            
            <line x1="8" y1="28" x2="24" y2="22" stroke="#0078D4" stroke-width="2"/>
            <path d="M24 22l-3 -1m3 1l-1 3" stroke="#0078D4" stroke-width="2" stroke-linecap="round"/>
        </svg>
    """,
    
    "fulltext": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" width="36" height="36">
            <rect width="36" height="36" fill="#f0f2f6" rx="5"/>
            <!-- Text lines -->
            <line x1="8" y1="10" x2="28" y2="10" stroke="#0078D4" stroke-width="2"/>
            <line x1="8" y1="16" x2="24" y2="16" stroke="#0078D4" stroke-width="2"/>
            <line x1="8" y1="22" x2="20" y2="22" stroke="#0078D4" stroke-width="2"/>
            <!-- Magnifying glass -->
            <circle cx="24" cy="24" r="4" fill="none" stroke="#0078D4" stroke-width="2"/>
            <line x1="27" y1="27" x2="30" y2="30" stroke="#0078D4" stroke-width="2" stroke-linecap="round"/>
        </svg>
    """,

    "mimicking": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" width="36" height="36">
            <rect width="36" height="36" fill="#f0f2f6" rx="5"/>
            <!-- Original document -->
            <rect x="6" y="8" width="14" height="20" fill="white" stroke="#0078D4" stroke-width="1.5"/>
            <!-- Document lines -->
            <line x1="9" y1="13" x2="17" y2="13" stroke="#0078D4" stroke-width="1.5"/>
            <line x1="9" y1="17" x2="17" y2="17" stroke="#0078D4" stroke-width="1.5"/>
            <line x1="9" y1="21" x2="15" y2="21" stroke="#0078D4" stroke-width="1.5"/>
            <!-- Copy document -->
            <rect x="16" y="12" width="14" height="20" fill="white" stroke="#0078D4" stroke-width="1.5"/>
            <!-- Copy document lines -->
            <line x1="19" y1="17" x2="27" y2="17" stroke="#0078D4" stroke-width="1.5"/>
            <line x1="19" y1="21" x2="27" y2="21" stroke="#0078D4" stroke-width="1.5"/>
            <line x1="19" y1="25" x2="25" y2="25" stroke="#0078D4" stroke-width="1.5"/>
            <!-- Arrow -->
            <path d="M14 6l4 -2l-4 -2" fill="none" stroke="#0078D4" stroke-width="1.5" stroke-linejoin="round"/>
        </svg>
    """,
    
    "user": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" width="36" height="36">
            <circle cx="18" cy="12" r="6" fill="#f0f2f6" stroke="#0078D4" stroke-width="2"/>
            <path d="M8 32c0-5.5 4.5-10 10-10s10 4.5 10 10" fill="#f0f2f6" stroke="#0078D4" stroke-width="2"/>
        </svg>
    """,
    
    "default": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" width="36" height="36">
            <circle cx="18" cy="18" r="14" fill="#f0f2f6" stroke="#0078D4" stroke-width="2"/>
            <line x1="18" y1="10" x2="18" y2="26" stroke="#0078D4" stroke-width="2"/>
            <line x1="10" y1="18" x2="26" y2="18" stroke="#0078D4" stroke-width="2"/>
        </svg>
    """,

    "clarifying": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36" width="36" height="36">
        <!-- Background -->
        <rect width="36" height="36" fill="#f0f2f6" rx="5"/>
        
        <!-- Question mark -->
        <path d="M18 8c-3.3 0-6 2.7-6 6h3c0-1.7 1.3-3 3-3s3 1.3 3 3c0 1.3-0.8 2-2 3l-1.2 1.2c-1.1 1.1-1.8 2.3-1.8 3.8v1h3v-1c0-1.3 0.8-2 2-3l1.2-1.2c1.1-1.1 1.8-2.3 1.8-3.8 0-3.3-2.7-6-6-6z" 
                fill="#ff0000"/>
        
        <!-- Dot -->
        <circle cx="18" cy="28" r="2" fill="#ff0000"/>
        </svg>
    """,
    
    "memory": """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <!-- Circle background -->
            <circle 
                cx="50" 
                cy="50" 
                r="45" 
                fill="#4CAF50" 
            />
            
            <!-- Checkmark -->
            <path 
                d="M30 50 L45 65 L70 35" 
                stroke="white" 
                stroke-width="8" 
                stroke-linecap="round" 
                stroke-linejoin="round" 
                fill="none"
            />
        </svg>
    """

}


# Tool descriptions for tooltips
TOOL_DESCRIPTIONS = {
    "sql": "For all tables in the DrugDB",
    "graph": "For the relation-rich drugs, disorders, and MOA data",
    "vector": "Only for the disorder definitions",
    "fulltext": "Only for the study titles of clinical trials",
    "mimicking": "Generate complex queries by mimicking the examples"
}


def svg_to_base64(svg_string: str) -> str:
    """Convert SVG string to base64 encoded data URL"""
    svg_string = ' '.join(svg_string.split()).strip()
    b64 = base64.b64encode(svg_string.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64}"

def get_tool_icon_and_description(message):
    """Get the appropriate icon and description for a message based on tool used"""
    if isinstance(message, HumanMessage):
        return svg_to_base64(TOOL_ICONS["user"].strip()), None
    elif isinstance(message, AIMessage):
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_name = message.tool_calls[0]["name"]
            return svg_to_base64(TOOL_ICONS.get(tool_name, TOOL_ICONS["default"]).strip()), TOOL_DESCRIPTIONS.get(tool_name)
        return svg_to_base64(TOOL_ICONS["default"].strip()), None
