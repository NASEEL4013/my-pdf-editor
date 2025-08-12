from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/pdf_splitter')
def pdf_splitter_page():
    return render_template('pdf_splitter.html')

if __name__ == '__main__':
    app.run()