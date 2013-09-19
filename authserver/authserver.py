import json

from flask import Flask, request

app = Flask(__name__)
app.debug = True

@app.route('/')
def index():
    pkey_hash = None
    cookie = request.cookies.get('xoid')
    if cookie:
        xoid = json.loads(cookie)
        if xoid:
            pkey_hash = xoid.get('pkey_hash')
    return "OK! <pre>{}</pre>".format(pkey_hash)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
