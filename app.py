import sys
from flask import Flask, request
from gevent import monkey
def stub(*args, **kwargs):
    pass
monkey.patch_all = stub
import grequests
import requests
import re
from eig_state.state_manager import StateManager
app = Flask("eig-brain")


@app.route("/", methods=["POST"])
def handleRequest():
    print("received request", file=sys.stderr)
    text = request.form['text']
    userid = request.form['userid']
    convid = request.form['convid']
    sessionid = request.form['sessionid']

    sm = StateManager(userid, convid, sessionid).next_round(text)
    if sm.conv_history.state_list[-1].has_swear:
        response = "I am not comfortable talking about that. Can we talk about something else?"
    elif sm.conv_history.state_list[-1].asks_advice:
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
          grequests.post('https://3ss5b0g2q4.execute-api.us-east-1.amazonaws.com/production',
                         data={'text':text}, timeout=2),
          grequests.get('http://107.22.159.20', params={'q': text}, timeout=3 )

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
            print("google response", goog_res)
            print("aiml response", aiml_res)
            return "Could you repeat that, please?"
    except requests.exceptions.RequestException:
        return "Could you repeat that, please?"
if __name__ == '__main__':
    app.run()
    #app.run(debug=True, host="0.0.0.0", port=8081)
