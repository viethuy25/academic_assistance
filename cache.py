from functools import lru_cache
import time
import json
from config import CACHE_EXPIRATION
import asyncio

class TimedCache:
    def __init__(self):
        self.cache = {}

    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < CACHE_EXPIRATION:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key, value):
        self.cache[key] = (value, time.time())

    def save_to_file(self, filename):
        with open(filename, 'w') as f:
            json.dump({k: v[0] for k, v in self.cache.items()}, f)

    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.cache = {k: (v, time.time()) for k, v in data.items()}
        except FileNotFoundError:
            pass

paper_cache = TimedCache()

# Load cache from file on startup
paper_cache.load_from_file('paper_cache.json')

def save_paper_summary(title, summary_data):
    paper_cache.set(title, summary_data)
    paper_cache.save_to_file('paper_cache.json')

def get_paper_summary(title):
    return paper_cache.get(title)

async def dict_to_async_generator(data_dict):
    for key, value in data_dict.items():
        yield key, value
        await asyncio.sleep(0)  # Optional: Yield control to event loop

