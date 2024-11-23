import json
import wandb
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime
from langchain.chat_models import ChatOpenAI
from langgraph.graph import Graph
import yaml
from tqdm import tqdm

class DBChatbotEvaluator:
    def __init__(self, config_path: str):
        """
        Initialize the evaluator with configuration.
        
        Args:
            config_path: Path to YAML configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # Initialize LLMs
        self.judge_llm = ChatOpenAI(
            model_name=self.config['judge_model'],
            temperature=0.1
        )
        
        # Initialize W&B
        wandb.init(
            project=self.config['wandb_project'],
            config=self.config
        )
        
        # Initialize the database chatbot
        self.db_chatbot = self._initialize_chatbot()
        
    def _initialize_chatbot(self) -> Graph:
        """Initialize the LangGraph chatbot"""
        # This should be implemented based on your specific LangGraph setup
        # Return your configured LangGraph chatbot
        pass
        
    def _read_test_cases(self, filepath: str) -> List[Dict]:
        """
        Read test cases from input file.
        
        Args:
            filepath: Path to test cases file
            
        Returns:
            List of dictionaries containing questions and expected answers
        """
        with open(filepath, 'r') as f:
            test_cases = json.load(f)
        return test_cases
        
    def _evaluate_response(self, 
                          question: str, 
                          expected_answer: str, 
                          bot_response: str, 
                          final_query: str) -> Dict:
        """
        Use LLM to evaluate the bot's response.
        
        Args:
            question: Original question
            expected_answer: Ground truth answer
            bot_response: Bot's response
            final_query: Final SQL query used
            
        Returns:
            Dictionary containing evaluation metrics
        """
        prompt = f"""
        Please evaluate the database chatbot's response against the expected answer.
        
        Question: {question}
        Expected Answer: {expected_answer}
        Bot's Response: {bot_response}
        Final Query: {final_query}
        
        Evaluate the following aspects on a scale of 1-10:
        1. Answer Correctness: How accurately does the response match the expected answer?
        2. Query Relevance: How well does the final SQL query match the question's intent?
        3. Response Completeness: Does the response address all aspects of the question?
        4. Natural Language Quality: How clear and well-formatted is the response?
        
        Provide your evaluation in JSON format with these metrics and a brief explanation for each score.
        """
        
        evaluation = self.judge_llm.predict(prompt)
        try:
            metrics = json.loads(evaluation)
        except json.JSONDecodeError:
            # Fallback if LLM doesn't provide valid JSON
            metrics = {
                "answer_correctness": 0,
                "query_relevance": 0,
                "response_completeness": 0,
                "natural_language_quality": 0,
                "explanation": "Failed to parse LLM evaluation"
            }
            
        return metrics
        
    def run_evaluation(self, test_cases_path: str) -> pd.DataFrame:
        """
        Run the evaluation pipeline.
        
        Args:
            test_cases_path: Path to test cases file
            
        Returns:
            DataFrame containing evaluation results
        """
        test_cases = self._read_test_cases(test_cases_path)
        results = []
        
        for case in tqdm(test_cases, desc="Evaluating test cases"):
            # Get bot response
            bot_result = self.db_chatbot.run(case['question'])
            bot_response = bot_result['response']
            final_query = bot_result['final_query']
            
            # Evaluate response
            evaluation = self._evaluate_response(
                question=case['question'],
                expected_answer=case['expected_answer'],
                bot_response=bot_response,
                final_query=final_query
            )
            
            # Calculate aggregate score
            aggregate_score = sum([
                evaluation['answer_correctness'] * 0.4,
                evaluation['query_relevance'] * 0.25,
                evaluation['response_completeness'] * 0.2,
                evaluation['natural_language_quality'] * 0.15
            ])
            
            # Prepare result entry
            result = {
                'question': case['question'],
                'expected_answer': case['expected_answer'],
                'bot_response': bot_response,
                'final_query': final_query,
                'aggregate_score': aggregate_score,
                **evaluation
            }
            
            # Log to W&B
            wandb.log({
                'aggregate_score': aggregate_score,
                'answer_correctness': evaluation['answer_correctness'],
                'query_relevance': evaluation['query_relevance'],
                'response_completeness': evaluation['response_completeness'],
                'natural_language_quality': evaluation['natural_language_quality']
            })
            
            results.append(result)
            
        # Create DataFrame
        results_df = pd.DataFrame(results)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_df.to_csv(f'evaluation_results_{timestamp}.csv', index=False)
        wandb.save(f'evaluation_results_{timestamp}.csv')
        
        return results_df
        
    def generate_summary_report(self, results_df: pd.DataFrame) -> None:
        """
        Generate and log summary report to W&B.
        
        Args:
            results_df: DataFrame containing evaluation results
        """
        summary = {
            'total_questions': len(results_df),
            'average_aggregate_score': results_df['aggregate_score'].mean(),
            'score_distribution': results_df['aggregate_score'].describe().to_dict(),
            'metric_averages': {
                'answer_correctness': results_df['answer_correctness'].mean(),
                'query_relevance': results_df['query_relevance'].mean(),
                'response_completeness': results_df['response_completeness'].mean(),
                'natural_language_quality': results_df['natural_language_quality'].mean()
            }
        }
        
        wandb.log({'summary': summary})
        
        # Create visualizations
        fig = wandb.plot.histogram(
            results_df['aggregate_score'].values,
            title='Distribution of Aggregate Scores'
        )
        wandb.log({'score_distribution': fig})

if __name__ == "__main__":
    # Example usage
    config_path = "config.yaml"
    test_cases_path = "test_cases.json"
    
    evaluator = DBChatbotEvaluator(config_path)
    results = evaluator.run_evaluation(test_cases_path)
    evaluator.generate_summary_report(results)