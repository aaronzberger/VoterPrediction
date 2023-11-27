import os
import pandas as pd
from tqdm import tqdm
import json
from config import (
    WITHHELD_DEMOGRAPHIC_FEATURES,
    PROCESSED_DATA_DIR,
    VOTER_FILE_DIR,
    VOTER_FILE_COLUMN_MAPPING_FILE,
    ELECTION_DATES_TO_NAMES_MAPPING_FILE,
    FEATURES_FILE,
    election_date_to_feature_names
)


# Strings which are unique in the title of each type of file for each county
VOTER_FILE_STR = "FVE"
ELECTION_MAP_STR = "Election Map"
ZONE_CODES_STR = "Zone Codes"
ZONE_TYPES_STR = "Zone Types"

columns_template = pd.read_csv(VOTER_FILE_COLUMN_MAPPING_FILE, header=0)

# Retrieve all the counties
counties: set[str] = set()
for file in sorted(os.listdir(VOTER_FILE_DIR)):
    if VOTER_FILE_STR in file:
        counties.add(file.split(" ")[0])

# Track the dates of elections, and their corresponding possible descriptions
state_elections: dict[str, set[str]] = {}
for file in os.listdir(VOTER_FILE_DIR):
    if ELECTION_MAP_STR in file:
        election_map = pd.read_csv(
            os.path.join(VOTER_FILE_DIR, file),
            sep="\t",
            encoding="unicode_escape",
            header=None,
        )

        # Check the date of the election
        for _, row in election_map.iterrows():
            if row[3] not in state_elections:
                state_elections[row[3]] = {row[2]}
            else:
                state_elections[row[3]].add(row[2])

# Dump to a json file
state_elections = {date: list(state_elections[date]) for date in state_elections}
json.dump(
    state_elections,
    open(ELECTION_DATES_TO_NAMES_MAPPING_FILE, "w"),
    indent=4,
)

election_column_names = []
for election in state_elections.keys():
    election_column_names.extend(election_date_to_feature_names(election))

# Only include up to the column named District 40
raw_column_names = columns_template["Field Description"].tolist()
demographic_columns = [
    col
    for col in raw_column_names
    if "Election" not in col
    and "District" not in col
    and col not in WITHHELD_DEMOGRAPHIC_FEATURES
]

# Here, include other custom feature changes
demographic_columns.remove("Gender")
demographic_columns.append("Gender M")
demographic_columns.append("Gender F")
demographic_columns.append("Gender U")

demographic_columns.remove("Party Code")
demographic_columns.append("Party D")
demographic_columns.append("Party R")
demographic_columns.append("Party I")

demographic_columns.remove("Last Vote Date")
demographic_columns.append("Last Vote Date Presence")
demographic_columns.append("Last Vote Date")

with open(FEATURES_FILE, "w") as f:
    json.dump(
        {
            "demographic": demographic_columns,
            "elections": election_column_names,
        },
        f,
        indent=4,
    )

all_column_names = demographic_columns + election_column_names

all_dataframes = []

