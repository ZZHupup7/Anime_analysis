import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import time
import random
from tqdm import tqdm
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Enhanced request headers to mimic a real browser
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/91.0.4472.124 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

# Base URL for the Top Anime page
BASE_URL = "https://myanimelist.net/topanime.php"


class AnimeScraperError(Exception):
    """Custom exception for scraper errors."""
    pass


def create_session():
    """
    Create an HTTP session with a retry strategy to handle transient errors.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)
    return session


def fetch_page(session, url):
    """
    Fetch a page and return a BeautifulSoup object.
    Raises AnimeScraperError on network issues.
    """
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        raise AnimeScraperError(f"Failed to fetch page: {e}")


def parse_anime_details(session, url):
    """
    Visit an anime's detail page and extract additional fields:
    Type, Episodes, Duration, Source, Aired dates, Season,
    Genres, and viewer statistics.
    """
    try:
        soup = fetch_page(session, url)
        info = {}

        # Map labels on the page to our field names
        info_fields = {
            "Type:": "Type",
            "Episodes:": "Episodes",
            "Duration:": "Duration",
            "Source:": "Source",
            "Aired:": "Aired",
            "Season:": "Season"
        }

        # Extract each field by its label
        for label, field in info_fields.items():
            element = soup.find('span', string=label)
            if element and element.next_sibling:
                info[field] = element.next_sibling.strip()
            else:
                info[field] = "Unknown"

        # Extract genres
        genres = [g.text for g in soup.select("span[itemprop='genre']")]
        info["Genres"] = ", ".join(genres) if genres else "Unknown"

        # Initialize viewer stats
        stats = {
            "Watching": 0,
            "Completed": 0,
            "On_Hold": 0,
            "Dropped": 0,
            "Plan_to_Watch": 0
        }

        # Search the entire page text for each status
        page_text = soup.get_text()
        for status, key in [
            ("Watching", "Watching"),
            ("Completed", "Completed"),
            ("On-Hold", "On_Hold"),
            ("Dropped", "Dropped"),
            ("Plan to Watch", "Plan_to_Watch")
        ]:
            match = re.search(fr"{status}:\s*([\d,]+)", page_text)
            if match:
                stats[key] = int(match.group(1).replace(",", ""))

        # Merge stats into info
        info.update(stats)

        # Infer season number from text if possible
        season_num = 1
        if info.get("Type", "").startswith("TV"):
            season_match = soup.find(string=lambda t: t and "Season" in t)
            if season_match:
                digits = "".join(filter(str.isdigit, season_match))
                if digits.isdigit():
                    season_num = int(digits)
        info["Season_Number"] = season_num

        return info

    except Exception as e:
        logging.error(f"Error parsing details from {url}: {e}")
        # Return defaults on failure
        return {
            "Type": "Unknown",
            "Episodes": "Unknown",
            "Duration": "Unknown",
            "Source": "Unknown",
            "Aired": "Unknown",
            "Season": "Unknown",
            "Genres": "Unknown",
            "Watching": 0,
            "Completed": 0,
            "On_Hold": 0,
            "Dropped": 0,
            "Plan_to_Watch": 0,
            "Season_Number": 1
        }


def parse_top_anime(session, soup):
    """
    From the Top Anime listing page soup, extract:
    Rank, Title, Score, Rating_Users, then call parse_anime_details.
    """
    anime_list = []
    entries = soup.find_all("tr", class_="ranking-list")

    for entry in tqdm(entries, desc="Scraping anime entries"):
        try:
            # Rank and title
            rank = int(entry.find("td", class_="rank").text.strip())
            title_tag = entry.find("h3", class_="anime_ranking_h3").find("a")
            title = title_tag.text.strip()
            link = title_tag["href"]

            # Score
            score_td = entry.find("td", class_="score")
            score = float(score_td.find("span").text.strip()
                          ) if score_td else 0.0

            # Number of users rated
            rating_text = score_td.get_text(strip=True)
            m = re.search(r'by ([\d,]+) users', rating_text)
            rating_users = int(m.group(1).replace(",", "")) if m else 0

            # Fetch detailed info
            details = parse_anime_details(session, link)

            anime_list.append({
                "Rank": rank,
                "Title": title,
                "Score": score,
                "Rating_Users": rating_users,
                **details
            })

            # Random delay to be polite
            time.sleep(random.uniform(5, 10))

        except Exception as e:
            logging.error(
                f"Error processing entry {title if 'title' in locals() else 'unknown'}: {e}")
            continue

    return anime_list


def save_data(anime_list, filepath):
    """
    Save the collected anime_list to CSV,
    creating the directory if needed.
    """
    if not anime_list:
        raise AnimeScraperError("No data to save")

    df = pd.DataFrame(anime_list)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False, encoding='utf-8')
    logging.info(f"Data saved successfully to {filepath}")
    return df


def main():
    """
    Main routine: fetch Top 150 anime across three pages
    and save to a CSV file.
    """
    try:
        script_dir = Path(__file__).resolve().parent
        data_dir = script_dir.parent / "data"
        output_file = data_dir / "top_anime_detailed.csv"

        session = create_session()
        all_anime = []

        # Fetch three pages (0, 50, 100) for Top 150 titles
        for offset in [0, 50, 100]:
            url = f"{BASE_URL}?limit={offset}"
            logging.info(f"Fetching Top Anime page with offset={offset}")
            soup = fetch_page(session, url)
            all_anime.extend(parse_top_anime(session, soup))
            time.sleep(random.uniform(2, 4))

        # Save results
        df = save_data(all_anime, output_file)

        logging.info("\nData Summary:")
        logging.info(f"Total entries fetched: {len(df)}")
        logging.info(f"Average score: {df['Score'].mean():.2f}")

    except Exception as e:
        logging.error(f"Script failed: {e}")
        raise


if __name__ == "__main__":
    main()
