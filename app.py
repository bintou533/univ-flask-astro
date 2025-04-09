from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/appareil_photo')
def appareil_photo():
    return render_template('appareil_photo.html')

@app.route('/telescope')
def telescope():
    return render_template('telescope.html')

@app.route('/photographies')
def photographies():
    return render_template('photographies.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)