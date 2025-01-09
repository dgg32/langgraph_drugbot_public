
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph, MessagesState, START
import utils.my_langchain_tools as my_langchain_tools
import sqlite3
from langchain_openai import ChatOpenAI
from langgraph.store.memory import InMemoryStore
from typing import TypedDict, Literal, Dict
from langchain_openai import ChatOpenAI
import streamlit as st
from langchain_core.messages import trim_messages

import utils.memory_handler as my_memory

from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage, AIMessage

import json
import utils.my_llm as my_llm

#llm = ChatOpenAI(model="gpt-4o", temperature=0)


all_tools = [my_langchain_tools.sql, my_langchain_tools.graph, my_langchain_tools.mimicking, my_langchain_tools.vector, my_langchain_tools.fulltext]
all_tools_category = {"sql": [my_langchain_tools.sql], "graph": [my_langchain_tools.graph], "mimicking": [my_langchain_tools.mimicking], 
                      "vector": [my_langchain_tools.vector], "fulltext": [my_langchain_tools.fulltext], "automatic": all_tools}

class State(MessagesState):
    selected_tools: list[str]
    #umls_terms: Dict[str, str]



# Define the function that calls the model
def choose_query_tool(state, config, store):
    MODEL_SYSTEM_MESSAGE = """You are a helpful assistant tasked with performing Q&A with a drug-trial DuckDB as backend.
                            Your task is to call the right query tool and forward the user's question to it.
                            IMPORTANT: do not modify or generate a query yourself. That is the job of the query tools.
                            Capture both the question and the amount of results 'top_k' that the user want to see. If the user does not specify the amount, don't ask the user back to clarify and just set top_k = 30.
                            Only one query tool for one question. Do not break the question into multiple parts.
                            If the user has defined some concepts or terms, use them in your query faithfully to personalize your responses.
                            Here is the memory (it may be empty): {memory}"""

    print("---call_tool_to_generate_query---")
    
    # Get selected tools
    selected_tools = state["selected_tools"]
    obj_tools = []
    for t in selected_tools:
        if t in all_tools_category:
            obj_tools = all_tools_category[t]
    
    print("---call_tool_to_generate_query---\nobj_tools:", obj_tools)
    model = my_llm.llm.bind_tools(obj_tools)
    
    # Get user context and memories
    user_id = config["configurable"]["user_id"]
    namespace = ("concept", user_id)
    existing_items = store.search(namespace)
    existing_memories = ([existing_item.value
                         for existing_item in existing_items]
                         if existing_items
                         else None)
    
    # Format memories
    format_memories = "\n"
    if existing_memories:
        for memo in existing_memories:
            format_memories += f" {memo.get('name')}: {str(memo.get('items'))}\n"
    
    # Prepare messages
    system_msg = MODEL_SYSTEM_MESSAGE.format(memory=format_memories)
    messages = state["messages"]
    print("++++++++---In choose_query_tool\nmessages:", messages)
    
    # Get recent message history
    last_human_msg = []
    for m in messages[::-1]:
        if m.type in ["human", "ai"]:
            if m.content.strip():
                last_human_msg.insert(0, m)
            if len(last_human_msg) == 10:
                break
    
    print("++++++++---last_msg", last_human_msg)
    
    # Get tool selection from the model
    tool_selection = model.invoke([SystemMessage(content=system_msg)] + last_human_msg)
    print("++++++++---In choose_query_tool, tool_selection:", tool_selection)

    
    return {"messages": [tool_selection]}


def limit_query_tool(state, config, store):
    """ You have five tools to choose from to answer the user's question. 
    sql covers all the tables and should be prefered. 
    graph covers the relationships among drugs, disorders and MOA. 
    vector covers the disorder definition. 
    fulltext covers the trials' StudyTitles. 
    mimicking uses user defined query templates and is good for complex queries. automatic means you choose the best tool."""
    print ("---limit_query_tool---")
    tool_call_id = ""
    for m in state["messages"][::-1]:
        if m.type == "ai":
            #print ("---limit_query_tool---", m.type, m)
            tool_call_id = m.additional_kwargs["tool_calls"][0]["id"]
            break


    print ("I captured the tool_call_id", tool_call_id)
    state["messages"].append(ToolMessage(content='', tool_call_id=tool_call_id))

    for m in state["messages"][::-1]:
        if m.type == "human":
            tool_choice = m.tool_choice
            if tool_choice in all_tools_category:
                return {"selected_tools": [tool_choice]}
            else:
                return {"selected_tools": ["automatic"]}
    #return {"selected_tools": }

