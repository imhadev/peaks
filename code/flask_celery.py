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

class hl:
    def __init__(self, leftp, rightp, cofp):
        self.leftp = leftp
        self.rightp = rightp
        self.cofp = cofp

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": 'peakserviceofficial@gmail.com',
    "MAIL_PASSWORD": 'peakpass123'
}

app = Flask(__name__)
app.secret_key = 'my unobvious secret key'
celery = Celery(broker='redis://redis:6379/0')
r = redis.StrictRedis(host='redis', port=6379, db=0)
app.config.update(mail_settings)
mail = Mail(app)


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
        if (r.get(video_id)) and (r.get(video_id).decode("utf-8") != '-1'):
            return redirect(url_for('chart', videoid=video_id))
        elif (r.get(video_id)) and (r.get(video_id).decode("utf-8") == '-1'):
            flash('video is processing', category='info')
        else:
            flash('invalid video id', category='warning')
    else:
        flash('invalid video id', category='warning')

    return render_template('index.html')


@app.route("/mailcode", methods=['POST'])
def mailcode():
    email_link = request.form['emaillink']

    if (email_link):
        if re.match(r'[^@]+@[^@]+\.[^@]+', email_link):
            if (r.get(email_link)):
                flash('too many requests', category='warning')
            else:
                flash('codes were sent to your email', category='success')
                sendmail.delay(email_link)
                r.setex(email_link, 86400, 1)
        else:
            flash('invalid email', category='warning')
    else:
        flash('invalid email', category='warning')

    return render_template('index.html')


@app.route("/videocode", methods=['POST'])
def videocode():
    video_id = request.form['videoid']
    video_code = request.form['videocode']

    if (video_id) and (video_code):
        if (r.get(video_id)) and (r.get(video_id).decode("utf-8") != '-1'):
            flash('video is already processed', category='info')
        elif (r.get(video_id)) and (r.get(video_id).decode("utf-8") == '-1'):
            flash('video is processing', category='info')
        else:
            if (r.get(video_code)):
                if (check(video_id) == 0):
                    flash('invalid video id', category='warning')
                else:
                    r.delete(video_code)
                    r.set(video_id, -1)
                    peakfunc.delay(video_id)
                    flash('video is processing, come back later to check the result', category='success')
            else:
                flash('invalid video code', category='warning')
    else:
        flash('invalid video id or code', category='warning')

    return render_template('index.html')


@celery.task(name='__main__.peakfunc')
def peakfunc(video_id):
    timestamps = load_timestamps(f'https://www.twitch.tv/videos/{video_id}')
    r.setex(video_id, 604800, timestamps)


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
    comtime = []
    for comment in comments:
        combody.append(comment['message']['body'].lower())
        comtime.append(comment['content_offset_seconds'])

    next_cursor = parsed_response.get('_next')

    return combody, comtime, next_cursor


def load_timestamps(url):
    if not url:
        return []

    match = re.search(r'^.*www\.twitch\.tv\/videos\/(\d+)$', url)

    if not match:
        return []

    video_id = match[1]

    combody = []
    comtime = []

    combody_portion, comtime_portion, next_cursor = load_portion(video_id)
    combody.extend(combody_portion)
    comtime.extend(comtime_portion)

    while next_cursor and comtime:
        combody_portion, comtime_portion, next_cursor = load_portion(video_id, next_cursor)
        combody.extend(combody_portion)
        comtime.extend(comtime_portion)

    peakresult = set_cof(combody, comtime)

    return peakresult


def set_cof(combody, comtime):
    timestampscof1 = []
    timestampscof2 = []
    cof = 4

    lastoffset = comtime[-1]

    for i in range(int(lastoffset / cof) + 1):
        timestampscof1.append(0)
        timestampscof2.append(0)

    for j in range(len(combody)):
        timestampscof1[int(comtime[j] / cof)] += 1
        if 'pog' in combody[j] or \
                'lul' in combody[j] or \
                'chomp' in combody[j] or \
                'pag' in combody[j]:
            timestampscof2[int(comtime[j] / cof)] += 1

    for x in range(len(timestampscof1)):
        if timestampscof1[x] != 0:
            timestampscof1[x] = int(timestampscof1[x] * (timestampscof2[x] / timestampscof1[x] / 2 + 1))

    peakresult = get_peakresult(timestampscof1)

    return peakresult


