import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
# load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Model configurations
GEMINI_MODEL_FLASH = 'gemini-1.5-flash'
GEMINI_MODEL_PRO = 'gemini-1.5-pro'

# Search configurations
MAX_RESULTS = {
    'last 7 days': 3,
    'last 30 days': 10,
    'last 365 days': 20
}

# Cache configurations
CACHE_EXPIRATION = 3600  # 1 hour in seconds

# FastAPI configurations
API_HOST = '127.0.0.1'
API_PORT = 8000

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# Prompt templates
ABSTRACT_RATING_PROMPT = """Rate the potential impact of this research paper on a scale of 1 to 100 based on the following information:
Title: {title}
Abstract: {abstract}
Citations: {citations}
Social Media Mentions: {social_mentions}

Provide only the numeric rating (1-100) without any explanation and 3 relevant keywords in this format: <number>,<keyword1>,<keyword2>,<keyword3>"""

PAPER_SUMMARY_PROMPT = """<System> You are a experienced research analyst across multiple scientific disciplines.
You can explain advanced topics in detail that even high school student can understand.
You are very critical in examining papers, especially papers that is intentionally made for buzz word or attention-seeking purpose with no substance.
Meticulously examine and break down research papers, providing a comprehensive analysis and identifying key information, along with a rating.
only provide methodology, content rating and rating explanation AND DO NOT ADD ANYTHING ELSE.
</System>

<Task> Focus on methodology and results. Analyze and summarize the following research paper strictly based on the instruction and ALWAYS display in bullet points. </Task>

<Instruction> Start with this sentence: 'Here is a breakdown of the research paper '_paper_name_' in bullet points:'.
Title: {title}
Abstract: {abstract}
Full Text: {full_text}

Format the response as a bulleted list for each section.:
1. Methodology (2-3 sentences in bullet points):
- Describe the addressed issue
- Describe the research design to solve the issue, beware of Contextual Significance.
- Evaluate the appropriateness and reliability of the chosen methodology, as well as identify any potential flaws or weaknesses in the study design or execution.

2. Content Rating: Provide a number assessment based on the comprehensiveness of methodology, potential gaps or biases and finidngs (can be found in abstract above):
- 80-100: Major impact
- 65-79: Good impact
- 51-64: Moderate to Limited impact
- Below 50: Below standard impact

3. Rating Explanation (1-2 sentences in bullet points):
- Provide a brief explanation for your impact rating by.

4. Key Finding (2-3 sentences in bullet points):
- Highlight any statistical significance and effect sizes reported.
- Evaluate the completeness of the results in addressing all research questions/hypotheses.

5. Potential improvement (1-2 sentences in bullet points):
- Identify any unanswered questions or areas requiring further investigation.
</Instruction>"""