from redis import Redis
from rq import Queue
from youtube_upload import upload_to_youtube

import os

redis_url = os.getenv("REDIS_URL")
redis_conn = Redis.from_url(redis_url)
queue = Queue(connection=redis_conn)

if __name__ == "__main__":
    # Start worker
    print("👷 Worker starting...")
    from rq import Worker
    Worker([queue], connection=redis_conn).work()
