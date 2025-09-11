import os
import sqlite3
import time
from datetime import datetime

from dotenv import load_dotenv

from libs.github import (get_branches, get_commit_data, get_org_repositories,
                         get_rate_limit, get_tree)

load_dotenv()

GITHUB_ORG = os.getenv('GITHUB_ORG')
API_TOKEN = os.getenv('API_PERSONAL_TOKEN')
DB_FILEPATH = os.getenv('DB_FILEPATH')


def api_rate_limit_check():
    while 1:
        rate = get_rate_limit(API_TOKEN)['rate']
        if rate['remaining'] > 0:
            break
        resets = datetime.fromtimestamp(int(rate['reset']))
        seconds_until_reset = int((resets - datetime.now()).total_seconds())
        print(f"No more API calls available. Waiting {seconds_until_reset} seconds until {resets.strftime('%Y-%m-%d %H:%M:%S')}.")
        time.sleep(seconds_until_reset + 5)  # add a buffer
    return


con = sqlite3.connect(DB_FILEPATH)
con.row_factory = sqlite3.Row
cur = con.cursor()

# initialize database
cur.execute("CREATE TABLE IF NOT EXISTS repositories (id INTEGER PRIMARY KEY, repo TEXT NOT NULL, UNIQUE(repo))")
cur.execute("CREATE TABLE IF NOT EXISTS branches (id INTEGER PRIMARY KEY, repo TEXT NOT NULL, branch TEXT NOT NULL, commit_ref TEXT, commit_date TEXT, commit_name TEXT, commit_email TEXT, tree_ref TEXT, UNIQUE(repo,branch))")
cur.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY, repo TEXT NOT NULL, branch TEXT NOT NULL, path TEXT NOT NULL, type TEXT, UNIQUE(repo,branch,path))")

# populate db with repositories (1 api call) and branches (1 api call per repo - circa 209)
answer = input("Do you want to refresh the repositories table? (y/n): ")
if answer.strip().lower() == "y":
    cur.execute("DELETE FROM branches")
    cur.execute("DELETE FROM repositories")
    repos = get_org_repositories(API_TOKEN, GITHUB_ORG)
    for repo in repos:
        print(f"Adding repository `{repo['name']}`")
        cur.execute("INSERT INTO repositories (repo) VALUES (?)", [repo['name']])
        branches = get_branches(API_TOKEN, GITHUB_ORG, repo['name'])
        for branch in branches:
            print(f"Adding branch {repo['name']}/{branch['name']}")
            cur.execute("INSERT INTO branches (repo,branch,commit_ref) VALUES (?,?,?)", [repo['name'], branch['name'], branch['commit']['sha']])
        print(f"Added {len(branches)} branches.")
        con.commit()
    print(f"Added {len(repos)} repositories.")

# update branches commit data (1 api call per branch - circa 8000  Nb: api rate-limit 5000req/hr)
res = cur.execute("SELECT * FROM branches WHERE tree_ref IS NULL")
for branch in res.fetchall():
    api_rate_limit_check()
    response = get_commit_data(API_TOKEN, GITHUB_ORG, branch['repo'], branch['commit_ref'])
    commit = response['commit']
    committer = commit['committer']
    tree = commit['tree']
    print(f"Updating branch commit info for {branch['repo']}/{branch['branch']}: {committer['date']} {committer['name']} <{committer['email']}> {tree['sha']}")
    cur.execute("UPDATE branches SET commit_date=?,commit_name=?,commit_email=?,tree_ref=? WHERE id=?", [committer['date'], committer['name'], committer['email'], tree['sha'], branch['id']])
    con.commit()

# get a list of files for each branch (1 api call per branch - circa 8000  Nb: api rate-limit 5000req/hr)
res = cur.execute("SELECT b.* FROM branches AS b LEFT JOIN files AS f USING(repo,branch) WHERE f.id IS NULL")
for branch in res.fetchall():
    api_rate_limit_check()
    response = get_tree(API_TOKEN, GITHUB_ORG, branch['repo'], branch['tree_ref'])
    for obj in response['tree']:
        if obj['type'] == 'tree':  # subdir
            continue
        print(f"Adding file to {branch['repo']}/{branch['branch']}: [{obj['type']}] {obj['path']}")
        cur.execute("INSERT INTO files (repo,branch,path,type) VALUES (?,?,?,?)", [branch['repo'], branch['branch'], obj['path'], obj['type']])
    con.commit()

# close db connection
con.close