for county in tqdm(
    sorted(counties), desc="Processing counties", unit="county", colour="green"
):
    # region Load the data
    voter_data = election_map = zone_codes = zone_types = None
    for file in os.listdir(VOTER_FILE_DIR):
        if county in file and VOTER_FILE_STR in file:
            voter_data = pd.read_csv(
                os.path.join(VOTER_FILE_DIR, file),
                sep="\t",
                encoding="unicode_escape",
                header=None,
                dtype=str,
            )
        if county in file and ELECTION_MAP_STR in file:
            election_map = pd.read_csv(
                os.path.join(VOTER_FILE_DIR, file),
                sep="\t",
                encoding="unicode_escape",
                header=None,
            )

            # Map the election number to a date in the elections
            county_elections = {}
            for _, row in election_map.iterrows():
                date = row[3]
                if date in state_elections:
                    county_elections[row[1]] = date
                else:
                    print(
                        f"Skipping election {row[1]} in county {county} due to missing data"
                    )

        if county in file and ZONE_CODES_STR in file:
            zone_codes = pd.read_csv(
                os.path.join(VOTER_FILE_DIR, file),
                sep="\t",
                encoding="unicode_escape",
                header=None,
            )
        if county in file and ZONE_TYPES_STR in file:
            zone_types = pd.read_csv(
                os.path.join(VOTER_FILE_DIR, file),
                sep="\t",
                encoding="unicode_escape",
                header=None,
            )

    if voter_data is None or county_elections is None:
        print(f"Skipping county {county} due to missing data")
        continue
    # endregion

    voter_data.columns = columns_template["Field Description"].tolist()

    aligned_voter_data = pd.DataFrame(columns=all_column_names)

    # region Migrate the demographic columns
    for col in voter_data.columns:
        # Ignore the election columns
        if "Election" in col:
            continue

        elif col == "Gender":
            aligned_voter_data["Gender M"] = (voter_data[col] == "M").astype(int)
            aligned_voter_data["Gender F"] = (voter_data[col] == "F").astype(int)
            aligned_voter_data["Gender U"] = (~voter_data[col].isin(["M", "F"])).astype(
                int
            )

        elif col == "Party Code":
            aligned_voter_data["Party D"] = (voter_data[col] == "D").astype(int)
            aligned_voter_data["Party R"] = (voter_data[col] == "R").astype(int)
            aligned_voter_data["Party I"] = (~voter_data[col].isin(["D", "R"])).astype(
                int
            )

        # Scale all dates to 0-1 (using 1900 to today as range)
        elif col in [
            "DOB",
            "Registration Date",
            "Status Change Date",
            "Date Last Changed",
        ]:
            date = pd.to_datetime(voter_data[col], errors="coerce", format="%m/%d/%Y")
            today = pd.to_datetime("today")
            start_date = pd.to_datetime("1900-01-01")

            # If date is before start or after today, set to start or today
            date = date.where(date > start_date, start_date)
            date = date.where(date < today, today)

            # In these columns, there are very few missing values, so we can just fill them with the start date
            date = date.fillna(start_date)

            aligned_voter_data[col] = round(
                (date - start_date) / (today - start_date), 3
            )

        # Scale all dates (which may or may not exist) to 0-1
        elif col == "Last Vote Date":
            date = pd.to_datetime(voter_data[col], errors="coerce", format="%m/%d/%Y")
            today = pd.to_datetime("today")
            start_date = pd.to_datetime("1900-01-01")

            # If date is before start or after today, set to start or today
            date = date.where(date > start_date, start_date)
            date = date.where(date < today, today)

            aligned_voter_data["Last Vote Date Presence"] = (~date.isna()).astype(int)

            date = date.fillna(start_date)

            aligned_voter_data["Last Vote Date"] = round(
                (date - start_date) / (today - start_date), 3
            )

        elif col == "Voter Status":
            aligned_voter_data[col] = (voter_data[col] == "A").astype(int)

        # Migrate the non-custom columns
        elif col in all_column_names:
            aligned_voter_data[col] = voter_data[col]

        elif col in WITHHELD_DEMOGRAPHIC_FEATURES or "District" in col:
            continue

        else:
            print(f"Found a missing column {col} in county {county}")
            aligned_voter_data[col] = None
    # endregion

    added_dates: set[str] = set()

    # region Migrate the election columns
    for index, election_date in county_elections.items():
        if election_date in added_dates:
            # This election was already added, so merge the features with the existing ones
            aligned_voter_data[
                f"Election {election_date} Party D"
            ] = aligned_voter_data[f"Election {election_date} Party D"].combine_first(
                voter_data[f"Election {index} Party"] == "D"
            )
            aligned_voter_data[
                f"Election {election_date} Party R"
            ] = aligned_voter_data[f"Election {election_date} Party R"].combine_first(
                voter_data[f"Election {index} Party"] == "R"
            )
            aligned_voter_data[
                f"Election {election_date} Party I"
            ] = aligned_voter_data[f"Election {election_date} Party I"].combine_first(
                ~voter_data[f"Election {index} Party"].isin(["D", "R"])
            )
            aligned_voter_data[f"Election {election_date} Voted"] = aligned_voter_data[
                f"Election {election_date} Voted"
            ].combine_first(
                voter_data[f"Election {index} Vote Method"]
                .isin(["AP", "MB", "AB", "P"])
                .astype(int)
            )
            aligned_voter_data[
                f"Election {election_date} By Mail"
            ] = aligned_voter_data[f"Election {election_date} By Mail"].combine_first(
                voter_data[f"Election {index} Vote Method"]
                .isin(["MB", "AB"])
                .astype(int)
            )
            continue

        aligned_voter_data[f"Election {election_date} Party D"] = (
            voter_data[f"Election {index} Party"] == "D"
        ).astype(int)
        aligned_voter_data[f"Election {election_date} Party R"] = (
            voter_data[f"Election {index} Party"] == "R"
        ).astype(int)
        aligned_voter_data[f"Election {election_date} Party I"] = (
            ~voter_data[f"Election {index} Party"].isin(["D", "R"])
        ).astype(int)
        aligned_voter_data[f"Election {election_date} Voted"] = (
            voter_data[f"Election {index} Vote Method"]
            .isin(["AP", "MB", "AB", "P"])
            .astype(int)
        )
        aligned_voter_data[f"Election {election_date} By Mail"] = (
            voter_data[f"Election {index} Vote Method"].isin(["MB", "AB"]).astype(int)
        )
        aligned_voter_data[f"Election {election_date} Presence"] = 1

        added_dates.add(election_date)
    # endregion

    # For all the elections that are not present, set the presence to 0
    for election_date in state_elections.keys():
        if election_date not in added_dates:
            aligned_voter_data[f"Election {election_date} Presence"] = 0

    # Save the csv
    aligned_voter_data.to_csv(
        f"{PROCESSED_DATA_DIR}/{county}_voter_data.csv", index=False
    )

    all_dataframes.append(voter_data)


full_state_data = pd.concat(all_dataframes, axis=0, ignore_index=True, sort=False)

# Save the data
full_state_data.to_csv("pa_voter_data.csv", index=False)
