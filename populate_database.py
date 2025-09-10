import os
import sqlite3

from dotenv import load_dotenv

from libs.github import get_branches, get_commit_data, get_org_repositories, get_tree

load_dotenv()

GITHUB_ORG = os.getenv('GITHUB_ORG')
API_TOKEN = os.getenv('API_PERSONAL_TOKEN')
DB_FILEPATH = os.getenv('DB_FILEPATH')

con = sqlite3.connect(DB_FILEPATH)
con.row_factory = sqlite3.Row
cur = con.cursor()

# initialize database
cur.execute("CREATE TABLE IF NOT EXISTS repositories (id INTEGER PRIMARY KEY, repo TEXT NOT NULL, UNIQUE(repo))")
cur.execute("CREATE TABLE IF NOT EXISTS branches (id INTEGER PRIMARY KEY, repo TEXT NOT NULL, branch TEXT NOT NULL, commit_ref TEXT, commit_date TEXT, commit_email TEXT, tree_ref TEXT, UNIQUE(repo,branch))")
cur.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY, repo TEXT NOT NULL, branch TEXT NOT NULL, path TEXT NOT NULL, type TEXT, UNIQUE(repo,branch,path))")

# populate db with repositories (1 api call)
answer = input("Do you want to refresh the repositories table? (y/n): ")
if answer.strip().lower() == "y":
    cur.execute("DELETE FROM repositories")
    repos = get_org_repositories(API_TOKEN, GITHUB_ORG)
    for repo in repos:
        print(f"Adding repository `{repo['name']}`")
        cur.execute("INSERT INTO repositories (repo) VALUES (?)", [repo['name']])
        con.commit()
    print(f"Loaded {len(repos)} repositories.")

# populate db with branches (1 api call per repository - circa 209)
answer = input("Do you want to refresh the branches table? (y/n): ")
if answer.strip().lower() == "y":
    cur.execute("DELETE FROM branches")
    res = cur.execute("SELECT * FROM repositories")
    for repo in res.fetchall():
        branches = get_branches(API_TOKEN, GITHUB_ORG, repo['repo'])
        for branch in branches:
            print(f"Adding branch {repo['repo']}/{branch['name']}")
            cur.execute("INSERT OR IGNORE INTO branches (repo,branch,commit_ref) VALUES (?,?,?)", [repo['repo'], branch['name'], branch['commit']['sha']])
            con.commit()
        print(f"Loaded {len(branches)} branches into {repo['repo']} repository.")

# update branches commit data (1 api call per branch - branch count (>8000) is greater than api rate-limit (5000/hr), so you will have to re-run this script for the following to complete)
res = cur.execute("SELECT * FROM branches WHERE tree_ref IS NULL")
for branch in res.fetchall():
    response = get_commit_data(API_TOKEN, GITHUB_ORG, branch['repo'], branch['commit_ref'])
    commit = response['commit']
    committer = commit['committer']
    tree = commit['tree']
    print(f"{branch['repo']}/{branch['branch']} {committer['date']} <{committer['email']}> {tree['sha']}")
    cur.execute("UPDATE branches SET commit_date=?,commit_email=?,tree_ref=? WHERE id=?", [committer['date'], committer['email'], tree['sha'], branch['id']])
    con.commit()

# get a list of files for each branch (1 api call per branch - branch count (>8000) is greater than api rate-limit (5000/hr), so you will have to re-run this script for the following to complete)
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
