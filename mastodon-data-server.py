#!/usr/bin/env python3
import bigjson
from tqdm import tqdm
import dateutil.parser
import datetime
from collections import defaultdict
import pickle
import http.server
import socketserver
from urllib.parse import urlparse
from urllib.parse import parse_qs

# todo: polls
# todo: better link icon

LINK_ICON = """<svg xmlns="http://www.w3.org/2000/svg" width="16.25" height="16.495" viewBox="0 0 4.3 4.364"><path d="M4.3 0L3.016.383l.29.273L1.132 2.96l.395.373 2.173-2.301.29.273zM1.273.18A1.277 1.277 0 000 1.454V3.09a1.276 1.276 0 001.273 1.273h1.674A1.277 1.277 0 004.22 3.091V1.944h-.544V3.09a.72.72 0 01-.73.729H1.274a.72.72 0 01-.728-.729V1.454a.72.72 0 01.728-.728h1.281V.18H1.273z" color="#555"/></svg>"""

DM_ICON = """<svg xmlns="http://www.w3.org/2000/svg" width="16.25" height="16.495" viewBox="0 0 4.3 4.364"><path d="M1.02.31a.921.921 0 00-.876.666l1.999 1.155L4.172.958A.922.922 0 003.3.31H1.02zm3.198 1.202L2.143 2.711.103 1.533v1.602c0 .502.415.916.918.916H3.3a.922.922 0 00.917-.916V1.512z" color="#000"/></svg>"""

REPLY_ICON = """<svg xmlns="http://www.w3.org/2000/svg" width="16.25" height="16.495" viewBox="0 0 4.3 4.364"><path d="M2.089 2.789v-.725c2.434 0-.28 1.516-1.519 1.97 2.26 0 6.146-3.08 1.519-3.08V.26L.136 1.47z"/></svg>"""

TEMPLATE = """
<html>
<head>
<meta charset="utf-8">
<style>
body {
  background: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC4AAAAuAgMAAAAq18OkAAAACVBMVEXE9OuFxMzPo53j2hi5AAAAe0lEQVR4AWNkY/nGwMrA8JuB6/93RrGGOgZGB4b9DEz1uxlFJyQwMAQwbGBgWDCbcZrIDQYWAYY3DBwK1xiXIevRQujZziiF0DMNRQ+qPUwIPfsZBRB6FjCKIPTcoK4eVP+EIvRcZwzDFQbU1TPwYYASP+TEKVoY4LIHAMTQoQ+1yn7bAAAAAElFTkSuQmCC');
  background-attachment: fixed;
  font-family: sans;
}

.box {
  border: 1px solid black;
  background: white;
  border-radius: 5px;
  box-shadow: 0px 2px 5px grey;
  padding: 10px;
}

h1 {
	text-align: center;
	width: 100%%;
}

.dates {
  width: 400px;
  position: fixed;
  top: 10px;
  right: 10px;
}

.year {
  margin: 10px 0px;
}

.year .title {
  margin-bottom: 5px;
  display: block;
  font-weight: bold;
}

.months {
  display: flex;
  flex-wrap: nowrap;
  align-items: flex-start;
}

.month {
  margin-right: 2px;
  text-align: center;
  font-size: 12px;
  flex: 1 1 0px;
}

.month:last-child {
  margin-right: 0px;
}

.monthbar {
  height: 60px;
  border-radius: 4px;
  margin-bottom: 5px;
  background: #d1f1eb;
  display: block;
  overflow: hidden;
  position: relative;
  box-sizing: border-box;
}

.monthbar.selected {
	border: 2px solid black;
}

.fill {
  background: #3d9da9;
  position: absolute;
  border-radius: 2px;
  bottom: 0;
  left: 0;
  right: 0;
  top: 0;
}

.toot {
  width: 600px;
  margin: 20px auto 20px auto;
  
  display: flex;
  flex-wrap: nowrap;
  align-items: flex-start;
}

.content {
  flex-grow: 1;
  margin-left: 10px;
  overflow-wrap: anywhere;
}

span.at {
  color: #555;
}

span.postdate {
  color: #555;
	font-size: 11px;
}

img.avatar {
  width: 50px;
  height: 50px;
  display: block;
}

.images {
  display: flex;
  flex-wrap: nowrap;
  align-items: flex-start;
  margin-top: 15px;
}

.image {
  height: 300px;
  flex-grow: 1;
  border: 1px solid black;
  margin-right: 10px;
  background-position: center !important;
  background-size: cover !important;
}

video.image {
	height: auto;
	max-height: 600px;
	width: 100%%;
}

audio.image {
	height: 50px;
	width: 100%%;
	border: none;
}

.image:last-child {
  margin-right: 0px;
}

.hidden {
	display: none;
}

.icon {
	float: right;
	margin-left: 5px;
}
</style>
</head>
<body>
%(body)s
<script>
var buttons = document.querySelectorAll("button.showmore")
Array.prototype.forEach.call(buttons, function(button) {
    button.onclick = function() {
        button.parentNode.nextElementSibling.classList.toggle('hidden');
    }
});
</script>
</body>
</html>
"""

