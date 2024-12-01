import os
import re
import math
import json
from typing import List, Dict
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from datasets import load_dataset
import chromadb
from items import JobDescription
#from testing import Tester
from agents.agent import Agent


class FrontierAgent:
    name = "Frontier Agent"
    color = "BLUE"

    MODEL = "gpt-4o-mini"

    SYSTEM_PROMPT = """
    You are an AI assistant that prepares interview strategies based on job descriptions. 
    Your output must include:
    1. Job Title
    2. Responsibilities
    3. Required Skills
    4. Preparation Strategy:
       - Topics to study
       - Recommended resources
    5. Interview Questions:
       - Technical questions with sample answers
       - Behavioral questions with sample answers
    Strictly respond in JSON
    """

    def __init__(self, collection):
        """
        Initialize the FrontierAgent by setting up OpenAI, Chroma Datastore, and Sentence Transformer.
        """
        self.log("Initializing Frontier Agent for job descriptions")
        self.openai = OpenAI()
        self.collection = collection
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.log("Frontier Agent is ready")

    def log(self, message: str):
        print(f"[LOG]: {message}")

    def make_context(self, similars: List[str]) -> str:
        """
        Create context using similar job descriptions to provide additional input for the prompt.
        :param similars: List of similar job descriptions.
        :return: Context string to include in the OpenAI prompt.
        """
        context = "Here are some similar job descriptions for context:\n\n"
        for similar in similars[:3]:
            context += f"Job Description:\n{similar}\n\n"
        return context

    def messages_for(self, description: str, similars: List[str]) -> List[Dict[str, str]]:
        """
        Construct the prompt with the job description and similar items.
        :param description: Job description to analyze.
        :param similars: List of similar job descriptions for context.
        :return: List of messages for the OpenAI chat.
        """
        system_message = self.SYSTEM_PROMPT
        user_prompt = self.make_context(similars)
        user_prompt += f"And now the input job description:\n\n{description}\n\n"
        user_prompt += (
            "Please provide jobtitle, responsibiity,required skills, preperation strategy and interview questions in JSON format"
        )
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ]

    def find_similars(self, description: str):
        """
        Find similar job descriptions using Chroma Datastore.
        :param description: Job description to query.
        :return: List of similar job descriptions.
        """
        try:
          self.log("Performing similarity search in Chroma datastore")
          vector = self.model.encode([description])
          results = self.collection.query(query_embeddings=vector.tolist(), n_results=5)
          documents = results['documents'][0][:]
          self.log("Found similar job descriptions")
          return documents
        except Exception as e:
          self.log(f"Error during similarity search: {e}")
          return []

    def prepare(self, description: str) -> Dict:
        """
        Generate an interview preparation plan for the given job description.
        """
        similars = self.find_similars(description)
        try:
            response = self.openai.chat.completions.create(
                model=self.MODEL,
                messages=self.messages_for(description, similars),
                max_tokens=1000
            )
            raw_content = response.choices[0].message.content
            self.log(f"Received response from OpenAI: {raw_content[:100]}...")  # Log first 100 chars
    
            # Parse JSON response
            try:
                result = json.loads(raw_content)  # Parse the string into a dictionary
            except json.JSONDecodeError as e:
                self.log(f"Error parsing JSON: {e}")
                return {"error": "Failed to parse JSON response from OpenAI."}
    
            # Enrich the result with additional fields (if needed)
            result["technical_questions"] = [
                {"question": "What is microservices architecture?", "answer": "Microservices architecture is ..."},
                {"question": "Explain load balancing.", "answer": "Load balancing is ..."}
            ]
            result["behavioral_questions"] = [
                {"question": "Describe a challenging project.", "answer": "One challenging project I worked on ..."}
            ]
            return result
        except Exception as e:
            self.log(f"Error during OpenAI call: {e}")
            return {"error": "Failed to generate preparation plan due to API error."}