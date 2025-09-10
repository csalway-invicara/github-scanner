import os
import sqlite3
from datetime import datetime, timezone

from dotenv import load_dotenv

from libs.github import get_branches, get_org_repositories, get_commit_data, get_tree

load_dotenv()

GITHUB_ORG = os.getenv('GITHUB_ORG')
API_TOKEN = os.getenv('API_FINE_GRAINED_TOKEN')
DB_FILEPATH = os.getenv('DB_FILEPATH')

now = datetime.now(timezone.utc)

# initialize database
con = sqlite3.connect(DB_FILEPATH)
con.row_factory = sqlite3.Row
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS repositories (id INTEGER PRIMARY KEY, repo TEXT NOT NULL, UNIQUE(repo))")
cur.execute("CREATE TABLE IF NOT EXISTS branches (id INTEGER PRIMARY KEY, repo TEXT NOT NULL, branch TEXT NOT NULL, commit_ref TEXT, commit_date TEXT, commit_email TEXT, tree_ref TEXT, UNIQUE(repo,branch))")
cur.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY, repo TEXT NOT NULL, branch TEXT NOT NULL, path TEXT NOT NULL, type TEXT, UNIQUE(repo,branch,path))")

# populate db with repositories
res = cur.execute("SELECT * FROM repositories")
if len(res.fetchall()) == 0:
    for repo in get_org_repositories(API_TOKEN, GITHUB_ORG):
        cur.execute("INSERT INTO repositories (repo) VALUES (?)", [repo['name']])

con.commit()

# populate db with branches
res = cur.execute("SELECT * FROM branches")
if len(res.fetchall()) == 0:
    res = cur.execute("SELECT * FROM repositories")
    for repo in res.fetchall():
        for branch in get_branches(API_TOKEN, GITHUB_ORG, repo['repo']):
            print(f"{repo['repo']}/{branch['name']}")
            cur.execute("INSERT INTO branches (repo,branch,commit_ref) VALUES (?,?,?)", [repo['repo'], branch['name'], branch['commit']['sha']])

con.commit()

# update branches commit data
res = cur.execute("SELECT * FROM branches WHERE tree_ref IS NULL")
for branch in res.fetchall():
    response = get_commit_data(API_TOKEN, GITHUB_ORG, branch['repo'], branch['commit_ref'])
    commit = response['commit']
    committer = commit['committer']
    tree = commit['tree']
    print(f"{branch['repo']}/{branch['branch']} {committer['date']} <{committer['email']}> {tree['sha']}")
    cur.execute("UPDATE branches SET commit_date=?,commit_email=?,tree_ref=? WHERE id=?", [committer['date'], committer['email'], tree['sha'], branch['id']])
    con.commit()

# get a list of files for each branch
res = cur.execute("SELECT b.* FROM branches AS b LEFT JOIN files AS f USING(repo,branch) WHERE f.id IS NULL")
for branch in res.fetchall():
    response = get_tree(API_TOKEN, GITHUB_ORG, branch['repo'], branch['tree_ref'])
    for obj in response['tree']:
        if obj['type'] == 'tree':  # subdir
            continue
        print(f"{branch['repo']}/{branch['branch']} [{obj['type']}] {obj['path']}")
        cur.execute("INSERT INTO files (repo,branch,path,type) VALUES (?,?,?,?)", [branch['repo'], branch['branch'], obj['path'], obj['type']])
    con.commit()

# close db connection
con.close
