import os
from datetime import datetime

from dotenv import load_dotenv

from libs.github import get_rate_limit

load_dotenv()

API_TOKEN = os.getenv('API_FINE_GRAINED_TOKEN')

rate = get_rate_limit(API_TOKEN)['rate']

resets = datetime.fromtimestamp(int(rate['reset'])).strftime('%Y-%m-%d %H:%M:%S')

print(f"limit: {rate['limit']}, used: {rate['used']}, remaining: {rate['remaining']}, resets: {resets}")
