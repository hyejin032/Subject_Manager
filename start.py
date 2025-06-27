from flask import Flask

app = Flask("JobScrapper")

@app.route("/")
def home():
  return 'Hello Flask!'

app.run("0.0.0.0")