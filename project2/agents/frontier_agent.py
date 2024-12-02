import os
import re
import math
import json
from typing import List, Dict,Optional
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from datasets import load_dataset
import chromadb
from items import JobDescription
#from testing import Tester
from agents.agent import Agent


class FrontierAgent(Agent):
    name = "Frontier Agent"
    color = Agent.BLUE

    MODEL = "gpt-4o-mini"
    
    SYSTEM_PROMPT = """
        You are a skilled career coach and interviewer. Your job is to provide the following 
        for any given job description:
        1. Job title.
        2. Responsibilities.
        3. Required skills.
        4. Three interview questions.
        5. Answers for those questions.
        6. Five preparation resources (including their titles and links).
        7. A clear list of key skills to focus on for excelling in this role.
        Respond strictly in JSON format.
    """

    
    
    USER_PROMPT = """
        Given the following job description, generate:
        1. Three interview questions tailored to the job description.
        2. Detailed answers for these questions, focusing on the required skills.
        3. Five preparation materials (e.g., articles, books, courses) with links to help candidates prepare.

        Job Description:
        

        Please respond in JSON format like this:
        {{
          "interview_questions": ["Question 1", "Question 2", "Question 3"],
          "answers": ["Answer for Question 1", "Answer for Question 2", "Answer for Question 3"],
          "resources": [
            {{"title": "Resource 1", "link": "https://example.com/resource1"}},
            {{"title": "Resource 2", "link": "https://example.com/resource2"}},
            {{"title": "Resource 3", "link": "https://example.com/resource3"}},
            {{"title": "Resource 4", "link": "https://example.com/resource4"}},
            {{"title": "Resource 5", "link": "https://example.com/resource5"}}
          ]
        }}
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
        user_prompt += self.USER_PROMPT
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
        similars = self.find_similars(description)
        try:
            response = self.openai.chat.completions.create(
                model=self.MODEL,
                messages=self.messages_for(description, similars),
                max_tokens=1000,
                temperature=0.7
            )
            raw_content = response.choices[0].message.content
            self.log(f"Received response from OpenAI: {raw_content[:100]}...")  # Log first 100 chars
    
            # Parse JSON response
            cleaned_content = raw_content.strip()
            if cleaned_content.startswith("```"):
                cleaned_content = cleaned_content.split("\n", 1)[1]
                cleaned_content = cleaned_content.rsplit("```", 1)[0]
    
            preparation_plan = json.loads(cleaned_content)
    
            # Ensure all required keys have valid data or defaults
            required_keys = {
                "job_title": "Unknown Title",
                "responsibilities": [],
                "required_skills": [],
                "interview_questions": [],
                "answers": [],
                "resources": [],
                "skills_to_focus": []
            }
            for key, default in required_keys.items():
                if key not in preparation_plan or not isinstance(preparation_plan[key], type(default)):
                    preparation_plan[key] = default
    
            # Fallback for `skills_to_focus`
            if not preparation_plan["skills_to_focus"] and preparation_plan["required_skills"]:
                self.log("Inferring `skills_to_focus` from `required_skills`.")
                preparation_plan["skills_to_focus"] = preparation_plan["required_skills"]
    
            return preparation_plan
    
        except json.JSONDecodeError as e:
            self.log(f"JSON parsing error: {e}")
            return {"error": "Failed to parse JSON response."}
        except Exception as e:
            self.log(f"Error during OpenAI call: {e}")
            return {"error": "API error."}
    def search_similar_jobs(self, query: str) -> List[Dict]:
        """
        Search the vector store for jobs similar to the query.
        :param query: User's search input (e.g., "Data Scientist").
        :return: List of similar job descriptions.
        """
        try:
            self.log(f"Searching vector store for jobs similar to: {query}")
            query_vector = self.model.encode([query])
            results = self.collection.query(query_embeddings=query_vector.tolist(), n_results=5)

            # Return structured job data
            jobs = []
            for doc in results["documents"][0]:
                job_data = json.loads(doc)  # Assuming job descriptions are stored as JSON strings
                jobs.append({
                    "job_title": job_data.get("job_title", "Unknown"),
                    "description": job_data.get("description", "No description available"),
                    "url": job_data.get("url", "No URL available")
                })
            return jobs

        except Exception as e:
            self.log(f"Error during job search: {e}")
            return []





           
        

   
    
            