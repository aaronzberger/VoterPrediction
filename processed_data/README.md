# Full PA Data: V1.0 (all elections)

This directory contains one file for each election, but the headers for all files are the same.

Each county stores the voting history of all voters for 40 elections, but these 40 vary for each county.
This version of the data processing takes the union of all of these election dates and stores them for every county.
For each election, there exists a feature presence column indicating whether that county stored that election's data.

In some cases, multiple elections were stored on the same date (for example, in Allegneny county).
These elections involved disjoint sets of voters (districts within the county) and were thus merged into a single election.
However, the feature presence column is set to 1 for the entire county, since the county stored data for that date
(even though some voters may not have had the opportunity to vote in that election).

The file `pa_data_all_elections_sample.csv` contains a sample of 10\% of all the data (sampled from each county).
This totals a bit under a million voters, and can be used for further sampling and data visualization. The entire file cannot be generated easily since it is too large to fit in memory.

The file `elections.json` is not unique to this version of the data, but maps each election date to the varying titles used for that election in each county.
Most of these differences are simply due to differing naming convention, but some involve disjoint districts voting on the same day for differently named elections.

## Future
Future versions may do the following:
 - eliminate elections which are not very present in many counties
 - more accurately mark feature presence columns based on the description of the election and the individual voter districts, although this may require significant effort
 - include more demographic data which was left out of this version for simplicity (districts of voters, address and other location date, etc.)

## Access
Files which are not in the Github repo are in Google Drive to save space. See [here](https://drive.google.com/drive/folders/1LfXkXtt8WQvSNmtZzysS29DO0yvEy7w-?usp=sharing)