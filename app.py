from flask import Flask, request
from pymongo import MongoClient
import re
import grequests
import requests
from eig_state.state_manager import StateManager
import sys

app = Flask("eig-brain")


@app.route("/", methods=["POST"])
def handleRequest():
    text = request.form['text']
    userid = request.form['userid']
    convid = request.form['convid']

    sm = StateManager(userid, convid).next_round(text)
    if sm.conv_history.state.has_swear:
        response = "I am not comfortable talking about that. Can we talk about something else?"
    elif sm.conv_history.state.asks_advice:
        response = "I don't think that I have the requisite knowledge to answer such a question."
    else:
        response = discriminate(text)
    sm.set_response(response)
    return response

def exception_handler(request, exception):
    print("Request Exception", exception, file=sys.stderr)

def discriminate(text):
    try:
        print(text, file=sys.stderr)
        reqs = [
          grequests.post('https://3ss5b0g2q4.execute-api.us-east-1.amazonaws.com/production', data={'text':text}, timeout=3),
          grequests.get('http://107.22.159.20', params={'q': text}, timeout=3)
        ]
        aiml_res, goog_res = grequests.map(reqs, exception_handler=exception_handler)
        if goog_res and goog_res.text != "" and goog_res.text != 'Hello' and goog_res.text != 'Query not found':
            print("Google", file=sys.stderr)
            return goog_res.text
        elif aiml_res:
            print("aiml", file=sys.stderr)
            if goog_res:
                print(goog_res.text, file=sys.stderr)
            return aiml_res.text
        else:
            print("goog_res", goog_res, file=sys.stderr)
            print("aiml_res", aiml_res, file=sys.stderr)
            return "Sorry, something went wrong."
    except requests.exceptions.RequestException as e:
        print(e, file=sys.stderr)
        return "Sorry, something went wrong."

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8081)
