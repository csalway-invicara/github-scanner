import os
import sqlite3

from dotenv import load_dotenv
from libs.github import get_file_content

load_dotenv()

GITHUB_ORG = os.getenv('GITHUB_ORG')
API_TOKEN = os.getenv('API_PERSONAL_TOKEN')  # ensure 'repo' is selected for permissions
DB_FILEPATH = os.getenv('DB_FILEPATH')
PATH_PATTERN = '%package-lock.json%'  # in sql format

con = sqlite3.connect(DB_FILEPATH)
con.row_factory = sqlite3.Row
cur = con.cursor()

# download all relevant files
res = cur.execute(f"SELECT * FROM files WHERE path LIKE '{PATH_PATTERN}'")
for file in res.fetchall():
    filesdir = "./files"
    filepath = f"{file['repo']}/{file['branch']}/{file['path']}"
    filedir = f"{filesdir}/{os.path.dirname(filepath)}"
    print(f"Downloading {filepath}...")
    if os.path.isfile(f"{filesdir}/{filepath}"):
        print("File already downloaded. Skipping.")
        continue
    os.makedirs(filedir, exist_ok=True)
    try:
        content = get_file_content(API_TOKEN, GITHUB_ORG, file['repo'], file['branch'], file['path'])
        with open(f"{filesdir}/{filepath}", 'wb') as f:
            f.write(content)
    except Exception as e:
        print(e)

con.close()
