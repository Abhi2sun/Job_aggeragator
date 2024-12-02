from pydantic import BaseModel
from typing import List, Dict, Tuple
from bs4 import BeautifulSoup
import re
import feedparser
from tqdm import tqdm
import requests
import time
import logging
from typing import Optional, List,Self

# Configure logging for error reporting
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RSS Feed URLs for job descriptions
feeds = [
    
   "https://remotive.com/remote-jobs/software-dev/senior-independent-software-developer-1919265",
    "https://www.freelancer.com/rss.xml",
    "https://remoteok.com/remote-jobs.rss",
    "https://www.simplyhired.com/search?q=data&l="
    
]
# Utility to clean and extract text
def extract(html_snippet: str) -> str:
    """
    Use Beautiful Soup to clean up this HTML snippet and extract useful text
    """
    soup = BeautifulSoup(html_snippet, 'html.parser')
    snippet_div = soup.find('div', class_='snippet summary')
    
    if snippet_div:
        description = snippet_div.get_text(strip=True)
        description = BeautifulSoup(description, 'html.parser').get_text()
        description = re.sub('<[^<]+?>', '', description)
        result = description.strip()
    else:
        result = html_snippet
    return result.replace('\n', ' ')

class ScrapedJobDescription:
    """
    A class to represent a Job Description retrieved from an RSS feed or API.
    """
    job_title: str
    company: str
    location: str
    summary: str
    url: str
    responsibilities: str
    skills: str

    def __init__(self, entry: Dict[str, str]):
        """
        Populate this instance based on the provided RSS entry.
        """
        self.job_title = entry.get("title", "Unknown Title")
        self.company = entry.get("company", "Unknown Company")
        self.location = entry.get("location", "Unknown Location")
        self.summary = extract(entry.get("summary", ""))
        self.url =  entry.get("links", [{}])[0].get("href", "URL Not Available")
        self.responsibilities = "Responsibilities not available"
        self.skills = "Skills not available"

        try:
            job_page = requests.get(self.url, timeout=5).content
            soup = BeautifulSoup(job_page, "html.parser")
            content = soup.find("div", class_="job-content").get_text(separator="\n").strip()
            self.responsibilities, self.skills = self.parse_content(content)
        except Exception as e:
            logger.error(f"Error parsing job page: {e}")

    def parse_content(self, content: str) -> Tuple[str, str]:
        """
        Parse the job content to extract responsibilities and skills.
        """
        try:
            if "Responsibilities" in content and "Required Skills" in content:
                responsibilities, skills = content.split("Required Skills", 1)
                return responsibilities.strip(), skills.strip()
            elif "Responsibilities" in content:
                return content, "Skills not specified"
            return "Responsibilities not specified", "Skills not specified"
        except Exception as e:
            logger.error(f"Error splitting content: {e}")
            return "Responsibilities not specified", "Skills not specified"

    def __repr__(self):
        return f"<{self.job_title} at {self.company}>"

    def describe(self):
        return f"Title: {self.job_title}\nCompany: {self.company}\nLocation: {self.location}\nSummary: {self.summary}\nURL: {self.url}"

    @classmethod
    def fetch(cls, show_progress: bool = False) -> List[Self]:
        """
        Retrieve all job descriptions from the selected RSS feeds or APIs.
        """
        jobs = []
        feed_iter = tqdm(feeds) if show_progress else feeds
        for feed_url in feed_iter:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]:  # Fetch a maximum of 10 jobs per feed
                    jobs.append(cls(entry))
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error fetching feed {feed_url}: {e}")
        return jobs

# Models for structured output
class Job(BaseModel):
    """
    A class to represent a Job Description with structured fields.
    """
    description: str
    job_title: str
    company: str
    location: str
    responsibilities: str
    skills: List[str]
    url: str
    prep_questions: Optional[List[str]] = None  # Add this field

class JobSelection(BaseModel):
    """
    A class to represent a selection of Job Descriptions.
    """
    jobs: List[Job]

class InterviewPreparation(BaseModel):
    """
    A class to represent interview preparation details for a specific job.
    """
    job: Job
    job_title: str
    skills_to_focus: List[str]
    technical_questions: List[str]
    technical_answers: List[str]
    behavioral_questions: List[str]
    behavioral_answers: List[str]
    resources: List[str]  # URLs or books for further preparation
