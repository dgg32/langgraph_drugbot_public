import autoevals
import os
import yaml
import braintrust
from openai import AsyncOpenAI

from braintrust import EvalAsync


with open("../config.yaml", "r") as stream:
    try:
        PARAM = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

os.environ["OPENAI_API_KEY"] = PARAM['openai_api']

braintrust.login(api_key=PARAM["BRAINTRUST_API_KEY"])


PROMPT = """\
You are comparing a submitted answer to an expert answer on a given question. Here is the data:
[BEGIN DATA]
************
[Question]: {{input}}
************
[Expert]: {{expected}}
************
[Chatbot_output]: {{output}}
************
[END DATA]
 
Compare the factual content of the submitted answer with the expert answer. Ignore any differences in style, grammar, or punctuation.
The submitted answer may either be a subset or superset of the expert answer, or it may conflict with it. Determine which case applies. Answer the question by selecting one of the following options:
(A) The submitted answer is a subset of the expert answer and is fully consistent with it.
(B) The submitted answer is a superset of the expert answer and is fully consistent with it.
(C) The submitted answer contains all the same details as the expert answer.
(D) There is a disagreement between the submitted answer and the expert answer.
(E) The answers differ, but these differences don't matter from the perspective of factuality.
 
Answer the question by calling `select_choice` with your reasoning in a step-by-step matter to be
sure that your conclusion is correct. Avoid simply stating the correct answer at the outset. Select a
single choice by setting the `choice` parameter to a single choice from A, B, C, D, or E.
"""
 
llm_classifier = autoevals.LLMClassifier(
    name="Chatbot evaluator",
    prompt_template=PROMPT,
    choice_scores={"A": 0.5, "B": 1, "C": 1, "D": 0, "E": 1},
    use_cot=True,
)

async def task(input):
    return await llm_classifier.eval_async(
        input=input["question"],
        output=input["generated_answer"],
        expected=input["expected_answer"],
    )


def five_grader(output):
    return abs(output.score)



async def run(qa_set, metadata={}):
  def data():
    for one_set in qa_set:
        yield dict(
            input=one_set, expected=0
        )
  

  await EvalAsync(
      "LLM-as-a-judge",
      data=data,
      task=task,
      scores=[five_grader],
      experiment_name="Classifier",
      max_concurrency=10,
      metadata=metadata,
  )