MODEL_SYSTEM_MESSAGE = """You are a helpful chatbot. 

You are designed to be a companion to a user, helping them get answer from a drug-trial database.

You have a long term memory which keeps track one thing:
User defined concepts (terms and their definitions or examples provided by the user, such as the 'Four Horsemen' are cardiovascular disease, cancer, neurodegenerative disease, and foundational disease)

Here is the current User Concepts (may be empty if no information has been collected yet):
<user_definition>
{user_definition}
</user_definition>

Here are your instructions for reasoning about the user's messages:

1. Reason carefully about the user's messages as presented below. 

2. Must take one and only one of the following actions, never more than one!!!!!!! Do NOT try to answer the question yourself, it is the job of the query tools:
- If the message looks like a definition, update the user's definition by calling the update_concept tool
- If the message looks like a question or a request, use the limit_query_tool route to generate a query

3. Tell the user that you have updated your memory, if appropriate:
- Tell the user them when you update the concept list"""

class Choose_Direction(TypedDict):
    """ Decision on which route to go next """
    action_type: Literal['update_concept', 'limit_query_tool']

def select_intent(state, config, store):
    """Load user defined concepts from the store and use them to personalize the chatbot's response."""

    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Retrieve profile memory from the store
    namespace = ("profile", user_id)
    memories = store.search(namespace)
    if memories:
        user_definition = memories[0].value
    else:
        user_definition = None

    system_msg = MODEL_SYSTEM_MESSAGE.format(user_definition=user_definition)

    print ("Before response")
    #print ("""---select_intent---\n state["messages"]:""", state)
    #for m in state["messages"]:
    #    print ("---select_intent---", m)

    #messages = filter_messages(state["messages"])

    #messages = state["messages"]
    # messages = trim_messages(
    #         state["messages"],
    #         max_tokens=32000,
    #         strategy="last",
    #         token_counter=ChatOpenAI(model="gpt-4o"),
    #         allow_partial=False,
    #     )
    #messages = filter_messages(state["messages"])
    #response = llm.bind_tools([Choose_Direction], parallel_tool_calls=False).invoke([SystemMessage(content=system_msg)]+state["messages"])

    response = my_llm.llm.bind_tools([Choose_Direction], parallel_tool_calls=False).invoke([SystemMessage(content=system_msg)] + state["messages"])

    print ("---select_intent---\nresponse: ", response)
    #print ("+++++---select_intent---+++\nresponse: ", response, "\nconfig: ", config, "\nstore: ", store)
    return {"messages": [response]}



def route_message(state, config, store) -> Literal[END, "update_concept", "limit_query_tool"]:

    """Reflect on the memories and chat history to decide whether to update the memory collection."""
    message = state['messages'][-1]
    print ("---route_message---\n message:", state['messages'])
    print ("len(message.tool_calls) = ", len(message.tool_calls))
    if len(message.tool_calls) ==0:
        return END
    else:
        tool_call = message.tool_calls[0]
        print ("---route_message---\n tool_call:", tool_call)
        if tool_call['args']["action_type"] == "update_concept":
            print ("***********update_concept")
            return "update_concept"
        elif tool_call['args']["action_type"] == "limit_query_tool":
            print ("***********limit_query_tool")
            return "limit_query_tool"
        else:
            raise ValueError

def human_feedback(state):
    print("---human_feedback state---", state)
    print("---human_confirms_query---")
    pass



builder = StateGraph(State)
# Define the three nodes we will cycle between

builder.add_node("select_intent", select_intent)

#builder.add_node("intents", intents)

builder.add_node("update_concept", my_memory.update_concept)


builder.add_node("limit_query_tool", limit_query_tool)
builder.add_node("choose_query_tool", choose_query_tool)
tool_node = ToolNode(all_tools)
builder.add_node("tools", tool_node)
#workflow.add_node("ask_human", ask_human)
builder.add_node("human_feedback", human_feedback)
builder.add_node("execute_query_and_answer", my_langchain_tools.execute_query_and_answer)

builder.add_edge(START, "select_intent")
builder.add_conditional_edges("select_intent", route_message)
builder.add_edge("update_concept", END)

builder.add_edge("limit_query_tool", "choose_query_tool")
builder.add_conditional_edges("choose_query_tool", tools_condition, path_map=["tools", "__end__"])

#workflow.add_edge("tools", "execute_query_and_answer")
builder.add_edge("tools", "human_feedback")

# After we get back the human response, we go back to the choose_query_tool
builder.add_edge("human_feedback", "execute_query_and_answer")

builder.add_edge("execute_query_and_answer", END)

#memory = MemorySaver()

# if os.path.exists("checkpoints.db"):
#     os.remove("checkpoints.db")
db_path = 'checkpoints.db'
conn = sqlite3.connect(db_path, check_same_thread=False)
within_thread_memory = SqliteSaver(conn)
#within_thread_memory = MemorySaver()

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
# We add a breakpoint BEFORE the `ask_human` node so it never executes
across_thread_memory = InMemoryStore()
app = builder.compile(checkpointer=within_thread_memory, interrupt_before=["human_feedback"], store=across_thread_memory)