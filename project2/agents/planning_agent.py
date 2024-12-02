import json
import logging
from typing import List
from agents.agent import Agent
from agents.jobs import Job, JobSelection, InterviewPreparation
from agents.scanner import ScannerAgent
from agents.frontier_agent import FrontierAgent
from agents.messaging_agent import MessagingAgent
import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib
import json
from typing import Optional, List
from agents.agent import Agent
from agents.jobs import ScrapedJobDescription, JobSelection,Job,InterviewPreparation,Job
from agents.scanner import ScannerAgent
from agents.frontier_agent import FrontierAgent
from agents.messaging_agent import MessagingAgent


class PlanningAgent(Agent):
    name = "Planning Agent"
    color = Agent.GREEN

    def __init__(self, collection):
        self.scanner = ScannerAgent()
        self.preparer = FrontierAgent(collection)
        self.messenger = MessagingAgent()
        self.logger = logging.getLogger(__name__)

    def log(self, message: str):
        """Logs a message to the console."""
        self.logger.info(f"[Planning Agent]: {message}")

    def analyze_job(self, job: Job) -> Optional[InterviewPreparation]:
        self.log(f"Analyzing job: {job.job_title}")
    
        try:
            # Generate preparation plan using FrontierAgent
            preparation_plan = self.preparer.prepare(job.description)
    
            if "error" in preparation_plan:
                self.log(f"Error in preparation plan: {preparation_plan['error']}")
                return None
    
            # Extract fields from FrontierAgent's response
            job_title = preparation_plan.get("job_title", job.job_title or "Unknown Title")
            if isinstance(job_title, list):  # Ensure job_title is a string
                job_title = job_title[0] if job_title else "Unknown Title"
    
            interview_questions = preparation_plan.get("interview_questions", [])
            answers = preparation_plan.get("answers", [])
    
            # Handle the resources field
            resources = preparation_plan.get("resources", [])
            if isinstance(resources, list):
                resources = [
                    resource.get("link", "")
                    for resource in resources
                    if isinstance(resource, dict) and "link" in resource
                ]
            else:
                resources = []  # Default to an empty list if malformed
    
            # Handle skills_to_focus
            skills_to_focus = preparation_plan.get("skills_to_focus", [])
            if not isinstance(skills_to_focus, list):  # Default to an empty list if malformed
                skills_to_focus = []
    
            return InterviewPreparation(
                job=job,
                job_title=job_title,
                skills_to_focus=skills_to_focus,
                technical_questions=interview_questions,
                technical_answers=answers,
                behavioral_questions=[],  # Add if required
                behavioral_answers=[],   # Add if required
                resources=resources
            )
        except Exception as e:
            self.log(f"Error analyzing job: {e}")
            return None
    



    def plan(self, memory: List[Job]) -> Optional[InterviewPreparation]:
        """Full planning workflow."""
        self.log("Starting planning workflow.")
        selection = self.scanner.scan(memory)

        if not selection:
            self.log("No new jobs found.")
            return None

        interview_preps = []
        for job in selection.jobs[:5]:  # Process a maximum of 5 jobs
            prep = self.analyze_job(job)
            if prep:
                interview_preps.append(prep)

        if not interview_preps:
            self.log("No valid interview preparations could be generated.")
            return None

        best = interview_preps[0]  # Use the first valid preparation
        self.messenger.alert(best)
        return best



                            

       