from .celerypeak import gettimecodes

from flask import Flask, render_template, url_for, request

app = Flask(__name__)


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
    print(video_id)
    gettimecodes.delay(video_id)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)