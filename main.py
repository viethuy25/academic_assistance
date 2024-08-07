from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import asyncio
import time
import logging
from paper_processing import fetch_papers, generate_paper_summary
from config import API_HOST, API_PORT, MAX_RESULTS

logger = logging.getLogger(__name__)


app = FastAPI()

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

class SearchRequest(BaseModel):
    field: str
    time_range: str

class PaperSummary(BaseModel):
    title: str
    authors: str
    impact_score: float
    keywords: List[str]
    citations: int
    url: str
    summary: str

@app.post("/search")
async def search_papers(request: SearchRequest):
    logger.info(f"Received search request: field={request.field}, time_range={request.time_range}")

    async def stream_response():
        start_time = time.time()
        max_results = MAX_RESULTS[request.time_range]
        yield f"Searching for {max_results} top papers in {request.field} from the {request.time_range}.\n\n".encode()
        await asyncio.sleep(0)
        try:
            logger.info("Fetching papers...")
            papers = await fetch_papers(request.field, request.time_range)
            yield f"Found top papers in {request.field} from the {request.time_range}. Generating summaries\n\n".encode()
            await asyncio.sleep(0)
            logger.info(f"Processing {len(papers)} papers...")
            yield f"Processing {len(papers)} papers...\n\n".encode()
            await asyncio.sleep(0)

            for i, paper in enumerate(papers, 1):
                logger.info(f"Generating summary for paper {i}/{len(papers)}")
                yield f"Generating summary for paper {i}/{len(papers)}\n".encode()
                await asyncio.sleep(0)

                if type(paper) == str:
                    yield paper
                else:
                    summary_generator = generate_paper_summary(paper)
                    for summary_part in summary_generator:
                        yield summary_part
                        await asyncio.sleep(0)
                yield "\n\n".encode()

            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"Search completed in {execution_time:.2f} seconds")
            yield f"Execution time: {execution_time:.2f} seconds".encode()
        except Exception as e:
            logger.error(f"An error occurred during search: {str(e)}", exc_info=True)
            yield f"An error occurred: {str(e)}".encode()

    return StreamingResponse(stream_response(), media_type="text/plain")

@app.get("/", response_class=HTMLResponse)
async def root():
    logger.info("Serving index.html")
    with open("templates/index.html", "r") as f:
        content = f.read()
    return HTMLResponse(content=content)

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {API_HOST}:{API_PORT}")
    uvicorn.run(app, host=API_HOST, port=API_PORT)