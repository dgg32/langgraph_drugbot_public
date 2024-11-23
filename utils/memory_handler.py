from pydantic import BaseModel, Field
from trustcall import create_extractor
from typing import Optional
import uuid
from langchain_core.messages import SystemMessage, merge_message_runs
from langchain_openai import ChatOpenAI
import streamlit as st

class Concept(BaseModel):
    """This is the user-defined concepts"""
    name: Optional[str] = Field(description="The name of concept", default=None)
    items: list[str] = Field(
        description="Items that belong to the concept", 
        default_factory=list
    )


model = ChatOpenAI(model="gpt-4o", temperature=0)

concept_extractor = create_extractor(
    model,
    tools=[Concept],
    tool_choice="Concept",
    enable_inserts=True,
)

# Trustcall instruction
TRUSTCALL_INSTRUCTION = """Reflect on following interaction. 

Use the provided tools to retain any necessary definition provided by the user. 

Use parallel tool calling to handle updates and insertions simultaneously.

System Time: {time}"""

def update_concept(state, config, store):

    """Reflect on the chat history and update the concept collection."""
    
    print ("---update_concept---")
    st.session_state.tool_name = "memory"
    # Get the user ID from the config
    user_id = config["configurable"]["user_id"]

    # Define the namespace for the memories
    namespace = ("concept", user_id)

    # Retrieve the most recent memories for context
    existing_items = store.search(namespace)

    
    tool_calls = state['messages'][-1].tool_calls

    #store.put(namespace, "Concept", memory)

    # Format the existing memories for the Trustcall extractor
    category_name = "Concept"
    existing_memories = ([(existing_item.key, category_name, existing_item.value)
                          for existing_item in existing_items]
                          if existing_items
                          else None
                        )

    # # Merge the chat history and the instruction
    # TRUSTCALL_INSTRUCTION_FORMATTED=TRUSTCALL_INSTRUCTION.format(time=datetime.now().isoformat())
    updated_messages=list(merge_message_runs(messages=[SystemMessage(content=TRUSTCALL_INSTRUCTION)] + state["messages"][:-1]))
    # print ("state['messages']", state["messages"][:-1])
    # print ("updated_messages", updated_messages)
    # # Invoke the extractor
    result = concept_extractor.invoke({"messages": updated_messages, 
                                          "existing": existing_memories})
    
    # print ("result", result)

    # # Save the memories from Trustcall to the store

    for r, rmeta in zip(result["responses"], result["response_metadata"]):
        store.put(namespace,
                  rmeta.get("json_doc_id", str(uuid.uuid4())),
                  r.model_dump(mode="json"),
         )
    

    print (",,,,,,,,,,,,,,,,,,,,,,,,update_concept---tool_calls))))))))))))\n", tool_calls)
    return {"messages": [{"role": "tool", "content": "updated concept", "name":"memory", "tool_call_id":tool_calls[0]['id']}]}
    #return {"messages": [{"role": "ai", "content": result, "name":"memory", "tool_call_id":tool_calls[0]['id']}]}



