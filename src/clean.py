import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Configure logging for this script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def clean_anime_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalize the raw anime DataFrame:
    - Convert Score to numeric
    - Normalize Rating_Users
    - Convert Episodes to numeric, handling 'Unknown'
    - Fill missing Type with 'Other'
    - Convert viewer status columns to numeric
    - Compute Total_Watchers and Completion_Rate
    - Sort by Score descending
    """
    logging.info("Starting data cleaning process...")

    # Convert Score to float
    df['Score'] = pd.to_numeric(df['Score'], errors='coerce')

    # Normalize Rating_Users (remove commas if present)
    if df['Rating_Users'].dtype == 'object':
        df['Rating_Users'] = pd.to_numeric(
            df['Rating_Users'].str.replace(',', ''), errors='coerce'
        )
    else:
        df['Rating_Users'] = pd.to_numeric(df['Rating_Users'], errors='coerce')

    # Convert Episodes to numeric, treat 'Unknown' as NaN
    df['Episodes'] = df['Episodes'].replace('Unknown', np.nan)
    df['Episodes'] = pd.to_numeric(df['Episodes'], errors='coerce')

    # Fill missing Type with 'Other'
    df['Type'] = df['Type'].fillna('Other')

    # Convert status columns to numeric and log first few values
    status_cols = ['Watching', 'Completed',
                   'On_Hold', 'Dropped', 'Plan_to_Watch']
    for col in status_cols:
        logging.info(
            f"Cleaning column: {col} (first 5 values: {df[col].head().tolist()})")
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Compute total watchers and completion rate
    df['Total_Watchers'] = df[status_cols].sum(axis=1)
    df['Completion_Rate'] = (
        df['Completed'] / df['Total_Watchers'] * 100
    ).round(2).fillna(0)

    # Sort by Score descending, reset index
    df = df.sort_values('Score', ascending=False).reset_index(drop=True)
    return df


def main():
    """
    Load raw data CSV, clean it, and save to a new CSV.
    """
    try:
        script_dir = Path(__file__).resolve().parent
        data_dir = script_dir.parent / "data"
        input_file = data_dir / "top_anime_detailed.csv"
        output_file = data_dir / "top_anime_detailed_cleaned.csv"

        df = pd.read_csv(input_file)
        logging.info(f"Loaded {len(df)} rows of raw data")

        df_cleaned = clean_anime_data(df)
        df_cleaned.to_csv(output_file, index=False, encoding='utf-8')
        logging.info(f"Cleaned data saved to {output_file}")

        # Summary stats
        logging.info(f"Total anime count after cleaning: {len(df_cleaned)}")
        logging.info(f"Average score: {df_cleaned['Score'].mean():.2f}")
        logging.info(f"Most common type: {df_cleaned['Type'].mode()[0]}")

    except Exception as e:
        logging.error(f"Error during data cleaning: {e}")
        raise


if __name__ == "__main__":
    main()