def get_peakresult(timestamps):
    timestampscheck = []
    sum = 0

    for x in range(len(timestamps)):
        timestampscheck.append(True)
        sum = sum + timestamps[x]

    avg = sum / len(timestamps)

    peakresultarar = []
    peakresultavgar = []

    numpeaks = 0
    coftop = 3
    f = True
    while (numpeaks < 10) and f:
        peakresultar = []
        peakresultidar = []
        maxp = 0
        i = 0
        for x in range(len(timestamps)):
            if (timestamps[x] > maxp) and (timestampscheck[x]):
                maxp = timestamps[x]
                i = x

        if (maxp <= avg * 1.3):
            f = False
        else:
            timestampscheck[i] = False
            peakresultar.append(timestamps[i])
            peakresultidar.append(i)
            peaklen = 1
            qleft = i - 1
            qright = i + 1
            g = True
            while (peaklen <= 15) and g:
                if ((qleft < 0) or (timestampscheck[qleft] == False)) and \
                        ((qright >= len(timestamps)) or (timestampscheck[qleft] == qright)):
                    g = False
                else:
                    if (qleft < 0) or (timestampscheck[qleft] == False):
                        if (timestamps[qright] * coftop >= maxp):
                            timestampscheck[qright] = False
                            peakresultar.append(timestamps[qright])
                            peakresultidar.append(qright)
                            peaklen += 1
                            qright += 1
                        else:
                            g = False
                    elif (qright >= len(timestamps)) or (timestampscheck[qright] == False):
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
            for idp in peakresultidar:
                if (minl == -1) or idp < minl:
                    minl = idp

            for idp in peakresultidar:
                if (maxr == -1) or idp > maxr:
                    maxr = idp

            peaksum = 0
            for res in peakresultar:
                peaksum = peaksum + res

            if (len(peakresultar) == 0):
                peakavg = int(peaksum / 1)
            else:
                peakavg = int(peaksum / len(peakresultar))

            highlightel = hl(minl, maxr, peakavg)
            peakresultarar.append(highlightel)

            numpeaks += 1

    peakresultarar.sort(key=lambda xxx: xxx.leftp)

    start = 0
    if (len(peakresultarar) > 0):
        end = peakresultarar[0].leftp
    else:
        end = 0
    sumavg = 0
    for q in range(start, end):
        sumavg += timestamps[q]
    if (end - start == 0):
        avgavg = int(sumavg / 1)
    else:
        avgavg = int(sumavg / (end - start))
    highlightel = hl(start, end, avgavg)
    peakresultavgar.append(highlightel)

    for t in range(len(peakresultarar)):
        sumavg = 0
        start = peakresultarar[t].rightp + 1
        if (t == (len(peakresultarar) - 1)):
            end = len(timestamps)
        else:
            end = peakresultarar[t + 1].leftp

        for q in range(start, end):
            sumavg += timestamps[q]

        if (end - start == 0):
            avgavg = int(sumavg / 1)
        else:
            avgavg = int(sumavg / (end - start))
        highlightel = hl(start, end, avgavg)
        peakresultavgar.append(highlightel)

    peakresult = ''
    peakresult = peakresult + str(peakresultavgar[0].leftp) + ' ' + str(peakresultavgar[0].rightp) + ' ' + str(peakresultavgar[0].cofp) + ' '

    for z in range(len(peakresultarar)):
        peakresult = peakresult + str(peakresultarar[z].leftp) + ' ' + str(peakresultarar[z].rightp) + ' ' + str(peakresultarar[z].cofp) + ' ' + str(peakresultavgar[z + 1].leftp) + ' ' + str(peakresultavgar[z + 1].rightp) + ' ' + str(peakresultavgar[z + 1].cofp) + ' '

    return peakresult


@celery.task(name='__main__.sendmail')
def sendmail(email_link):
    code1 = id_generator()
    code2 = id_generator()

    f1 = True
    f2 = True

    while (f1):
        if (r.get(code1)):
            code1 = id_generator()
        else:
            r.setex(code1, 604800, 1)
            f1 = False

    while (f2):
        if (r.get(code2)):
            code2 = id_generator()
        else:
            r.setex(code2, 604800, 1)
            f2 = False

    with app.app_context():
        msg = Message('Hello', sender='peakserviceofficial@gmail.com', recipients=[email_link])
        msg.body = "Your codes are " + code1 + ", " + code2
        mail.send(msg)


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def check(video_id):
    params = {}

    response = requests.get(
        url=f'https://api.twitch.tv/v5/videos/{video_id}/comments',
        params=params,
        headers={
            'Client-ID': 'ccn4gx4qj2tnvd2zpy1vkhmlkn0hg6',
        },
    )

    parsed_response = response.json()
    if (parsed_response.get('error') == 'Bad Request'):
        return 0
    else:
        return 1


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
