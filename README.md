![flowDiagram](https://github.com/user-attachments/assets/5282a11f-1e0f-445f-b52d-22fef6a1af9e)
Job Aggregator Project
Overview
The Job Aggregator project is an autonomous agent-based framework designed to scrape, process, and provide actionable insights about job opportunities. The system leverages state-of-the-art AI, a vector database, and a combination of agents to find relevant jobs, generate interview preparation plans, and present them in an interactive user interface. Users can search for jobs, analyze opportunities, and prepare effectively for their desired roles using this platform.

Key Features
Search for Jobs: Users can type job titles or roles into the search bar, which triggers a search in the vector store and fetches similar jobs from the web.
Job Insights: The system generates detailed preparation plans, including:
Job title
Responsibilities
Required skills
Interview questions and answers
Recommended resources for preparation
Skills to focus on
Visualization: A 3D scatter plot visualizes job descriptions in a vectorized space for better understanding.
Autonomous Agents:
Scanner Agent: Scrapes and retrieves job descriptions from the web and vector store.
Frontier Agent: Processes job descriptions and creates preparation plans.
Planning Agent: Coordinates activities between agents.
Messaging Agent: Notifies users about results.
Gradio-based UI: Interactive interface for seamless user interaction and visualization.

Project Architecture
Workflow Diagram
The project follows a modular and agent-driven architecture:
*******************************************************************************************************************************************************************************************************************************************************************************
UI:
Built using Gradio.
Includes a search bar, logs, and a visualization plot.
Displays job preparation insights in a table.
Agent Framework:
Manages memory and logging.
Coordinates the activities of the agents.
Agents:
Scanner Agent:
Scrapes job descriptions from the web using RSS feeds or APIs.
Searches the vector store for relevant jobs based on user queries.
Frontier Agent:
Processes job descriptions to generate preparation plans using OpenAI.
Planning Agent:
Manages coordination between Scanner Agent, Frontier Agent, and Messaging Agent.
Messaging Agent:
Sends push notifications to users about job insights.
Vector Store:
Stores and manages job embeddings for fast and efficient search.
Powered by ChromaDB with persistent storage.
*****************************************************************************************************************************************************************************************************************************************************************************
Installation:
1.Clone the repository:
git clone https://github.com/your-repo/job-aggregator.git
cd job-aggregator

2.Create a virtual environment and activate it:
python3 -m venv env
source env/bin/activate

3.Install the dependencies:
pip install -r requirements.txt

4.Set up the .env file with necessary configurations:
OpenAI API key
ChromaDB database path
RSS feed URLs
api for messaging agent
*****************************************************************************************************************************************************************************************************************************************************************************
Code Structure

job-aggregator/
│
├── agents/                # Contains all agent classes
│   ├── scanner_agent.py   # Scrapes and searches jobs
│   ├── frontier_agent.py  # Processes job descriptions
│   ├── planning_agent.py  # Manages agent activities
│   ├── messaging_agent.py # Sends notifications to users
│
├── app.py                 # Main entry point for the application
├── job_agent_framework.py # Framework for managing agents and memory
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
└── .env                   # Environment variables for API keys and configs
*****************************************************************************************************************************************************************************************************************************************************************************

How it Works
Job Scraping:

The Scanner Agent fetches job data from RSS feeds and APIs.
User inputs in the search bar trigger additional searches in the vector store and web.
Processing Descriptions:

The Frontier Agent uses OpenAI to generate preparation insights.
Coordination:

The Planning Agent orchestrates activities between agents.
Insights are passed to the Messaging Agent for user notifications.
Visualization:

Vectorized job descriptions are plotted in 3D for a holistic view of the job market.

****************************************************************************************************************************************************************************************************************************************************************************
echnologies Used
Backend:
Python
OpenAI API
ChromaDB for vector search
Frontend:
Gradio for the interactive UI
Plotly for 3D scatter plots
AI Models:
Hugging Face’s sentence-transformers/all-MiniLM-L6-v2 for text embeddings
OpenAI GPT for generating job insights
Database:
Persistent vector storage with ChromaDB
Visualization:
t-SNE for dimensionality reduction
Plotly for 3D plotting
****************************************************************************************************************************************************************************************************************************************************************************

Future Enhancements
Additional Job Sources:
Integrate more APIs and feeds for diverse job opportunities.
Advanced Filters:
Add filters for location, job type, and salary range.
Enhanced Visualization:
Provide richer insights with category-based visual clusters.
****************************************************************************************************************************************************************************************************************************************************************************
