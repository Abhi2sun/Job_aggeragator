import os
import sys
import logging
import json
from typing import List, Optional
from dotenv import load_dotenv
import chromadb
from agents.planning_agent import PlanningAgent
from agents.jobs import JobSelection, Job, InterviewPreparation
from sklearn.manifold import TSNE
import numpy as np
from agents.jobs import Job
from matplotlib import cm
from matplotlib.colors import to_hex
import os
import sys
import logging
import json
from typing import List
from dotenv import load_dotenv
from chromadb import PersistentClient
from agents.planning_agent import PlanningAgent
from agents.jobs import Job, InterviewPreparation
import numpy as np
from sklearn.manifold import TSNE
import plotly.graph_objects as go

# Constants for logging and visualization
BG_BLUE = '\033[44m'
WHITE = '\033[37m'
RESET = '\033[0m'

CATEGORIES = ['Software Development', 'Data Science', 'Mobile Development', 'Web Development', 
              'DevOps', 'Management', 'UI/UX Design', 'Other']
COLORS = ['blue', 'green', 'red', 'purple', 'orange', 'yellow', 'brown', 'gray']


def init_logging():
    """Initialize logging for the framework."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] [Agents] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)


class JobAgentFramework:
    """
    Main framework for managing job agents, including memory storage and task execution.
    """

    DB = "jobs_vectorstore"  # Path to persistent database
    MEMORY_FILENAME = "job_memory.json"  # File to persist memory across runs

    def __init__(self):
        init_logging()
        load_dotenv()  # Load environment variables (e.g., API keys)
        self.client = PersistentClient(path=self.DB)
        self.memory = self._read_memory()
        self.collection = self.client.get_or_create_collection('Job_desc')
        self.planner = None

    def _read_memory(self) -> List[Job]:
        """
        Load previously processed jobs from persistent storage.
        """
        if os.path.exists(self.MEMORY_FILENAME):
            with open(self.MEMORY_FILENAME, "r") as file:
                data = json.load(file)
            return [InterviewPreparation(**item) for item in data]
        return []

    def _write_memory(self):
        """
        Persist current memory state to disk.
        """
        data = [job.dict() for job in self.memory]
        with open(self.MEMORY_FILENAME, "w") as file:
            json.dump(data, file, indent=2)

    def _log(self, message: str):
        """Log a message with a specific format."""
        text = BG_BLUE + WHITE + "[Job Agent Framework] " + message + RESET
        logging.info(text)

    def _init_planner(self):
        """
        Lazily initialize the PlanningAgent to avoid circular imports.
        """
        if not self.planner:
            self._log("Initializing PlanningAgent")
            from agents.planning_agent import PlanningAgent
            self.planner = PlanningAgent(self.collection)
            self._log("PlanningAgent is ready")

    def run(self):
        """
        Execute the main framework logic, invoking the planner to process jobs.
        """
        self._init_planner()
        self._log("Starting PlanningAgent...")
        result = self.planner.plan(memory=self.memory)
        self._log(f"PlanningAgent returned: {result}")
        if result:
            self.memory.append(result)
            self._write_memory()
        return self.memory

    @staticmethod
    def get_plot_data(max_datapoints=10000):
        """
        Retrieve data for visualization from the vectorstore.
        """
        client = PersistentClient(path=JobAgentFramework.DB)
        collection = client.get_or_create_collection('Job_desc')
        result = collection.get(include=['embeddings', 'documents', 'metadatas'], limit=max_datapoints)
        vectors = np.array(result['embeddings'])
        documents = result['documents']
        categories = [metadata.get('category', 'Other') for metadata in result['metadatas']]
        unique_categories = list(set(categories))
        colormap = cm.get_cmap('tab20', len(unique_categories))
        category_to_color = {category: to_hex(colormap(i)) for i, category in enumerate(unique_categories)}
        colors = [category_to_color[category] for category in categories]

        # TSNE dimensionality reduction
        tsne = TSNE(n_components=3, random_state=42, n_jobs=-1)
        reduced_vectors = tsne.fit_transform(vectors)
        return documents, reduced_vectors, colors

    @staticmethod
    def visualize(max_datapoints=10000):
        """
        Visualize job data in a 2D scatter plot.
        """
        documents, reduced_vectors, colors = JobAgentFramework.get_plot_data(max_datapoints)
        fig = go.Figure(data=[go.Scatter(
            x=reduced_vectors[:, 0],
            y=reduced_vectors[:, 1],
            mode='markers',
            marker=dict(size=5, color=colors, opacity=0.7),
            text=documents
        )])

        fig.update_layout(
            title='2D Visualization of Job Descriptions',
            xaxis_title='TSNE Dimension 1',
            yaxis_title='TSNE Dimension 2',
            width=1200,
            height=800,
            margin=dict(r=20, b=10, l=10, t=40),
            showlegend=False
        )
        fig.show()


if __name__ == "__main__":
    framework = JobAgentFramework()
    framework.run()
    JobAgentFramework.visualize()


