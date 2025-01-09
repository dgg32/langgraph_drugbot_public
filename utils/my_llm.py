# import yaml
# from langchain_openai import ChatOpenAI
# import os

# with open("config.yaml", "r") as stream:
#     try:
#         PARAM = yaml.safe_load(stream)
#     except yaml.YAMLError as exc:
#         print(exc)

# # Set up your OpenAI API key
# os.environ["OPENAI_API_KEY"] = PARAM['openai_api']
# llm = ChatOpenAI(model_name="gpt-4o-mini")

import yaml
from langchain_openai import AzureChatOpenAI
from openai import AzureOpenAI
from langchain_openai import AzureOpenAIEmbeddings


#with open("../config.yaml", "r") as stream:
with open("config.yaml", "r") as stream:
    try:
        PARAM = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

# settings
base_url = PARAM['azure_base_url']
api_version = PARAM['azure_api_version']
llm_key = PARAM['azure_key']
chat_deployment_name = 'explore'
embeddings_deployment_name = 'embeddings'
embeddings_api_version = 'api_version'


embeddings = AzureOpenAIEmbeddings(
    model="text-embedding-3-small",
    azure_endpoint="https://geminidata-enterprise.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2023-05-15",
    #openai_api_version=embeddings_api_version,
    api_key = llm_key
)

llm=AzureChatOpenAI(
  azure_endpoint=base_url, 
  deployment_name=chat_deployment_name,
  api_version=api_version,
  api_key=llm_key)


client = AzureOpenAI(
            azure_endpoint=base_url,
            api_key=llm_key,
            api_version=api_version
        )