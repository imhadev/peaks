import os
import sys
import requests
import re
import redis

sys.path.append(os.getcwd())

from flask import Flask, render_template, request
from celery import Celery


app = Flask(__name__)
celery = Celery(broker='redis://localhost:6379/0')
r = redis.StrictRedis(host='localhost', port=6379, db=0)


@app.route("/")
@app.route("/home")
def home():
    return render_template('index.html')


@app.route("/about")
def about():
    return render_template('about.html')


@app.route("/submit", methods=['POST'])
def submit():
    video_id = request.form['email_link']

    if (r.get(video_id)):
        timestampsres = r.get(video_id)
        print(timestampsres)
    else:
        peakfunc.delay(video_id)
        print('come back in 30 mins')

    return render_template('index.html')


@celery.task(name='__main__.peakfunc')
def peakfunc(video_id):
    timestamps = load_timestamps(f'https://www.twitch.tv/videos/{video_id}')
    str1 = ' '.join(str(e) for e in timestamps)
    r.set(video_id, str1)


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


if __name__ == '__main__':
    app.run(debug=True)
