from flask import render_template
from flask import make_response
from flask import request
from flask import Flask

from flask_socketio import SocketIO
from flask_socketio import emit

import subprocess
import threading
import traceback
import base64
import random
import string
import time
import os

import eventlet
import serial

ser = serial.Serial()
ser.baudrate = 19200
ser.port = "/dev/ttyUSB0"
ser.timeout = 0

def diceword():
    words = []
    for _ in range(4):
        word = ""
        with open("/usr/share/dict/american-english-small", "r") as wordlist:
            for n, tempword in enumerate(i.lower() for i in wordlist if i.rstrip("\n").isalpha()):
                if random.random() < (1.0 / (n+1)):
                    word = tempword
        words.append(word.rstrip("\n"))
    words[0] = words[0].title()
    return " ".join(words)

def generate_key():
    return "".join(random.choice(string.ascii_letters + string.digits) for i in range(32))

app = Flask(__name__)
socketio = SocketIO(app)

newest_key = ""

upload_key = generate_key()

diceword = diceword()

def read_sketch(name="./platformio/src/rossum.ino"):
    content = ""
    try:
        with open(name, "r") as rossum:
            content = rossum.read()
    except:
        try:
            content = read_sketch("./sketches/blink.ino")
        except:
            content = "//Can't read rossum.ino or blink.ino!"
    return content

def save_sketch(content):
    with open("./platformio/src/rossum.ino", "w") as rossum:
        rossum.write(content)

@app.route("/", methods=["GET", "POST"])
def auth():
    global newest_key
    global upload_key
    if request.method == "GET":
        try:
            if request.cookies["authkey"] == newest_key:
                return render_template("editor.html", editor_text=read_sketch(), upload_key=upload_key, diceword=diceword)
            else:
                resp = make_response(render_template("auth.html", placeholder="What's the password?"))
                resp.set_cookie("authkey", "", expires=0)
                return resp
        except:
            return render_template("auth.html", placeholder="What's the password?")
    else:
        if request.form["password"].lower() == base64.b64decode("ZG9tbyBhcmlnYXRvIG1yIHJvYm90bw==").decode("utf-8"):
            resp = make_response(render_template("editor.html", editor_text=read_sketch(), upload_key=upload_key, diceword=diceword))
            newest_key = generate_key()
            resp.set_cookie("authkey", newest_key)
            return resp
        else:
            return render_template("auth.html", placeholder="Nope.")

@app.route("/upload", methods=["POST"])
def handle_upload():
    global upload_key
    if request.form["auth"] != upload_key:
        return "nope"
    socketio.emit("line", {"content": "Data received.\nSaving file..."}, broadcast=True)
    eventlet.sleep()
    save_sketch(request.form["content"])
    socketio.emit("line", {"content": "Compiling and uploading..."}, broadcast=True)
    eventlet.sleep()
    proc = subprocess.Popen(["platformio", "run", "-d", "./platformio"], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
    error = False
    while True:
        line = proc.stdout.readline()
        if line and (not (line.startswith("Reading") or line.startswith("Writing"))):
            if "ERROR:" in line:
                error = True
            socketio.emit("line", {"content": line.rstrip()}, broadcast=True)
        else:
            break
        eventlet.sleep()
    if not error:
        socketio.emit("line", {"content": "Successfully uploaded source to Arduino!"}, broadcast=True)
        eventlet.sleep(1)
        socketio.emit("reafy", broadcast=True)
    else:
        socketio.emit("line", {"content": "Failed to upload to Arduino. Press Ctrl-I to continue."}, broadcast=True)
        eventlet.sleep()
        socketio.emit("uploaderror", broadcast=True)
    eventlet.sleep()
    return "done"

@socketio.on("seropen")
def seropen(auth):
    global upload_key
    global diceword
    if auth == upload_key or auth == diceword:
        if not ser.is_open:
            ser.open()

@socketio.on("serclose")
def serclose(auth):
    global upload_key
    global diceword
    if auth == upload_key or auth == diceword:
        if ser.is_open:
            ser.close()
    
@socketio.on("serwrite")
def serwrite(data, auth):
    global upload_key
    global diceword
    if auth == upload_key or auth == diceword:
        if data and len(data) > 0:
            ser.write((data + "\n").encode("utf-8"))
        c = ser.read()
        if c and len(c) > 0:
            socketio.emit("serline", {"content": "".join(read_data)}, broadcast=True)

@socketio.on_error()
def error_handler(e):
    socketio.emit("error", {"content": "".join(traceback.format_tb(e.__traceback__))})

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80)
