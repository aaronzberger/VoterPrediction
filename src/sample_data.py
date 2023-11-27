"""Take a sample of the data from each election and combine them into one file"""

import os

import pandas as pd
from tqdm import tqdm

from src.config import PROCESSED_DATA_DIR, TEN_PCT_SAMPLE_FILE


dataframes = []

for file in tqdm(
    os.listdir(PROCESSED_DATA_DIR), desc="Reading files", unit="file", colour="green"
):
    if file.endswith(".csv"):
        if file == TEN_PCT_SAMPLE_FILE:
            # If this script was already run, skip the file
            continue
        else:
            df = pd.read_csv(os.path.join(PROCESSED_DATA_DIR, file))

            # Take a random sample of 10% of the rows
            df = df.sample(frac=0.1, random_state=42)
            dataframes.append(df)

print("Combining dataframes (this could take a while)...")
df = pd.concat(dataframes, axis=0, ignore_index=True, sort=False)
df.to_csv(TEN_PCT_SAMPLE_FILE, index=False)
