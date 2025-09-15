import requests
from requests import Response
import time
from datetime import datetime


def get_rate_limit(api_token):
    # https://docs.github.com/en/rest/rate-limit/rate-limit?apiVersion=2022-11-28#get-rate-limit-status-for-the-authenticated-user
    url = "https://api.github.com/rate_limit"
    response = requests.get(url, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {api_token}"
    })
    response.raise_for_status()
    return response.json()


def wait_rate_limit(api_token):
    while 1:
        rate = get_rate_limit(api_token)['rate']
        if rate['remaining'] > 0:
            break
        resets = datetime.fromtimestamp(int(rate['reset']))
        seconds_until_reset = int((resets - datetime.now()).total_seconds())
        print(
            f"No more API calls available. Waiting {seconds_until_reset} seconds until {resets.strftime('%Y-%m-%d %H:%M:%S')}.")
        time.sleep(seconds_until_reset + 5)  # add a buffer
    return


def get_response(api_token, url, hdrs={}) -> Response:
    # https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api?apiVersion=2022-11-28
    wait_rate_limit(api_token)
    response = requests.get(url, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {api_token}"
    } | hdrs)  # This method updates the original dictionary (python 3.9+)
    response.raise_for_status()
    return response


def split_link_header(link_header):
    # https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api?apiVersion=2022-11-28#using-link-headers
    parts = link_header.split(',')
    links = {}
    for part in parts:
        section = part.strip().split(';')
        if len(section) == 2:
            url = section[0].strip()[1:-1]  # Remove < and >
            rel = section[1].strip().split('=')[1].strip('"')
            links[rel] = url
    return links


def get_paged_response(api_token, url, key=None) -> dict | list:
    # https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api?apiVersion=2022-11-28
    response = get_response(api_token, url)
    data = response.json()  # list or dict
    while 'link' in response.headers:
        links = split_link_header(response.headers['link'])
        if 'next' not in links:
            break
        response = get_response(api_token, links['next'])
        if isinstance(data, list):
            data.extend(response.json())
        elif key is not None and key in data and isinstance(data[key], list):
            data[key].extend(response.json())
    return data


def get_org_repositories(api_token, org):
    # https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#list-organization-repositories
    url = f"https://api.github.com/orgs/{org}/repos?per_page=100&page=1"
    return get_paged_response(api_token, url)


def get_branches(api_token, owner, repo):
    # https://docs.github.com/en/rest/branches/branches?apiVersion=2022-11-28#list-branches
    url = f"https://api.github.com/repos/{owner}/{repo}/branches?per_page=100&page=1"
    return get_paged_response(api_token, url)


def get_commit_data(api_token, owner, repo, ref, key='files') -> dict | list:
    # https://docs.github.com/en/rest/commits/commits?apiVersion=2022-11-28#get-a-commit
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{ref}?per_page=100&page=1"
    return get_paged_response(api_token, url, key)


def get_tree(api_token, owner, repo, tree_sha):
    # https://docs.github.com/en/rest/git/trees?apiVersion=2022-11-28#get-a-tree
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1"
    response = get_response(api_token, url)
    return response.json()


def get_file_content(api_token, owner, repo, branch, path):
    # https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28#get-repository-content
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    response = get_response(api_token, url, hdrs={
        "Accept": "application/vnd.github.raw+json"
    })
    return response.content  # binary data
