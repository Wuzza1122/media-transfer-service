import os
from redis import Redis
from rq import Worker, Queue, Connection

# ✅ Import your job function(s) here
from youtube_upload import upload_to_youtube

listen = ['default']
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = Redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        print("🎧 Worker connected and listening for jobs...")
        worker = Worker(list(map(Queue, listen)))
        worker.work()
