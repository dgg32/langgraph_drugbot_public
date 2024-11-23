#import duckdb
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
import yaml
import os
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
#from operator import itemgetter
#from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from sqlalchemy import create_engine
from langchain_core.tools import tool
from langchain_core.prompts import FewShotPromptTemplate
from langchain_core.prompts import PromptTemplate
import duckdb
import json
from langchain_community.vectorstores import LanceDB
from langchain.chains import create_sql_query_chain
#from langchain_core.messages import AIMessage
# from langchain_core.runnables import (
#     Runnable,
#     RunnableLambda,
#     RunnableMap,
#     RunnablePassthrough,
# )
import my_db_specifics as my_db_specifics

with open("config.yaml", "r") as stream:
    try:
        PARAM = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

# Set up your OpenAI API key
os.environ["OPENAI_API_KEY"] = PARAM['openai_api']
llm = ChatOpenAI(model_name="gpt-4o-mini")

@tool
def mimicking(question: str, top_k: int):
    """ When you think the question is unlikely to be answer by a single simple query tool, 
    or the question may likely require a complex combination of sql, vector, graph, and full-text search tools,
    or it may require to join several tables, use this tool to generate those complex queries by closely mimicing the examples."""
    examples = []

    print ("in mimicking")

    for line in open("interaction.jsonl", "r").readlines():
        example = json.loads(line)
        examples.append(example)

    print ("examples", json.dumps(examples, indent=2))
    database_description = my_db_specifics.sql_database_prompt

    print ("before example_selector")
    example_selector = SemanticSimilarityExampleSelector.from_examples(
        examples,
        OpenAIEmbeddings(),
        LanceDB,
        k=5,
        input_keys=["input"],
    )
    print ("before example_prompt")
    example_prompt = PromptTemplate.from_template("User input: {input}\nquery: {query}")
    print ("after example_prompt")
    complex_generation_prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=example_prompt,
        prefix="""You are a duckdb expert. Given an input question, take the examples as templates, and only substitute the template variables with those extracted from the question. Closely mimicing the examples and don't modify the examplar structure easily, since they are curated by human. Add a 'LIMIT {top_k}' clause to the end of the query. \n\nHere is the relevant table info: {table_info}\n\nBelow are a number of examples of questions and their corresponding queries. Use them to as inspiration generate your query.
        - Almost always start with SELECT, unless it is a graph query.
        - The subquery in FROM clause should have an alias, without the keyword AS, Here is an example: SELECT * FROM Trials, GRAPH_TABLE( ... )  drug_for_disease WHERE Trials.drug_cui = drug_for_disease.drug_cui
        - If the search term contains a single quote, it should be escaped with another single quote. For example, 'Alzheimer's Disease' should be 'Alzheimer''s Disease'.
        - Only return query not anything else like ```sql ... ```
        - Every variable in the graph pattern has to be bound by a variable. For example, (i:Drug)-[:MAY_TREAT]->(c:Disorder WHERE c.name = 'Alzheimer''s Disease') is not correct because :MAY_TREAT is not bound to a variable. Instead, it should be (i:Drug)-[m:MAY_TREAT]->(c:Disorder WHERE c.name = 'Alzheimer''s Disease').
        - If it is a graph query, use "COLUMNS" as the return statement in the graph query.
        - Based on the question, include a 'LIMIT' clause before the end of the query. Never write 'LIMIT 0;' nor 'LIMIT;' If you are unsure about the number of results, remove the LIMIT clause entirely.
        - Make sure all parentheses are balanced.
        - Ends with a semicolon
        - Output the final query only.
        """,
        suffix="User input: {input}\ngraph query: ",
        input_variables=["input", "table_info", "top_k"],
    )

    print ("before generate_query")
    generate_query = (
        complex_generation_prompt
        | llm | StrOutputParser()
    )

    query = generate_query.invoke({"input": question, "table_info": database_description, "top_k": top_k})
    print ("query", query)
    return query


