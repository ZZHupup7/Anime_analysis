# Anime Ratings Data Analysis

Analyze top anime from MyAnimeList: scrape, clean, and visualize their ratings and viewer statistics.

## Project Structure
```
anime_analysis/
├── data/
│ ├── top_anime_detailed.csv
│ └── top_anime_detailed_cleaned.csv
├── plots/
│ ├── top_10_anime.png
│ ├── score_vs_episodes.png
│ ├── genre_distribution.png
│ └── watching_status.png
├── src/
│ ├── scrape.py
│ ├── clean.py
│ └── analyze_visualize.py
├── requirements.txt
└── README.md
```

## Setup
1. Clone this repository:


```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

2.Create and activate a virtual environment:
python -m venv venv
# macOS/Linux
source venv/bin/activate
# Windows
venv\Scripts\activate



3.Install dependencies:
pip install -r requirements.txt


Usage
Scrape top anime data (Top 150):
python src/scrape.py

Clean the raw data:
python src/clean.py

Visualize the results:
python src/analyze_visualize.py

Raw and cleaned CSV files are stored in data/.

Generated plots are saved in plots/.


Contributing
Pull requests and issues are welcome. Feel free to suggest new analyses or improvements!
