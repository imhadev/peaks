import os
import sys
import requests
import re
import redis
import string
import random

sys.path.append(os.getcwd())

from flask import Flask, render_template, request, flash, redirect, url_for
from flask_mail import Mail, Message
from celery import Celery


mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": 'peakserviceofficial@gmail.com',
    "MAIL_PASSWORD": '*********'
}

app = Flask(__name__)
app.secret_key = 'my unobvious secret key'
celery = Celery(broker='redis://localhost:6379/0')
r = redis.StrictRedis(host='localhost', port=6379, db=0)
app.config.update(mail_settings)
mail = Mail(app)


@app.route("/test")
def test():
    return render_template('test.html')


@app.route("/")
@app.route("/home")
def home():
    return render_template('index.html')


@app.route("/about")
def about():
    return render_template('about.html')


@app.route("/chart")
def chart():
    labels = ["January","February","March","April","May","June","July","August"]
    values = [10,9,8,7,6,4,7,8]
    return render_template('chart.html', values=values, labels=labels)


@app.route("/videocode", methods=['POST'])
def videocode():
    video_id = request.form['videoid']
    video_code = request.form['videocode']

    if (r.get(video_id)):
        timestampsres = r.get(video_id)
        return redirect(url_for('chart'))
    else:
        if (r.get(video_code)):
            r.delete(video_code)
            peakfunc.delay(video_id)
            flash('come back in 30 mins', category='success')
        else:
            flash('video code is wrong', category='warning')

    return render_template('test.html')


@app.route("/mailcode", methods=['POST'])
def mailcode():
    email_link = request.form['emaillink']

    if (r.get(email_link)):
        if (int(r.get(email_link)) >= 2):
            flash('too many requests', category='warning')
        else:
            flash('code was sent to your email', category='success')
            sendmail.delay(email_link)
            r.set(email_link, 2)
    else:
        flash('code was sent to your email', category='success')
        sendmail.delay(email_link)
        r.set(email_link, 1)

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


@celery.task(name='__main__.sendmail')
def sendmail(email_link):
    code = id_generator()
    r.set(code, 1)

    with app.app_context():
        msg = Message('Hello', sender='peakserviceofficial@gmail.com', recipients=[email_link])
        msg.body = "Your code is " + code
        mail.send(msg)


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


if __name__ == '__main__':
    app.run(debug=True)