@tool
def sql(question: str, top_k: int):
    """ Use the SQL route to get the answer from the database. It can find data across all tables. Consider it as the default tool. top_k is the number of results to return."""
    print ("==== sql ====")
    print ("sql question", question, "top_k", top_k)
    database_description = my_db_specifics.sql_database_prompt
    
    examples = my_db_specifics.sql_examples


    example_selector = SemanticSimilarityExampleSelector.from_examples(
        examples,
        OpenAIEmbeddings(),
        LanceDB,
        k=5,
        input_keys=["input"],
    )

    example_prompt = PromptTemplate.from_template("User input: {input}\nSQL query: {query}")
    sql_generation_prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=example_prompt,
        prefix="""You are a DuckDB expert. Given an input question, create a syntactically correct DuckDB query to run. Ignore the {top_k} parameter for now.
        Here is the relevant table info: {table_info}
        - If the search term contains a single quote, it should be escaped with another single quote. For example, 'Alzheimer's Disease' should be 'Alzheimer''s Disease'.
        - Only return SQL Query not anything else like ```sql ... ```
        - Using NOT IN with NULL values
        - Using UNION when UNION ALL should have been used
        - Using BETWEEN for exclusive ranges
        - Data type mismatch in predicates
        - Using the correct number of arguments for functions
        - Casting to the correct data type
        - Using the proper columns for joins
        - Never write a LIMIT clause.
        - Make sure all parentheses are balanced.
        - Ends with a semicolon
        - Output the final SQL query only.
        Below are a number of examples of questions and their corresponding SQL queries.""",
        suffix="User input: {input}\nSQL query: ",
        input_variables=["input", "top_k", "table_info"],
    )

    engine = create_engine('duckdb:///' + PARAM['drugdb_path'], connect_args={
        'read_only': True
    })

    db = SQLDatabase(engine=engine)

    #db = SQLDatabase.from_uri('duckdb:///' + PARAM['drugdb_path'])
    write_query = create_sql_query_chain(llm, db, sql_generation_prompt)
    print ("write_query", write_query)

    # generate_query = (
    #     write_query
    #     | llm | StrOutputParser()
    # )
    
    sql_query = write_query.invoke({"question": question, "table_info": database_description, "top_k": top_k})
    sql_query = sql_query.strip()
    if top_k is not None:
        if sql_query.endswith(";"):
            sql_query = sql_query[:-1] + f"\n LIMIT {top_k};"
        else:
            sql_query = sql_query + f"\n LIMIT {top_k};"
    #print ("sql_query", sql_query)
    
    engine.dispose()
    #db.close()
    #return {"draft_query": [sql_query]} 
    return sql_query
    #print ("sql_query", sql_query)
    #return AIMessage(sql_query)


@tool
def graph(question: str, top_k: int):
    
    """Use the graph query language route to get the answer from the database. Only suitable for questions that involve the interrelationship between the Drugs, Disorders, and MOA tables. top_k is the number of results to return."""

    print ("++++++++++++++++question", question, "top_k", top_k)
    database_description = my_db_specifics.graph_database_prompt
    print ("before examples")
    examples = my_db_specifics.graph_examples
    print ("before example_selector")
    example_selector = SemanticSimilarityExampleSelector.from_examples(
        examples,
        OpenAIEmbeddings(),
        LanceDB,
        k=5,
        input_keys=["input"]
    )
    print ("before example_prompt")
    example_prompt = PromptTemplate.from_template("User input: {input}\ngraph query: {query}")
    print ("after example_prompt")
#- Add a 'LIMIT {top_k}' clause to the end of the query. Place the LIMIT clause after the closing parenthesis.
    pgq_generation_prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=example_prompt,
        prefix="""You are a DuckPGQ expert. Given an input question, create a syntactically correct graph query to run.
        Here is the relevant table info: {table_info}
        DuckPGQ is very similar to Cypher. But there are some differences.
        Double check the user's DuckPGQ graph query for common mistakes, including:
        - If the search term contains a single quote, it should be escaped with another single quote. For example, 'Alzheimer's Disease' should be 'Alzheimer''s Disease'.
        - It must start with "FROM GRAPH_TABLE (drug_graph" before the MATCH clause. It ends with a closing parenthesis before the LIMIT clause.
        - Only return graph query not anything else like ```sql ... ```
        - Every variable in the graph pattern has to be bound by a variable. For example, (i:Drug)-[:MAY_TREAT]->(c:Disorder WHERE c.name = 'Alzheimer''s Disease') is not correct because :MAY_TREAT is not bound to a variable. Instead, it should be (i:Drug)-[m:MAY_TREAT]->(c:Disorder WHERE c.name = 'Alzheimer''s Disease').
        - Use "COLUMNS" as the return statement in the graph query.
        - Replace all '\n' with a space.
    
        - Never write a LIMIT clause.
        - Make sure all parentheses are balanced.
        - Ends with a semicolon
        - Output the final graph query only.
        Below are a number of examples of questions and their corresponding graph queries.""",
        suffix="User input: {input}\ngraph query: ",
        input_variables=["input", "table_info", "top_k"],
    )



    generate_query = (
        pgq_generation_prompt
        | llm | StrOutputParser()
    )

    graph_query = generate_query.invoke({"input": question, "table_info": database_description, "top_k": top_k})
    graph_query = graph_query.strip()
    #print ("graph_query", graph_query)
    if top_k is not None:
        if graph_query.endswith(";"):
            graph_query = graph_query[:-1] + f"\n LIMIT {top_k};"
        else:
            graph_query = graph_query + f"\n LIMIT {top_k};"
    return graph_query
    #return AIMessage(graph_query)


