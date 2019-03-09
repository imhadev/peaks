import requests
import re

from celery import Celery

app = Celery(broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

@app.task
def gettimecodes(video_id):
    timestamps = load_timestamps(f'https://www.twitch.tv/videos/{video_id}')
    return timestamps


def load_portion(video_id, cursor=None):
    if cursor:
        params = {'cursor': cursor}
    else:
        params = {}

    response = requests.get(
        url=f'https://api.twitch.tv/v5/videos/{video_id}/comments',
        params=params,
        headers={
            'Client-ID': 'ccn4gx4qj2tnvd2zpy1vkhmlkn0hg6',
        },
    )

    parsed_response = response.json()

    comments = parsed_response.get('comments')
    timestamps = [comment['content_offset_seconds'] for comment in comments]

    next_cursor = parsed_response.get('_next')

    return timestamps, next_cursor


def load_timestamps(url):
    if not url:
        return []

    match = re.search(r'^.*www\.twitch\.tv\/videos\/(\d+)$', url)

    if not match:
        return []

    video_id = match[1]
    timestamps = []

    timestamps_portion, next_cursor = load_portion(video_id)
    timestamps.extend(timestamps_portion)

    # while next_cursor and timestamps_portion:
    #     timestamps_portion, next_cursor = load_portion(video_id, next_cursor)
    #     timestamps.extend(timestamps_portion)
    #     print(timestamps[-1])

    return timestamps
