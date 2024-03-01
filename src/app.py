from playwright.sync_api import sync_playwright
import requests
import re
import urllib
import json
import os
import yaml
from flask import Flask
from flask import redirect

app = Flask(__name__)


datadir = os.environ["DATADIR"]
with open(os.path.join(datadir, "config.yml"), 'r') as file:
    config = yaml.safe_load(file)

class TokenError(Exception):
    pass

class Tokensniffer:
    def __init__(self):
        self.token = None
    def refresh(self):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.on("request", self.onRequest)
            page.goto(urllib.parse.urljoin(config["tv_url"] ,"/tv/fox-news-channel-live-stream/"))
            browser.close()
    def onRequest(self, request):
        if "/token/" in request.url:
            self.token = request.post_data_json["password"]
            print("new token: " + self.token)
        else:
            return False

def listChannels():
    res = {}
    channelListRegex = "<a class=\"list-group-item\" href=\"(.*)\">(.*)</a>"
    streamIdRegex = "<div id=\"stream_name\" stream-name=\"(.*)\"></div>"
    indexHTML = requests.get(config["tv_url"]).text
    for line in indexHTML.splitlines():
        search = re.search(channelListRegex, line)
        if search == None:
            continue
        name = search.group(2)
        streamHTML = requests.get(urllib.parse.urljoin(config["tv_url"], search.group(1))).text
        streamId = None
        for line in streamHTML.splitlines():
            search = re.search(streamIdRegex, line)
            if search == None:
                continue
            streamId = search.group(1)            
            break
        if streamId != None:
            res[name.replace("&amp;", "&")] = streamId
    return res

def getStream(chid, token):
    if chid not in channels.values():
        raise KeyError()
    # 1st request to get cookies and x-csrf token.
    r1 = requests.get(config["tv_url"])
    # the csrf token
    csrftoken = re.findall('csrf\-token"\s*content\s*=\s*"([^"]+)"',r1.text,re.DOTALL)[0]
    # final request to api with the cookie and token.
    r2 = requests.post(urllib.parse.urljoin(config["tv_url"], "/token/" + chid), cookies=r1.cookies, json={"password":token}, headers={"Content-Type": "application/json","X-Csrf-Token":csrftoken})
    if r2.status_code != 200:
        raise TokenError("Invalid token")
    try:
        json_object = json.loads(r2.text)
        print("res was json")
        return r2.json()[-1]
    except ValueError as e:
        print ("res was string") 
        print(r2.text)
        r3 = requests.get(r2.text)
        for line in r3.text.splitlines():
            if line.startswith("#"):
                continue
            if "_high.m3u8" in line:
                return urllib.parse.urljoin(r2.text, line)

channels = listChannels()
token = Tokensniffer()
token.refresh()



@app.route("/channels.m3u")
def fullm3u():
    m3u = "#EXTM3U"
    for i, value in channels.items():
        m3u += "\n#EXTINF:-1 tvg-chno=\"%s\",%s\n%s/channel/%s" % (str(list(channels.keys()).index(i) + 1), i, config["visible_url"], value)
    return(m3u)
@app.route("/channel/<channel>")
def appchannel(channel):
    try:
        res = getStream(channel, token.token)
        return redirect(res)
    except TokenError:
        print("token invalid, requesting new one")
        token.refresh()
        return redirect(getStream(channel, token.token))
    except KeyError:
        return ("Channel does not exist, or is blocked.", 404)
