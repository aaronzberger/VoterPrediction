import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VOTER_FILE_DIR = os.path.join(BASE_DIR, "PA Voter File 7_15_23")
assert os.path.isdir(VOTER_FILE_DIR), f"Directory {VOTER_FILE_DIR} does not exist"

VOTER_FILE_COLUMN_MAPPING_FILE = os.path.join(BASE_DIR, VOTER_FILE_DIR, "column_mapping.csv")

ELECTION_DATES_TO_NAMES_MAPPING_FILE = os.path.join(
    BASE_DIR, "election_dates_to_names.json"
)

PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "processed_data")
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# Map type of feature to names of features (demographic, elections)
FEATURES_FILE = os.path.join(BASE_DIR, PROCESSED_DATA_DIR, "features.json")

TEN_PCT_SAMPLE_FILE = os.path.join(BASE_DIR, PROCESSED_DATA_DIR, "sample_ten_pct.csv")
MAJOR_ELECTIONS_DATES_FILE = os.path.join(BASE_DIR, "major_elections.json")
SLIDING_WINDOW_FILE = os.path.join(BASE_DIR, "sliding_window.csv")

WITHHELD_DEMOGRAPHIC_FEATURES = set(
    [
        "Home Phone",
        "Mail Country",
        "ID Number",
        "Title",
        "Last Name",  # Theoretically, names could be used to deduce race and other demographic information,
        "First Name",  # but the potential for stereotyping and bias is too high
        "Middle Name",
        "Suffix",
        "Custom Data 1",
        "House Number",
        "House Number Suffix",
        "Street Name",
        "Apartment Number",
        "Address Line 2",
        "City",
        "State",
        "Zip",
        "Mail Address 1",
        "Mail Address 2",
        "Mail City",
        "Mail State",
        "Mail Zip",
        "Precint Code",
        "Precint Split ID",
        "County",  # Should probably be added back in, but need to encode text
    ]
)


def election_date_to_feature_names(election_date):
    return [
        f"Election {election_date} Presence",
        f"Election {election_date} Party D",
        f"Election {election_date} Party R",
        f"Election {election_date} Party I",
        f"Election {election_date} Voted",
        f"Election {election_date} By Mail",
    ]
