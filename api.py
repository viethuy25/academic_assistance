import google.generativeai as genai
import arxiv
from aiohttp import ClientSession
from config import GEMINI_API_KEY, GEMINI_MODEL_FLASH, GEMINI_MODEL_PRO

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model_flash = genai.GenerativeModel(GEMINI_MODEL_FLASH)
model_pro = genai.GenerativeModel(GEMINI_MODEL_PRO)

async def fetch_url(session: ClientSession, url: str) -> str:
    async with session.get(url) as response:
        return await response.text()

async def get_arxiv_paper(arxiv_id: str) -> arxiv.Result:
    client = arxiv.Client()
    search = arxiv.Search(id_list=[arxiv_id])
    results = list(client.results(search))
    if results:
        return results[0]
    raise ValueError(f"No paper found with arXiv ID: {arxiv_id}")

async def get_social_media_mentions(session: ClientSession, title: str) -> int:
    # Placeholder function - replace with actual implementation
    return 0

async def get_google_scholar_data(session: ClientSession, title: str, authors: list) -> tuple:
    # Placeholder function - replace with actual implementation
    return 0, 0

def generate_flash_content(prompt: str) -> str:
    response = model_flash.generate_content(prompt)
    return response.text

def generate_flash_content_stream(prompt: str):
    response = model_flash.generate_content(prompt, stream=True)
    for chunk in response:
        yield chunk.text

def generate_pro_content(prompt: str):
    response = model_pro.generate_content(prompt, stream=True)
    for chunk in response:
        yield chunk.text

# Add any other API-related functions here