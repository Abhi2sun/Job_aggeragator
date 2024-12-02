from transformers import AutoTokenizer
import re
from typing import Optional, List

BASE_MODEL = "meta-llama/Meta-Llama-3.1-8B"
MIN_TOKENS = 10
MAX_TOKENS = 150
MIN_CHARS = 200
CEILING_CHARS = MAX_TOKENS * 7


class JobDescription:
    """
    A class to clean, tokenize, and prepare job descriptions for training and testing.
    """
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    #print(f"Tokenizerr: {tokenizer}")

    PROMPT_TEMPLATE = """
    Analyze the following job description and extract:
    1. Job Title
    2. Responsibilities
    3. Required Skills
    4. Recommended Preparation Topics
    5. Interview Questions (Technical and Behavioral)

    Job Description:
    {description}
    """

    def __init__(self, data: dict):
        self.job_title = data.get('job_title', 'Unknown Title')
        self.description = data.get('description', '')
        self.requirements = data.get('requirements', '')
        self.skills = data.get('skills', [])
        self.include = False
        self.token_count = 0
        self.prompt = None

        # Parse and preprocess the data 
        self.parse(data)

    def scrub(self, text: str) -> str:
        """
        Clean up text by removing extra characters and spaces.
        """
        text = re.sub(r'[^\w\s,]', '', text).strip()  # Remove special characters except commas
        text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
        return text

    def parse(self, data: dict):
        """
        Parse the input data and prepare the prompt.
        """
        # Combine description, requirements, and skills
        contents = self.scrub(data.get('description', '')) + '\n'
        requirements = self.scrub(data.get('requirements', ''))
        if requirements:
            contents += requirements + '\n'
        skills = ', '.join(data.get('skills', []))
        if skills:
            contents += f"Skills: {skills}\n"

        # Debugging: Check content length
        print(f"Content Length: {len(contents)}")
        if len(contents) > MIN_CHARS:
            contents = contents[:CEILING_CHARS]
            tokens = self.tokenizer.encode(contents, add_special_tokens=False)
            print(f"Token Count: {len(tokens)}")  # Debugging token count
            if len(tokens) > MIN_TOKENS:
                tokens = tokens[:MAX_TOKENS]
                text = self.tokenizer.decode(tokens)
                self.make_prompt(text)  # Call make_prompt
                self.include = True
            else:
                print(f"Token count below minimum: {len(tokens)}")
        else:
            print(f"Content length below minimum: {len(contents)}")

    def make_prompt(self, text: str):
        """
        Set the prompt instance variable to be a prompt appropriate for training.
        """
        self.prompt = self.PROMPT_TEMPLATE.format(description=text)
        self.token_count = len(self.tokenizer.encode(self.prompt, add_special_tokens=False))
        print(f"Prompt set: {self.prompt}")  # Debug: Print the prompt

    def __repr__(self):
        """
        Return a string representation of the job description.
        """
        return f"<JobDescription: {self.job_title}>"



