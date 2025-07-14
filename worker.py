import os
from redis import Redis
from rq import Worker, Queue, Connection

# 📦 Import job functions
from youtube_upload import upload_to_youtube

# 🔧 Redis Connection
redis_url = os.getenv("REDIS_URL")
redis_conn = Redis.from_url(redis_url)
queue = Queue(connection=redis_conn)

# 🎯 Start worker process
if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker([queue])
        worker.work()