@tool
def vector(question: str, top_k: int = 5) -> str:
    """Use vector search to get the disorder from the database. Only suitable for fuzzy questions that involve the definition of disorder, 
    such as "joint-related disorders" or "disorders that cause rash". If the user asks for a specific disorder, such as 'what is Pericarditis?', use the SQL or graph instead."""
    
    vector_query = my_db_specifics.vector_search_query_template.format(question=question, limit=top_k)
    
    return vector_query

@tool
def fulltext(question: str, top_k: int = 10) -> str:
    """Use the full text search to get the trials from the database. Only suitable for questions that involve the StudyTitle. Use this tool when users question does not read like a sentence and looks like some keywords instead. Keep the original query for the user's reference. And keep all the operators such as &, |, and ! in the query."""
    #print ("original_query", original_query)
    field_with_full_text_search = "StudyTitle"

    generate_query = my_db_specifics.full_text_search_query_template.format(original_query=question.replace("'", "''"), field=field_with_full_text_search, limit=top_k)

    
    return generate_query


def execute_query_and_answer(state):
    
    """ Node to answer a question """
    print("---execute_query_and_answer---")
    
    #print ("state", state)
    # for i, m in enumerate(state["messages"]):
    #     print (i, m)

    messages = state["messages"]
    question = ""
    query = ""
    #query = state["messages"][-2].content
    for m in messages[::-1]:
        if question != "" and query != "":
            break
        #print ("execute_query_and_answer.m", m)
        if m.type == "ai" and len(question) == 0:
            if len(m.content.strip()) == 0:
                question = json.loads(m.additional_kwargs["tool_calls"][0]["function"]["arguments"])["question"]
        elif m.type == "human" and len(query) == 0:
            #print ("m.content", m.content)
            query = m.content

    
    #1 content='' additional_kwargs={'tool_calls': [{'id': 'call_u3LxRfcWLN4lGxWD9joQzYmN', 'function': {'arguments': '{"question":"What diseases can hydroflumethiazide treat?","top_k":5}', 'name': 'sql'}, 'type': 'function'}], 'refusal': None} response_metadata={'token_usage': {'completion_tokens': 28, 'prompt_tokens': 109, 'total_tokens': 137, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_name': 'gpt-4o-2024-08-06', 'system_fingerprint': 'fp_45cf54deae', 'finish_reason': 'tool_calls', 'logprobs': None} id='run-82248ab2-7303-467c-8a4e-a5c3ca416eb3-0' tool_calls=[{'name': 'sql', 'args': {'question': 'What diseases can hydroflumethiazide treat?', 'top_k': 5}, 'id': 'call_u3LxRfcWLN4lGxWD9joQzYmN', 'type': 'tool_call'}] usage_metadata={'input_tokens': 109, 'output_tokens': 28, 'total_tokens': 137, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 0}}
    #{'arguments': '{"question":"What diseases can hydroflumethiazide treat?","top_k":5}', 'name': 'sql'}
    #print(state["messages"][-3].additional_kwargs["tool_calls"][0]["function"]["arguments"])
    #question = json.loads(state["messages"][-3].additional_kwargs["tool_calls"][0]["function"]["arguments"])["question"]
    
    #pass

    def embeddings(document: str) -> list[float]:
        result = OpenAIEmbeddings(model=PARAM['vector_embedding_model']).embed_query(document)
        return result
    
    con = duckdb.connect(PARAM['drugdb_path'], config = {"allow_unsigned_extensions": "true"})
    con.create_function('embeddings', embeddings)

    

    for c in my_db_specifics.initialization_commands:
        #print (c)
        con.sql(c)

    # # Answer
    print ("question", question)
    print ("query", query)
    execute_result = con.sql(query).fetchall()
    #print ("execute_result", execute_result)
    
    
    final_response = ""
    if len(execute_result) == 0:
        final_response = "No results found."
    else:

        answer_prompt = PromptTemplate.from_template(
            """Given the Question {question} and the query_result {query_result}, format the results into sentences or a table for the human to understand. 
            Don't add any data or facts outside of the query_result. 
            Don't alter the quoted strings from the query_result even if they are not grammatically correct (no conversion of "inhibitors" to "inhibitor" and vice versa).
            """
        )

        formulate_human_readable_answer = (
        answer_prompt
        | llm
        | StrOutputParser()
        )

        final_response = formulate_human_readable_answer.invoke({"question": question, "query_result": execute_result})

    con.close()

    tool_call_id = ""
    for m in state["messages"][::-1]:
        print ("m", m.type, m)
        if m.type == "tool":
            tool_call_id = m.tool_call_id
            break
    #print ("in execute_query_and_answer tool_calls = state['messages'][-1].tool_calls", tool_calls[0]['id'])
    print ("return tool_call_id", tool_call_id)
    return {"messages": {"question": question, "query": query, "execute_result": execute_result, "role": "assistant", "content": final_response, "tool_call_id":tool_call_id}}
