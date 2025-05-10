import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging

# Configure logging for visualization
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def set_style():
    """
    Apply consistent styling to all plots using matplotlib and seaborn.
    """
    plt.style.use('default')
    sns.set_style("whitegrid")
    sns.set_palette("husl")

    plt.rcParams.update({
        'figure.figsize': (10, 6),
        'font.size': 12,
        'axes.labelsize': 12,
        'axes.titlesize': 14,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'font.family': 'sans-serif',
        'grid.linestyle': '--',
        'grid.alpha': 0.6,
        'axes.grid': True,
        'figure.dpi': 100,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'figure.autolayout': True
    })


def plot_top_anime(df: pd.DataFrame, plots_dir: Path):
    """
    Plot the Top 10 highest-rated anime as a horizontal bar chart,
    include rank labels and viewership info on the right.
    """
    plt.figure(figsize=(15, 8))
    top_10 = df.head(10)

    colors = sns.color_palette("husl", 10)
    ax = sns.barplot(x='Score', y='Title', data=top_10, palette=colors)

    # Show rank on the left
    new_labels = [f"#{i+1}  {title}" for i,
                  title in enumerate(top_10['Title'])]
    ax.set_yticklabels(new_labels)
    ax.set_ylabel(None)

    # Extend x-axis to leave room for text
    max_score = df['Score'].max()
    plt.xlim(0, max_score + 0.5)

    # Helper to format viewership labels
    def format_watchers(n):
        if n >= 1e6:
            return f'{n/1e6:.1f}M viewers'
        elif n >= 1e3:
            return f'{n/1e3:.0f}K viewers'
        else:
            return f'{int(n)} viewers'

    # Annotate score and viewers on the right
    for idx, row in top_10.iterrows():
        score_str = f"{row['Score']:.2f}"
        if row['Total_Watchers'] > 0:
            text = f"{score_str}   {format_watchers(row['Total_Watchers'])}"
        else:
            text = score_str
        plt.text(max_score + 0.15, idx, text,
                 va='center', ha='left', fontsize=9, color='#444444')

    plt.title('Top 10 Highest Rated Anime\nwith Viewership',
              pad=20, fontweight='bold')
    plt.xlabel('Average Score (out of 10)', fontweight='bold')
    plt.ylabel('')

    plt.tight_layout()
    plt.savefig(plots_dir / 'top_10_anime.png', pad_inches=0.2)
    plt.close()


def plot_score_episodes(df: pd.DataFrame, plots_dir: Path):
    """
    Plot correlation between number of episodes and score,
    bubble size represents number of user ratings.
    """
    plt.figure(figsize=(12, 8))
    # Drop rows with missing Episodes or Score
    plot_df = df.dropna(subset=['Episodes', 'Score'])
    sns.scatterplot(data=plot_df, x='Episodes', y='Score',
                    hue='Type', size='Rating_Users',
                    sizes=(100, 1000), alpha=0.6)

    sns.regplot(data=plot_df, x='Episodes', y='Score',
                scatter=False, color='red', line_kws={'linestyle': '--'})

    plt.title('Episodes vs Score (size = ratings count)')
    plt.xlabel('Number of Episodes')
    plt.ylabel('Score')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    plt.savefig(plots_dir / 'score_vs_episodes.png')
    plt.close()


def plot_genres_distribution(df: pd.DataFrame, plots_dir: Path):
    """
    Plot the top 10 most common anime genres.
    """
    plt.figure(figsize=(14, 8))
    genres = df['Genres'].str.split(', ').explode()
    top_genres = genres.value_counts().head(10)

    colors = sns.color_palette("husl", len(top_genres))
    ax = sns.barplot(y=top_genres.index, x=top_genres.values, palette=colors)

    for container in ax.containers:
        ax.bar_label(container, fmt='%d', padding=5)

    plt.title('Top 10 Most Common Anime Genres')
    plt.xlabel('Count')
    plt.ylabel('Genre')

    plt.tight_layout()
    plt.savefig(plots_dir / 'genre_distribution.png')
    plt.close()


def plot_watching_status(df: pd.DataFrame, plots_dir: Path):
    """
    Plot distribution of anime watching status across users.
    Skips plotting if all counts are zero.
    """
    status_cols = ['Watching', 'Completed',
                   'On_Hold', 'Dropped', 'Plan_to_Watch']
    status_sums = df[status_cols].sum()
    if status_sums.sum() == 0:
        logging.info("All watching status counts are zero—skipping plot.")
        return

    plt.figure(figsize=(12, 7))
    sorted_sums = status_sums.sort_values()
    ax = sns.barplot(x=sorted_sums.values, y=sorted_sums.index, palette='husl')

    def fmt_num(x):
        return f'{x/1e6:.1f}M' if x >= 1e6 else f'{x/1e3:.0f}K'
    for container in ax.containers:
        ax.bar_label(container, fmt=fmt_num, padding=5)

    plt.title('Anime Watching Status Distribution')
    plt.xlabel('Number of Users')
    plt.ylabel('Status')

    plt.tight_layout()
    plt.savefig(plots_dir / 'watching_status.png')
    plt.close()


def main():
    """
    Load cleaned data and generate all visualizations.
    """
    try:
        script_dir = Path(__file__).resolve().parent
        data_dir = script_dir.parent / "data"
        plots_dir = script_dir.parent / "plots"
        plots_dir.mkdir(exist_ok=True)

        set_style()

        df = pd.read_csv(data_dir / "top_anime_detailed_cleaned.csv")
        logging.info(f"Loaded {len(df)} rows of cleaned data")

        plot_top_anime(df, plots_dir)
        plot_score_episodes(df, plots_dir)
        plot_genres_distribution(df, plots_dir)
        plot_watching_status(df, plots_dir)

        logging.info("All plots saved successfully.")

    except Exception as e:
        logging.error(f"Error during visualization: {e}")
        raise


if __name__ == "__main__":
    main()
