from flask import Flask, render_template


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/contests/')
def contests():
    return render_template('contests.html')


if __name__ == '__main__':
    app.run(debug=True)
