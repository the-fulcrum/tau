from flask import Flask, render_template, request, Markup, redirect
import sqlite3
import json
import hashlib
import time
from flask_cors import CORS
import subprocess
from os.path import exists

app = Flask(__name__)
CORS(app)

class Question():
    def __init__(self, l, index):
        self.title = l[index].split(",")[0]
        self.year = int(l[index].split(",")[1])
        self.difficulty = l[index].split(",")[2]
        self.topic = l[index].split(",")[3]
        self.question = l[index+1]

def dataProcess(data):
    print(data)
    splitData = data.split("@qn@")
    splitData = [datum for datum in splitData if datum != ""]
    return [Question(splitData, i) for i in range(0, len(splitData), 2)]

@app.route('/')
def searchPage():
    token = request.cookies.get("token")
    database = sqlite3.connect('questions.db')
    sqlData = (token,)
    details = database.execute(
        "SELECT username FROM Session INNER JOIN User ON Session.userhash = User.userhash WHERE Session.session_token = ?",
        sqlData).fetchone()
    print(details)
    if details == None:
        details = ("",)
    return render_template('index.html', data=details)

@app.route('/results', methods=['POST', 'GET'])
def resultsPage():
    search = request.form['search'].strip().split(' ')
    data = ()
    string = "SELECT * from Question;"
    substring = 0
    """while substring < len(search) and search[substring] not in ["-t", "-d", "-y"]:
        string = string + "processed_question LIKE ? OR "
        data = data + ("%" + search[substring] + "%",)
        substring += 1"""
    """for i in range(0, len(search)):
        registerData = False
        if search[i] == "-t":
            data = data + (search[i + 1],)
            string = string + "'topic' = ? AND "
        elif search[i] == "-d":
            data = data + (search[i + 1],)
            string = string + "'difficulty' = ? AND "
        elif search[i] == "-y":
            data = data + (int(search[i + 1]),)
            string = string + "'year' = ? AND "
    sqlData = data"""
    database = sqlite3.connect('questions.db')
    cursor = database.cursor()
    print(string)
    cursor.execute(string)
    returnData = cursor.fetchall()
    print(returnData)
    token = request.cookies.get("token")
    sqlData = (token,)
    details = database.execute(
        "SELECT username FROM Session INNER JOIN User ON Session.userhash = User.userhash WHERE Session.session_token = ?",
        sqlData).fetchone()
    if details == None:
        details = ("",)
    #returnData = rapidfuzz.process.extract(data['search'], returnData, limit=20, processor=lambda x: x[0])
    #style results.html
    return render_template('results.html', data=(returnData, details[0]))

@app.route('/contributions', methods=['GET'])
def contributions():
    token = request.cookies.get("token")
    database = sqlite3.connect('questions.db')
    sqlData = (token,)
    userhash = database.execute(
        "SELECT userhash FROM Session WHERE session_token = ?",
        sqlData).fetchone()
    contributions = database.execute(
        "SELECT * FROM Question WHERE userhash = ?",
        userhash
    ).fetchall()
    details = database.execute(
        "SELECT username FROM Session INNER JOIN User ON Session.userhash = User.userhash WHERE Session.session_token = ?",
        sqlData).fetchone()
    database.close()
    if details == None:
        details = ("",)
    return render_template('contributions.html', data=(contributions, details[0]))

@app.route('/delete', methods=['POST'])
def delete():
    token = request.cookies.get("token")
    id = request.form.get("delete")
    database = sqlite3.connect('questions.db')
    sqlData = (token,)
    userhash = database.execute(
        "SELECT userhash FROM Session WHERE session_token = ?",
        sqlData).fetchone()
    sqlData = (id, userhash[0])
    database.execute("DELETE FROM Question WHERE id = ? AND userhash = ?", sqlData)
    database.commit()
    database.close()
    return redirect("/contributions")

@app.route('/upload', methods=['GET'])
def uploadPage():
    # style upload.html
    token = request.cookies.get("token")
    database = sqlite3.connect('questions.db')
    sqlData = (token,)
    details = database.execute(
        "SELECT username FROM Session INNER JOIN User ON Session.userhash = User.userhash WHERE Session.session_token = ?",
        sqlData).fetchone()
    print(details)
    if details == None:
        details = ("",)
    return render_template('upload.html', data=details)

