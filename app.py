import re
import os
import cv2
import time
import spacy
import pytesseract
import numpy as np
import phonenumbers
import en_core_web_sm

from PIL import Image
from flask import Flask
from pathlib import Path
from pprint import pprint
from flask_cors import CORS
from validate_email import validate_email
from flask import Flask, request, make_response, jsonify

#     pytesseract.pytesseract.tesseract_cmd = r"{}".format(
#         os.path.expanduser('~')+r"\AppData\Local\Tesseract-OCR\tesseract.exe")

nlp = en_core_web_sm.load()

app = Flask(__name__)
log = app.logger

CORS(app)

@app.route('/', methods=['GET'])
def func():
    print("hello world")
    return make_response(jsonify({'status': "ok"}))

@app.route("/file-upload", methods=["POST"])
def upload():
    print(request.get_data())
    item = ""
    if request.get_data():
        image = np.asarray(bytearray(request.get_data()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        item = pytesseract.image_to_string(image)
    r = getExtract(item)
    response = jsonify({'status': "ok", "result": r})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

def getExtract(item):
    item_extracted = {
        "rawstring": item,
        "emails": getEmails(item.lower()),
        "websites": getWebsite(item.lower()),
        "mobiles": getMobile(item.lower()),
        "names": getPerson(item.lower())
    }
    pprint(item_extracted)
    return item_extracted

def get_img_string_values(img):
    result = {}
    img = cv2.imread(img)
    result["cv2"] = pytesseract.image_to_string(img)
    result["PIL"] = pytesseract.image_to_string(Image.fromarray(img))
    return result

def getPerson(item):
    print(" ".join(re.split(':| |\n', item)))
    doc = nlp(" ".join(re.split(':| |\n', item)))
    names = [X.text for X in doc.ents if X.label_ == "PERSON"]
    names_capitalized = [word.capitalize() for word in names]
    return names_capitalized


def getMobile(item):
    temp = []
    p = [r"(?:\+ *)?\d[\d\- ]{7,}\d",
         r"\(\d{2,4}\) +\d{8}",
         # r"\(\d{2,4}\) +\d{4,} +\d{4,}",
         r"\d{3}-\d{8}|\d{4}-\d{7}"
        ]
    for i in [re.findall(pat, " ".join(re.split(':| |\n', item))) for pat in p]:
        temp.extend(i)
    for string in item.split("\n"):
        for match in phonenumbers.PhoneNumberMatcher(string, None):
            if match:
                temp.append(match.raw_string)

    return list(set(temp))


def getEmails(plain_str):
    pattern = [
        r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])",
        r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?",
        r'\S+@\S+',
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"]
    res = []
    for i in [re.findall(pat, plain_str) for pat in pattern]:
        res.extend(i)
    return list(set([i for i in res if validate_email(i)]))


def getWebsite(plain_str):
    pattern = r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))'
    return [i for i in re.findall(pattern, plain_str)[0] if i != ""] if (re.findall(pattern, plain_str)) else ()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
