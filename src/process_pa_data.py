"""
TODO:
    - [ ] Figure out how to align features across different counties: they have different elections, but the major ones are the same
    - [ ] Within some counties like Allegheny, there are three separate elections on the same date (likely disjoint subsets of the voters voted in each, like special elections).
          Figure out how to handle this (likely by combining them into a single election).
    - [ ] Figure out how to ensure that the non-election features are constant across counties
"""

import os
import pandas as pd
from tqdm import tqdm
import sys
import json


DIR_NAME = "PA Voter File 7_15_23"
OUTPUT_DIR = "processed_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Strings which are unique to each type of file for each county
VOTER_FILE_STR = "FVE"
ELECTION_MAP_STR = "Election Map"
ZONE_CODES_STR = "Zone Codes"
ZONE_TYPES_STR = "Zone Types"


# Ensure the directory exists
assert os.path.isdir(DIR_NAME), f"Directory {DIR_NAME} does not exist"

columns = pd.read_csv(os.path.join(DIR_NAME, "column_mapping.csv"), header=0)

# Retrieve all the counties
counties: set[str] = set()
for file in sorted(os.listdir(DIR_NAME)):
    if file != "column_mapping.csv":
        counties.add(file.split(" ")[0])


# Track the dates of elections, and their corresponding possible descriptions
elections: dict[str, set[str]] = {}
for file in os.listdir(DIR_NAME):
    if ELECTION_MAP_STR in file:
        election_map = pd.read_csv(
            os.path.join(DIR_NAME, file),
            sep="\t",
            encoding="unicode_escape",
            header=None,
        )

        # Check the date of the election
        for _, row in election_map.iterrows():
            if row[3] not in elections:
                elections[row[3]] = {row[2]}
            else:
                elections[row[3]].add(row[2])

# Cast sets to lists for json serialization
for date in elections:
    elections[date] = list(elections[date])

json.dump(elections, open(os.path.join(OUTPUT_DIR, "elections.json"), "w"), indent=4)

election_column_names = []
for election in elections.keys():
    election_column_names.append(f"{election} Party")
    election_column_names.append(f"{election} Vote Method")


for county in tqdm(sorted(counties), desc="Processing counties", unit="county", colour="green"):
    voter_data = election_map = zone_codes = zone_types = None
    for file in os.listdir(DIR_NAME):
        if county in file and VOTER_FILE_STR in file:
            voter_data = pd.read_csv(
                os.path.join(DIR_NAME, file),
                sep="\t",
                encoding="unicode_escape",
                header=None,
                dtype=str,
            )
        if county in file and ELECTION_MAP_STR in file:
            election_map = pd.read_csv(
                os.path.join(DIR_NAME, file),
                sep="\t",
                encoding="unicode_escape",
                header=None,
            )

            # Map the election number to a date in the elections
            election_mapping = {}
            for _, row in election_map.iterrows():
                date = row[3]
                if date in elections:
                    election_mapping[row[1]] = date

        if county in file and ZONE_CODES_STR in file:
            zone_codes = pd.read_csv(
                os.path.join(DIR_NAME, file),
                sep="\t",
                encoding="unicode_escape",
                header=None,

            )
        if county in file and ZONE_TYPES_STR in file:
            zone_types = pd.read_csv(
                os.path.join(DIR_NAME, file),
                sep="\t",
                encoding="unicode_escape",
                header=None,
            )

    if voter_data is None or election_mapping is None:
        print(f"Skipping county {county} due to missing data")
        continue

    # Modify the column names for this county
    column_names = columns["Field Description"].copy()

    column_rename_map = {}

    # Replace election column names with the actual election names
    for i, name in enumerate(column_names):
        if "Election" in name:
            election_number = int(name.split(" ")[1])
            if election_number in election_mapping:
                column_rename_map[i] = election_mapping[election_number] + (" Vote Method" if "Vote Method" in name else " Party")
            else:
                continue
        else:
            column_rename_map[i] = name

    voter_data.rename(columns=column_rename_map, inplace=True)

    columns_to_drop = set(range(len(column_names))) - set(column_rename_map.keys())

    voter_data.drop(voter_data.columns[list(columns_to_drop)], axis=1, inplace=True)

    # # Set the column names
    # voter_data.columns = column_names

    # Drop the columns which are None
    # voter_data.dropna(axis=1, inplace=True)

    if len(set(voter_data.columns)) != len(voter_data.columns):
        print(f"Non-unique columns in {county}")
        column_counts = voter_data.columns.value_counts()
        print(column_counts[column_counts > 1])

    # Save the csv
    voter_data.to_csv(f"{OUTPUT_DIR}/{county}_voter_data.csv", index=False)

    # all_dataframes.append(voter_data)


# full_state_data = pd.concat(all_dataframes, axis=0, ignore_index=True, sort=False)

# Save the data
# full_state_data.to_csv("pa_voter_data.csv", index=False)

# Check for duplicate voter IDs
# assert len(full_state_data["ID Number"].unique()) == len(full_state_data), "Duplicate voter IDs"
