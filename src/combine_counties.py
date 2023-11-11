import pandas as pd
from tqdm import tqdm
import os


DIR_NAME = "processed_data"
OUTPUT_FILE = "pa_data_all_elections_sample.csv"

dataframes = []

for file in tqdm(os.listdir(DIR_NAME), desc="Reading files", unit="file", colour="green"):
    if file.endswith(".csv"):
        if file == OUTPUT_FILE:
            continue
        else:
            df = pd.read_csv(os.path.join(DIR_NAME, file))

            # Take a random sample of 10% of the rows
            df = df.sample(frac=0.1, random_state=42)
            dataframes.append(df)

print("Combining dataframes (this could take a while)...")
df = pd.concat(dataframes, axis=0, ignore_index=True, sort=False)
df.to_csv(OUTPUT_FILE, index=False)
