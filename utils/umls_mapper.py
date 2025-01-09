#from openai import OpenAI
from typing import Set, Dict, List
import json
from pydantic import BaseModel
import yaml
import os
import utils.umls as umls
import utils.my_llm as my_llm
#import umls
#import umls as umls
#import my_llm as my_llm

#with open("../config.yaml", "r") as stream:
with open("config.yaml", "r") as stream:
    try:
        PARAM = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

# Set up your OpenAI API key
os.environ["OPENAI_API_KEY"] = PARAM['openai_api']

from typing import Set, Dict, List
from pydantic import BaseModel
import re

class MedicalTerms(BaseModel):
    drugs: List[str]
    disorders: List[str]
    mechanisms: List[str]

def term_extractor(question: str) -> Set[str]:
    """
    Extract only explicitly mentioned medical terms from a question.
    
    Args:
        question (str): The input question to analyze
        
    Returns:
        Set[str]: Set of extracted medical terms that are explicitly present in the input
    """

    print ("*****term_extractor question", question)
    try:
        # Define the function for term extraction
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "extract_medical_terms",
                    "description": "Extract ONLY the drugs, disorders, and mechanisms of action that are EXPLICITLY mentioned in the user input. DO NOT include any terms that aren't word-for-word present in the input.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drugs": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of drug names that appear verbatim in the text. Must be exact matches only."
                            },
                            "disorders": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of disorders or medical conditions that appear verbatim in the text. Must be exact matches only."
                            },
                            "mechanisms": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of mechanisms of action of drugs that appear verbatim in the text. Must be exact matches only."
                            }
                        },
                        "required": ["drugs", "disorders", "mechanisms"]
                    }
                }
            }
        ]

        # Call OpenAI API with function calling
        response = my_llm.client.chat.completions.create(
            model=my_llm.chat_deployment_name,
            messages=[
                {
                    "role": "system", 
                    "content": """You are a precise medical term extractor. Your ONLY job is to find terms that are explicitly written in the input text.
                    Rules:
                    1. NEVER suggest or infer terms that aren't explicitly present
                    2. Only extract exact matches - no synonyms or related terms
                    3. If you're unsure if something is a medical term, don't extract it
                    4. Ignore hypothetical or question words (e.g., "what drug" should not extract "drug")
                    5. Case-sensitive matching only
                    """
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "extract_medical_terms"}},
            temperature=0
        )
        
        # Extract and validate the terms
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            function_args = eval(tool_call.function.arguments)

            print ("function_args", function_args)
            
            # Additional validation: Only keep terms that are actually in the input
            validated_args = {
                'drugs': [term for term in function_args['drugs'] if term.lower() in question.lower()],
                'disorders': [term for term in function_args['disorders'] if term.lower() in question.lower()],
                'mechanisms': [term for term in function_args['mechanisms'] if term.lower() in question.lower()]
            }
            
            # Validate with Pydantic
            terms = MedicalTerms(**validated_args)
            
            # Combine all terms into a set
            terms_set = set()
            terms_set.update(terms.drugs)
            terms_set.update(terms.disorders)
            terms_set.update(terms.mechanisms)
            
            return terms_set
        
        return set()
            
    except Exception as e:
        print(f"Error in term extraction: {e}")
        return set()


def entity_recognition(terms: Set[str]):
    results = {}

    try:
      for term in terms:
          # Call UMLS API for each term
          umls_results = umls.search(term, umls_token=PARAM["umls_token"], amount_of_results=1)

          if umls_results:
              results[term] = {"name": umls_results[0]["name"], "cui": umls_results[0]["cui"]}
    except Exception as e:
        print(f"Error in UMLS entity recognition: {e}")
    return results
    
def expand_question(original_question: str, terms: Dict[str, str]) -> str:
    """
    Expand the original question with the extracted medical terms.
    
    Args:
        original_question (str): The original question
        terms (Set[str]): Set of extracted medical terms
        
    Returns:
        str: The expanded question
    """
    expanded_question = original_question
    
    for term in terms:
        expanded_question = expanded_question.replace(term, f"{term} ({{UMLS_name: \"{terms[term]['name']}\", CUI: \"{terms[term]['cui']}\"}})")
        
    return expanded_question

# Example usage
if __name__ == "__main__":

    
    # # Replace with your actual OpenAI API key
    
    # # Test with sample questions
    # for question in sample_questions:
    #     print("\nQuestion:", question)
    #     terms = term_extractor(question)
    #     print("Extracted terms:", terms)

  question = "What drug may treat type 2 diabetes? Give me 5 results"

  terms = term_extractor(question)
  print ("terms", terms)

  umls_terms = entity_recognition(terms)
  print ("umls_terms", umls_terms)

  # Expand the question with UMLS terms
  expanded_question = expand_question(question, umls_terms)

  print ("expanded_question", expanded_question)