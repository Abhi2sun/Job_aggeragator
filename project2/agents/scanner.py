import os
import json
from typing import Optional, List
from openai import OpenAI
from agents.jobs import ScrapedJobDescription, JobSelection, Job

import logging


import os
import json
from typing import Optional, List
from openai import OpenAI

from agents.agent import Agent


class ScannerAgent(Agent):
    MODEL = "gpt-4o-mini"

    SYSTEM_PROMPT = """You identify and summarize the 5 most detailed job descriptions from a list, focusing on the most detailed responsibilities, required skills, and meaningful job titles. Respond strictly in JSON with no explanation, using this format:
    
    {
      "jobs": [
        {
          "job_title": "Extracted job title",
          "responsibilities": "Detailed responsibilities",
          "required_skills": ["Skill1", "Skill2"],
          "prep_questions": ["Question1", "Question2", "Question3"],
          "url": "Job URL"
        },
        ...
      ]
    }
    
    The most important factor is the quality and clarity of responsibilities and skills. Do not include vague or generic jobs. Focus on technical and specific roles with clear descriptions.
    """

    USER_PROMPT_PREFIX = """Respond with the 5 most detailed job descriptions, focusing on:
    - Specific responsibilities (minimum 2 sentences)
    - Clearly listed required skills (minimum 2 skills)
    - Generate 3 interview preparation questions for each job.
    
    Respond strictly in JSON and ensure all jobs include:
    - Job title
    - Responsibilities
    - Required skills
    - Prep questions
    - URL
    
    Job Descriptions:
    """

    USER_PROMPT_SUFFIX = "\n\nStrictly respond in JSON with up to 5 jobs."

    name = "Job Scanner Agent"
    color = Agent.CYAN

    def __init__(self):
        """
        Initialize the Job Scanner Agent by setting up OpenAI.
        """
        self.log("Job Scanner Agent is initializing")
        self.openai = OpenAI()
        self.log("Job Scanner Agent is ready")

    def fetch_jobs(self, memory) -> List[ScrapedJobDescription]:
        """
        Fetch new job postings, excluding those already in memory.
        """
        self.log("Job Scanner Agent is about to fetch job descriptions")
        urls = [job.job.url for job in memory]
        scraped = ScrapedJobDescription.fetch()  # Replace with your actual scraping logic
        new_jobs = [job for job in scraped if job.url not in urls]
        self.log(f"Job Scanner Agent received {len(new_jobs)} new jobs not already processed")
        return new_jobs

    def make_user_prompt(self, scraped) -> str:
        """
        Create a user prompt for OpenAI based on scraped job descriptions.
        """
        user_prompt = self.USER_PROMPT_PREFIX
        user_prompt += '\n\n'.join([job.describe() for job in scraped])
        user_prompt += self.USER_PROMPT_SUFFIX
        return user_prompt

    def scan(self, memory: List[str] = []) -> Optional[JobSelection]:
        """
        Call OpenAI to process job descriptions and return the most promising ones.
        """
        scraped = self.fetch_jobs(memory)
        if scraped:
            user_prompt = self.make_user_prompt(scraped)
            self.log("Job Scanner Agent is calling OpenAI for job selection")
            
            result = self.openai.beta.chat.completions.parse(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=JobSelection
            )
            result = result.choices[0].message.parsed
            result.jobs=[job for job in result.jobs if len(job.description)>50]
            self.log(f"Job Scanner Agent received {len(result.jobs)} selected jobs from OpenAI")
            return result
        else:
            self.log("No new jobs found to process")
        return None

