import asyncio
from datetime import datetime, timedelta
import pytz
from bs4 import BeautifulSoup
import re
import numpy as np
import logging
from config import MAX_RESULTS, ABSTRACT_RATING_PROMPT, PAPER_SUMMARY_PROMPT
from api import fetch_url, get_arxiv_paper, get_social_media_mentions, get_google_scholar_data, generate_flash_content, generate_pro_content, generate_flash_content_stream
from cache import paper_cache, get_paper_summary, save_paper_summary
import arxiv
import aiohttp


logger = logging.getLogger(__name__)

async def scrape_arxiv_html(session, arxiv_id):
    logger.info(f"Scraping arXiv HTML for ID: {arxiv_id}")
    url = f"https://arxiv.org/html/{arxiv_id}"
    html = await fetch_url(session, url)
    soup = BeautifulSoup(html, 'html.parser')

    full_text = ' '.join([p.text for p in soup.find_all('p')])
    cited_by = len(re.findall(r'\[(\d+)\]', full_text))  # Count references as a proxy
    authors = [a.text for a in soup.find_all('meta', attrs={'name': 'citation_author'})]

    logger.info(f"Scraped arXiv HTML for ID: {arxiv_id}. Found {cited_by} citations and {len(authors)} authors")
    return full_text, cited_by, authors

def calculate_impact_score(citations, author_h_index, social_mentions, days_since_publication, abstract_rating):
    logger.info("Calculating impact score")
    norm_citations = np.log1p(citations) / 10
    norm_author = (author_h_index if author_h_index else 5) / 100
    norm_social = np.log1p(social_mentions) / 5
    norm_recency = 1 - (days_since_publication / 365)
    norm_abstract = abstract_rating / 10

    weights = [0.2, 0.2, 0.2, 0.1, 0.3]
    score = np.dot(weights, [norm_citations, norm_author, norm_social, norm_recency, norm_abstract])

    logger.info(f"Calculated impact score: {score}")
    return score

async def quick_abstract_impact_rating(title, abstract, citations, h_index, social_mentions, days_since_publication):
    logger.info(f"Generating quick abstract impact rating for paper: {title}")
    prompt = ABSTRACT_RATING_PROMPT.format(
        title=title,
        abstract=abstract,
        citations=citations,
        social_mentions=social_mentions
    )

    response = generate_flash_content(prompt)
    parts = response.strip().split(',')
    try:
        rating = calculate_impact_score(citations, h_index, social_mentions, days_since_publication, int(parts[0].strip()))
        keywords = [part.strip() for part in parts[1:]]
        logger.info(f"Generated impact rating: {rating} with keywords: {keywords}")
        return max(1, min(100, rating)), keywords
    except ValueError:
        logger.error(f"Error parsing impact rating response: {response}")
        return 5, ['No keywords']
    

async def extract_paper_sections(full_text):
    sections = {
        'introduction': '',
        'methodology': '',
        'model_architecture': '',
        'results': ''
    }
    
    # Define patterns to match section headers
    patterns = {
        'introduction': r'(?i)introduction|background',
        'methodology': r'(?i)method(ology)?|approach',
        'model_architecture': r'(?i)model\s+architecture|network\s+structure',
        'results': r'(?i)results|findings'
    }
    
    # Find the start of each section
    section_starts = {}
    for section, pattern in patterns.items():
        match = re.search(pattern, full_text)
        if match:
            section_starts[section] = match.start()
    
    # Sort sections by their starting position
    sorted_sections = sorted(section_starts.items(), key=lambda x: x[1])
    
    # Extract content for each section
    for i, (section, start) in enumerate(sorted_sections):
        if i < len(sorted_sections) - 1:
            end = sorted_sections[i+1][1]
            sections[section] = full_text[start:end].strip()
        else:
            sections[section] = full_text[start:].strip()
    
    # Limit each section to 1000 words
    for section in sections:
        sections[section] = ' '.join(sections[section].split()[:1000])
    
    return sections

paper_is_cached = False
async def process_paper(session, paper, start_date):
    arxiv_id = paper.get_short_id()
    title = paper.title
    logger.info(f"Processing paper with arXiv ID: {arxiv_id}")

    global paper_is_cached
    cached_result = get_paper_summary(title)
    if cached_result:
        logger.info(f"Retrieved cached result for paper: {title}")
        paper_is_cached = True
        return cached_result

    full_text, cited_by, authors = await scrape_arxiv_html(session, arxiv_id)
    extracted_sections = await extract_paper_sections(full_text)

    social_mentions = await get_social_media_mentions(session, paper.title)
    citations, author_h_index = await get_google_scholar_data(session, paper.title, authors)

    days_since_publication = (datetime.now(pytz.utc) - paper.published).days
    impact_score, keywords = await quick_abstract_impact_rating(paper.title, paper.summary, citations, author_h_index, social_mentions, days_since_publication)

    result = {
        "title": paper.title,
        "authors": ", ".join(author.name for author in paper.authors),
        "impact_score": round(impact_score, 3),
        "keywords": keywords,
        "citations": citations,
        "url": paper.pdf_url,
        "full_text": extracted_sections, #extracted_sections, full_text
        "abstract": paper.summary,
    }

    paper_cache.set(arxiv_id, result)
    logger.info(f"Processed and cached result for arXiv ID: {arxiv_id}")
    return result

async def fetch_papers(query, time_range):
    logger.info(f"Fetching papers for query: {query}, time range: {time_range}")
    days = int(time_range.split()[1])
    start_date = datetime.now(pytz.utc) - timedelta(days=days)
    max_results = MAX_RESULTS[time_range]

    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers = []
    async with aiohttp.ClientSession() as session:
        tasks = [process_paper(session, paper, start_date) for paper in client.results(search)]
        papers = await asyncio.gather(*tasks)

    logger.info(f"Fetched and processed {len(papers)} papers")

    if paper_is_cached:
        return papers
    return sorted(papers, key=lambda x: int(x['impact_score']), reverse=True)[:3]

def generate_paper_summary(paper):
    logger.info(f"Generating summary for paper: {paper['title']}")

    formatted_summary = f"## {paper['title']}\n\n"
    formatted_summary += f"**Authors:** {paper['authors']}\n"
    formatted_summary += f"**Impact Score:** {paper['impact_score']}\n"
    formatted_summary += f"**Keywords:** {', '.join(paper['keywords'])}\n"
    formatted_summary += f"**Citations:** {paper['citations']}\n"
    formatted_summary += f"**URL:** {paper['url']}\n\n"
    formatted_summary += "**Summary:**\n"

    yield formatted_summary

    prompt = PAPER_SUMMARY_PROMPT.format(
        title=paper['title'],
        abstract=paper['abstract'],
        full_text=paper['full_text'][:12000] if len(paper['full_text']) > 12000 else paper['full_text']
    )

    logger.info(f"Generating detailed summary for paper: {paper['title']}")
    for part in generate_flash_content_stream(prompt):
        formatted_summary += part
        yield part

    logger.info(f"Completed summary generation for paper: {paper['title']}")
    save_paper_summary(paper['title'], formatted_summary)
    logger.info(f"Saved summary generation for paper: {paper['title']}")

# Add any other paper processing functions here