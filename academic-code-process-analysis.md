# Paper Search and Summary Process Analysis

## 1. User Interaction (`main.py`)
1. User submits a search request via the `/search` endpoint.
2. `search_papers` function is called with the field and time range.

## 2. Paper Fetching (`paper_processing.py` - `fetch_papers` function)
1. Calculate the start date based on the time range.
2. Set up an arXiv search query.
3. Create an `aiohttp.ClientSession`.
4. For each paper in the arXiv search results:
   - Call `process_paper` asynchronously.
   - These calls are gathered with `asyncio.gather`, allowing parallel processing.

## 3. Paper Processing (`paper_processing.py` - `process_paper` function)
For each paper:
1. Check if the paper is in the cache.
2. If not cached:
   - Scrape arXiv HTML (async).
   - Get social media mentions (async placeholder).
   - Get Google Scholar data (async placeholder).
   - Calculate impact score and generate keywords (sync, uses Gemini API).
3. Cache the processed paper data.

## 4. Paper Summary Generation (`paper_processing.py` - `generate_paper_summary` function)
This function is a generator that yields parts of the summary:
1. Yield formatted metadata (title, authors, impact score, etc.).
2. Generate a prompt for the detailed summary.
3. Use Gemini API to generate the detailed summary (sync operation).
4. Yield parts of the generated summary.

## 5. Response Streaming (`main.py` - `search_papers` function)
1. Fetch papers (async operation from step 2).
2. For each fetched paper:
   - Generate summary (calls `generate_paper_summary`).
   - Yield each part of the summary as it's generated.

## Key Observations
1. The main async operations are in paper fetching and processing (steps 2 and 3).
2. The Gemini API calls occur in two places:
   - During paper processing (`quick_abstract_impact_rating`) - This is part of the async flow.
   - During summary generation (`generate_paper_summary`) - This is the last step in the process.
3. The summary generation, which uses the Gemini API, is indeed at the last step of the process, allowing for streaming output without waiting for the full summary.
