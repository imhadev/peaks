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
    "MAIL_PASSWORD": '********'
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


@app.route("/chart/<videoid>")
def chart(videoid):
    timestampsres = r.get(videoid).decode("utf-8")
    timestampsresvalues = timestampsres.split()
    return render_template('chart.html', values=timestampsresvalues)


@app.route("/videoresult", methods=['POST'])
def videoresult():
    video_id = request.form['videoid']

    if (video_id):
        if (r.get(video_id).decode("utf-8") == '-1'):
            flash('video is processing', category='info')
        else:
            return redirect(url_for('chart', videoid=video_id))
    else:
        flash('invalid video id', category='warning')

    return render_template('index.html')


@app.route("/mailcode", methods=['POST'])
def mailcode():
    email_link = request.form['emaillink']

    if (email_link):
        if (r.get(email_link)):
            flash('too many requests', category='warning')
        else:
            flash('codes were sent to your email', category='success')
            sendmail.delay(email_link)
            r.set(email_link, 1)
    else:
        flash('invalid email', category='warning')

    return render_template('index.html')


@app.route("/videocode", methods=['POST'])
def videocode():
    video_id = request.form['videoid']
    video_code = request.form['videocode']

    r.set(video_id, -1)
    peakfunc.delay(video_id)

    # if (video_id) and (video_code):
    #     if (r.get(video_code)):
    #         r.delete(video_code)
    #         peakfunc.delay(video_id)
    #         flash('video is processing, come back later to check the result', category='success')
    #     else:
    #         flash('invalid video code', category='warning')
    # else:
    #     flash('invalid video id or code', category='warning')

    return render_template('index.html')


@celery.task(name='__main__.peakfunc')
def peakfunc(video_id):
    timestamps = load_timestamps(f'https://www.twitch.tv/videos/{video_id}')
    # str1 = ' '.join(str(e) for e in timestamps)
    r.set(video_id, timestamps)


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

    combody = []
    for comment in comments:
        combody.append(comment['message']['body'].lower() + ' ' + str(comment['content_offset_seconds']))

    timestampscof1 = []
    timestampscof2 = []
    cof = 3

    lastcomment = comments[-1]
    lastoffset = lastcomment['content_offset_seconds']

    print(lastoffset)
    print('...')

    for i in range(int(lastoffset / cof) + 1):
        timestampscof1.append(0)
        timestampscof2.append(0)

    for comment in comments:
        timestampscof1[int(comment['content_offset_seconds'] / cof)] += 1
        if 'pog' in comment['message']['body'].lower() or \
                'lul' in comment['message']['body'].lower() or \
                'chomp' in comment['message']['body'].lower() or \
                'pag' in comment['message']['body'].lower():
            timestampscof2[int(comment['content_offset_seconds'] / cof)] += 1

    print(combody)
    print('...')
    print(timestampscof1)
    print('...')
    print(timestampscof2)
    print('...')

    for x in range(len(timestampscof1)):
        if timestampscof1[x] != 0:
            timestampscof1[x] = timestampscof1[x] * (timestampscof2[x] / timestampscof1[x] / 2 + 1)

    print(timestampscof1)
    print('-----------------------')

    next_cursor = parsed_response.get('_next')

    return timestampscof1, next_cursor


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

    for p in range(2):
        timestamps_portion, next_cursor = load_portion(video_id, next_cursor)
        timestamps.extend(timestamps_portion)

    # while next_cursor and timestamps_portion:
    #     timestamps_portion, next_cursor = load_portion(video_id, next_cursor)
    #     timestamps.extend(timestamps_portion)

    timestampscheck = []
    sum = 0

    for x in range(len(timestamps)):
        timestampscheck.append(True)
        sum = sum + timestamps[x]

    avg = sum / len(timestamps)

    coftop = 2
    peakresult = ''
    numpeaks = 0
    f = True
    while (numpeaks < 10) and (f):

        peakresultar = []
        peakresultidar = []
        maxp = 0
        i = 0
        for x in range(len(timestamps)):
            if (timestamps[x] > maxp) and (timestampscheck[x]):
                maxp = timestamps[x]
                i = x

        if (maxp <= avg):
            f = False
        else:
            timestampscheck[i] = False
            peakresultar.append(timestamps[i])
            peakresultidar.append(i)
            peaklen = 1
            qleft = i - 1
            qright = i + 1
            g = True
            while (peaklen <= 12) and (g):
                if (qleft < 0) and (qright >= len(timestamps)):
                    g = False
                else:
                    if (qleft < 0):
                        if (timestamps[qright] * coftop >= maxp):
                            timestampscheck[qright] = False
                            peakresultar.append(timestamps[qright])
                            peakresultidar.append(qright)
                            peaklen += 1
                            qright += 1
                        else:
                            g = False
                    elif (qright >= len(timestamps)):
                        if (timestamps[qleft] * coftop >= maxp):
                            timestampscheck[qleft] = False
                            peakresultar.append(timestamps[qleft])
                            peakresultidar.append(qleft)
                            peaklen += 1
                            qleft -= 1
                        else:
                            g = False
                    else:
                        if (timestamps[qleft] > timestamps[qright]):
                            if (timestamps[qleft] * coftop >= maxp):
                                timestampscheck[qleft] = False
                                peakresultar.append(timestamps[qleft])
                                peakresultidar.append(qleft)
                                peaklen += 1
                                qleft -= 1
                            else:
                                g = False
                        else:
                            if (timestamps[qright] * coftop >= maxp):
                                timestampscheck[qright] = False
                                peakresultar.append(timestamps[qright])
                                peakresultidar.append(qright)
                                peaklen += 1
                                qright += 1
                            else:
                                g = False

            minl = -1
            maxr = -1
            for id in peakresultidar:
                if (minl == -1) or id < minl:
                    minl = id

            for id in peakresultidar:
                if (maxr == -1) or id > maxr:
                    maxr = id

            peaksum = 0
            for res in peakresultar:
                peaksum = peaksum + res

            peakavg = peaksum / len(peakresultar)

            peakresult = peakresult + str(minl) + ' ' + str(maxr) + ' ' + str(peakavg) + ' '
            numpeaks += 1

    return peakresult


@celery.task(name='__main__.sendmail')
def sendmail(email_link):
    code1 = id_generator()
    code2 = id_generator()
    r.set(code1, 1)
    r.set(code2, 1)

    with app.app_context():
        msg = Message('Hello', sender='peakserviceofficial@gmail.com', recipients=[email_link])
        msg.body = "Your codes are " + code1 + ", " + code2
        mail.send(msg)


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


if __name__ == '__main__':
    app.run(debug=True)