def months_to_html(monthly, selected):
	monthkeys = sorted(monthly.keys())
	maximum = max([len(monthly[date]) for date in monthkeys])
	start = datetime.datetime.strptime(monthkeys[0], "%Y-%m-%d")
	end = datetime.datetime.strptime(monthkeys[-1], "%Y-%m-%d")
	years = ""
	for year in reversed(range(start.year, end.year+1)):
		months = ""
		for month in range(12):
			date = '%04d-%02d-01' % (year, month+1)
			parseddate = datetime.datetime.strptime(date, "%Y-%m-%d")
			count = len(monthly[date])
			percent = 100 - count/maximum * 100
			selectedclass = "selected" if selected == date else ""
			months += """<div class="month">
<a title="%(monthname)s" href="/?date=%(date)s" class="monthbar %(selected)s">
<div class="fill" style="top:%(percent)d%%;"></div>
</a>
%(count)d
</div>""" % {"monthname": parseddate.strftime("%B"), "date": date, "count": count, "percent": percent, "selected": selectedclass}

		years += """<div class="year">
<span class="title">%(year)d</span>
<div class="months">
%(months)s
</div>
</div>""" % {"year": year, "months": months}

	return """<div class="dates box">%s</div>""" % years

def toots_to_html(toots):
	toots.sort(reverse=True, key=lambda toot: toot["published"])
	lines = ""
	for toot in toots:
		images = ""
		for attachment in toot["attachment"]:
			if attachment["mediaType"].startswith("video"):
				images += """<video controls class="image"><source src="%(href)s" type="%(type)s"></video>""" % {"data": str(attachment), "href": attachment["url"], "type": attachment["mediaType"]}
			elif attachment["mediaType"].startswith("audio"):
				images += """<audio controls class="image"><source src="%(href)s" type="%(type)s"></audio>""" % {"data": str(attachment), "href": attachment["url"], "type": attachment["mediaType"]}
			else:
				images += """<a alt="bep" title="bep" class="image" href="%(href)s" target="_blank" style="background: url('%(href)s')" ></a>""" % {"href": attachment["url"]}
		date = dateutil.parser.isoparse(toot["published"])
		postdate = date.strftime("%a, %d %b %Y %I:%M:%S %p")
		content =  """%(content)s
<div class="images">
%(images)s
</div>""" % {"content": toot["content"], "images": images}
		if toot["sensitive"]:
			content =  """<p>%(summary)s <button class="showmore">show more</button></p>
<div class="collapsible hidden">
%(content)s
</div>""" % {"summary": toot["summary"], "content": content}

		icons = """<a class="icon" href="%(url)s" target="_blank">%(icon)s</a>""" % {"url": toot["url"], "icon": LINK_ICON}
		if "directMessage" in toot and toot["directMessage"]:
			icons += """<a class="icon" title="direct message">%s</a>""" % DM_ICON
		if "inReplyTo" in toot and toot["inReplyTo"] is not None:
			icons += """<a class="icon" title="reply">%s</a>""" % REPLY_ICON
		line = """<div class="toot box"><!-- %(data)s -->
<div class="avatar">
<img class="avatar" src="./avatar.png" />
</div>
<div class="content">
%(icons)s
<b>talkative fishy</b> <span class="at">@blackle</span><br/>
<span class="postdate">%(postdate)s</span>
%(content)s
</div>
</div>""" % {"data": str(toot), "content": content, "postdate": postdate, "icons": icons}
		lines += line
		# file.write(line.encode('utf8'))
	return lines

def load_toots():
	toots = {}
	with open('outbox.json', 'rb') as f:
		j = bigjson.load(f)
		totalItems = j["totalItems"]
		allItems = j["orderedItems"]
		print("Loading toots for the first time")
		for i in tqdm(range(totalItems)):
			item = allItems[i]
			if (item["type"] != "Create"):
				continue
			obj = item["object"].to_python()
			toots[obj["id"]] = obj
	pickle.dump(toots, open("toots.pk", "wb"))
	return toots

def main():

	try:
		toots = pickle.load(open("toots.pk", "rb"))
	except:
		toots = load_toots()
	monthly = defaultdict(list)
	# bin the toots into months
	for key, toot in toots.items():
		date = dateutil.parser.isoparse(toot["published"])
		date = datetime.date(year=date.year, month=date.month, day=1)
		monthly[str(date)].append(toot)

	class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
		def do_GET(self):
			parsedpath = urlparse(self.path)
			if parsedpath.path == '/':
				self.send_response(200)
				self.send_header("Content-type", "text/html")
				self.end_headers()
				monthkeys = sorted(monthly.keys())
				date = monthkeys[0]
				query_components = parse_qs(parsedpath.query)
				if "date" in query_components:
					date = query_components["date"][0]
				dateparsed = datetime.datetime.strptime(date, "%Y-%m-%d")

				body = months_to_html(monthly, date)
				body += """<div class="toot box"><h1>%s</h1></div>\n""" % dateparsed.strftime("%B %Y")
				body += toots_to_html(monthly[date])
				body = TEMPLATE % {"body": body}

				self.wfile.write(body.encode('utf8'))
				return
			return http.server.SimpleHTTPRequestHandler.do_GET(self)

	PORT = 8001
	print("port:",PORT)
	server = socketserver.TCPServer(("", PORT), MyHttpRequestHandler)
	server.serve_forever()

if __name__ == "__main__":
	main()
