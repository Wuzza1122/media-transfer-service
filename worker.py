# worker.py
from redis import Redis
from rq import Queue, Worker, Connection
import os

# 👇 Ensure this import matches your filename and function name
from youtube_upload import upload_to_youtube

# ✅ Connect to Redis
redis_url = os.getenv("REDIS_URL")  # Should be rediss://... from Upstash
conn = Redis.from_url(redis_url)

if __name__ == '__main__':
    print("👷 Worker starting...")

    # ✅ Just importing `upload_to_youtube` makes it discoverable
    with Connection(conn):
        worker = Worker(["default"])
        worker.work()
