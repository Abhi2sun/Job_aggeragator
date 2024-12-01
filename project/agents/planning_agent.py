import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

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
        """
        Create instances of the agents that this planner coordinates across.
        """
        self.log("Planning Agent is initializing")
        self.scanner = ScannerAgent()
        self.preparer = FrontierAgent(collection)
        self.messenger = MessagingAgent()
        self.log("Planning Agent is ready")

    def analyze_job(self, job: Job) -> dict:
        """
        Run the workflow for a particular job description.
        :param job: A job description object.
        :return: A dictionary containing the preparation strategy and questions.
        """
        self.log(f"Planning Agent is preparing for job: {job.job_title}")
        preparation_plan = self.preparer.prepare(job.description)
        self.log(f"Planning Agent completed preparation for: {job.job_title}")
        return preparation_plan

    def plan(self, memory: List[str] = []) -> Optional[dict]:
        """
        Run the full workflow:
        1. Use the ScannerAgent to find job descriptions.
        2. Use the InterviewPreparationAgent to generate preparation plans.
        3. Use the MessagingAgent to send notifications about the preparation plan.
        :param memory: A list of URLs for jobs already processed.
        :return: A preparation plan for the most relevant job, or None if no jobs are found.
        """
        self.log("Planning Agent is starting a new run")

        # Step 1: Scan for new job descriptions
        selection = self.scanner.scan(memory=memory)
        if not selection or not selection.jobs:
            self.log("No new job descriptions found")
            return None

        # Step 2: Prepare for the best job in the selection
        best_job = selection.jobs[0]  # Assuming the first job is the most relevant
        preparation_plan = self.analyze_job(best_job)

        # Step 3: Notify the user
        if preparation_plan:
            self.messenger.alert(preparation_plan)
        self.log("Planning Agent has completed a run")
        return preparation_plan