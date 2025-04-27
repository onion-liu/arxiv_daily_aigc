import arxiv
import logging
from datetime import date, timedelta, datetime, timezone
from typing import List, Dict, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_cv_papers(category: str = 'cs.CV', max_results: int = 500, specified_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """Fetches papers from the specified category submitted on arXiv for a given date.

    Args:
        category (str): The arXiv category (e.g., 'cs.CV', 'cs.AI').
        max_results (int): The maximum number of results to retrieve.
        specified_date (Optional[date]): The specific date to fetch papers for (UTC).
                                         Defaults to 3 days before the current UTC date.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary contains
                              the 'title', 'summary', 'url', 'published_date',
                              'updated_date', 'categories', and 'authors' of a paper.
                              Returns an empty list if an error occurs or no papers are found.
    """
    if specified_date is None:
        # Default to 3 days ago (UTC)
        specified_date = datetime.now(timezone.utc).date() - timedelta(days=3)
        logging.info(f"No date specified, defaulting to {specified_date.strftime('%Y-%m-%d')} UTC.")
    else:
        logging.info(f"Fetching papers for specified date: {specified_date.strftime('%Y-%m-%d')} UTC.")

    # Format for arXiv API: YYYYMMDDHHMM (GMT/UTC)
    start_time_str = specified_date.strftime('%Y%m%d') + '0000'
    next_day = specified_date + timedelta(days=1)
    end_time_str = next_day.strftime('%Y%m%d') + '0000'

    # Construct the search query
    query = f'cat:{category} AND submittedDate:[{start_time_str} TO {end_time_str}]'
    logging.info(f"Using arXiv query: {query}")

    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    papers: List[Dict[str, Any]] = []
    try:
        results = client.results(search)
        # Iterate through the generator
        count = 0
        for result in results:
            papers.append({
                'title': result.title,
                'summary': result.summary.strip(),
                'url': result.entry_id,
                'published_date': result.published,
                'updated_date': result.updated,
                'categories': result.categories,
                'authors': [author.name for author in result.authors],
            })
            count += 1
        logging.info(f"Successfully fetched {count} papers submitted on {specified_date.strftime('%Y-%m-%d')} from {category}.")

    except arxiv.arxiv.UnexpectedEmptyPageError as e:
        logging.warning(f"arXiv query returned an empty page (potentially no results for the date/query): {e}")
        # This might not be a critical error, could just mean no papers found
    except arxiv.arxiv.HTTPError as e:
        logging.error(f"HTTP error during arXiv search: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during arXiv search: {e}", exc_info=True)
        # Log the full traceback for unexpected errors

    return papers

if __name__ == '__main__':
    logging.info("Starting arXiv paper fetching example...")
    # Example usage: Fetch papers for a specific date
    # Note: Using a future date like 2025 will likely return 0 results unless arXiv data exists for it.
    # Use a recent past date for better testing.
    # example_date = date.today() - timedelta(days=4) # Example: 4 days ago
    example_date = date(2025, 4, 23) # Or a specific past date known to have papers

    logging.info(f"Fetching papers for {example_date.strftime('%Y-%m-%d')}...")
    latest_papers = fetch_cv_papers(category='cs.CV', max_results=500, specified_date=example_date)

    if latest_papers:
        logging.info(f"--- Found {len(latest_papers)} Papers ---")
        for i, paper in enumerate(latest_papers):
            print(f"{i+1}. {paper['title']}. authors: {paper['authors']}.")
    else:
        print(f"No papers found for {date_example} or an error occurred.")