@app.route('/uploadData', methods=['POST', 'GET'])
def uploadData():
    token = request.cookies.get("token")
    contents = str(request.files['file'].read(), 'utf-8')
    data = dataProcess(contents)
    sqlData = (token,)
    database = sqlite3.connect('questions.db')
    details = database.execute(
        "SELECT userhash FROM Session WHERE session_token = ?",
        sqlData).fetchone()
    cursor = database.cursor()
    for datum in data:
        file = open(f"static/{str(hashlib.sha256(datum.question.encode('utf-8')).hexdigest())}.tex", "w")
        file.write(datum.question)
        file.close()
        log = subprocess.run(f"cd ~/tau/static/; pdflatex -halt-on-error {str(hashlib.sha256(datum.question.encode('utf-8')).hexdigest())}.tex", shell=True)
        if exists(f"static/{str(hashlib.sha256(datum.question.encode('utf-8')).hexdigest())}.pdf"):
            sqlData = (datum.year, datum.difficulty, datum.topic, details[0], str(hashlib.sha256(datum.question.encode('utf-8')).hexdigest()), datum.title, datum.question, 'Success')
            cursor.execute(f"INSERT INTO Question ('year', 'difficulty', "
                           f"'topic', 'userhash', 'file_name', 'title', 'contents', 'status') VALUES (?, "
                           f"?, ?, ?, ?, ?, ?, ?);", sqlData)
            cursor.execute("SELECT * from Question")
            print(cursor.fetchall())
            print(datum)
        else:
            sqlData = (datum.year, datum.difficulty, datum.topic, details[0],
                       str(hashlib.sha256(datum.question.encode('utf-8')).hexdigest()), datum.title, datum.question,
                       'Error')
            cursor.execute(f"INSERT INTO Question ('year', 'difficulty', "
                           f"'topic', 'userhash', 'file_name', 'title', 'contents', 'status') VALUES (?, "
                           f"?, ?, ?, ?, ?, ?, ?);", sqlData)
            cursor.execute("SELECT * from Question")
            print(cursor.fetchall())
            print(datum)
    database.commit()
    database.close()
    # redirect instead
    return redirect("/")

@app.route('/getDetails', methods=['POST', 'GET'])
def getDetails():
    token = request.cookies.get("token")
    print(token)
    database = sqlite3.connect('questions.db')
    sqlData = (token,)
    details = database.execute("SELECT username FROM Session INNER JOIN User ON Session.userhash = User.userhash WHERE Session.session_token = ?", sqlData).fetchone()
    print(details)
    return json.dumps({
        "name": details[0]
    })

@app.route('/get_token', methods=['POST'])
def getToken():
    nonce = str(int(time.time()))
    data = json.loads(request.data)
    userAuth = data['username'] + data['password']
    userhash = str(hashlib.sha256(userAuth.encode('utf-8')).hexdigest())
    auth = userhash + nonce
    token = str(hashlib.sha256(auth.encode('utf-8')).hexdigest())
    database = sqlite3.connect('questions.db')
    sqlData = (token, userhash, nonce)
    database.execute(f"PRAGMA foreign_keys = ON;")
    database.execute(f"INSERT INTO Session (session_token, userhash, nonce) VALUES (?, ?, ?);", sqlData)
    database.commit()
    database.close()
    return json.dumps({
        "token": str(hashlib.sha256(auth.encode('utf-8')).hexdigest())
    })

@app.route('/signUpData', methods=['POST', 'GET'])
def signUpData():
    nonce = str(int(time.time()))
    data = json.loads(request.data)
    if data['password'] != data['confirm_password']:
        raise Exception("Password does not match")
    else:
        userAuth = data['username'] + data['password']
        userhash = str(hashlib.sha256(userAuth.encode('utf-8')).hexdigest())
        sqlData = (userhash, data['username'])
        auth = userhash + nonce
        token = str(hashlib.sha256(auth.encode('utf-8')).hexdigest())
        database = sqlite3.connect('questions.db')
        database.execute(f"PRAGMA foreign_keys = ON;")
        database.execute(f"INSERT INTO User (userhash, username) VALUES (?, ?);", sqlData)
        sqlData = (token, userhash, nonce)
        database.execute(f"INSERT INTO Session (session_token, userhash, nonce) VALUES (?, ?, ?);", sqlData)
        database.commit()
        database.close()
        return json.dumps({
            "token": str(hashlib.sha256(auth.encode('utf-8')).hexdigest())
        })


@app.route('/signUp', methods=['POST', 'GET'])
def signUp():
    return render_template("sign_up.html")

@app.route('/signIn', methods=['POST', 'GET'])
def signIn():
    return render_template("sign_in.html")

app.run(host="0.0.0.0", port=5003, debug=True)