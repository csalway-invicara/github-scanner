# Github Scanner

## Notes

- Github has a rate-limit set of 5000 requests per hour - which you will hit often!
- A complete database (as of 10 Sep 2025) can be downloaded from [One Drive](https://invicara-my.sharepoint.com/:u:/p/christian_salway/EcpXFfNILjZJv46fOYfW51UBOzVEPgcjGw6M5YCqvOlAZA?e=cbd0vd)
- You can run `python rate_limit_checker.py` to see if you have any remaining api calls

## Setup

Create a `.env` file in the root with the following keys:

```
GITHUB_ORG="Invicara"
API_PERSONAL_TOKEN="<generate a Token (classic) with `repo` and `read:org` scopes>"
API_FINE_GRAINED_TOKEN="<generate a Fine-grained token for All repositories with 'Contents' read-only and 'Metadata' read-only>"
DB_FILEPATH="db/github-invicara.db"
```

Create a python virtual environment:

```
 python -m venv .venv
 source .venv/bin/activate
 python -m pip install -U pip
 python -m pip install -r requirements.txt
 ```

Populate the database first by running `python populate_database.py` -  you will have to run this several times as GitHub API is rate-limited to 5000 req/hr.

Then run `python get_files.py` to download the required file (specified in `PATH_PATTERN`) from all branches in all repo's.

## Running

Update the package list (`packages`) in `scan_files.py` and then run `python scan_files.py`. Results will be printed.

