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
  background: #BCF;
  display: block;
  overflow: hidden;
  position: relative;
}

.fill {
  background: #359;
  position: absolute;
  border-radius: 4px;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1;
}
span.monthcount {
  z-index: 2;
  color: white;
  font-weight: bold;
  position: absolute;
  display: block;
  text-align: center;
  padding-top: 10px;
  bottom: 0;
  left: 0;
  right: 0;
  top: 0;
  text-shadow: 0px 0px 4px black;
  font-size: 14px;
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
</style>
</head>
<body>
%(body)s
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
			months += """<div class="month">
<a title="%(monthname)s" href="/?date=%(date)s" class="monthbar">
<div class="fill" style="top:%(percent)d%%;"></div>
</a>
%(count)d
</div>""" % {"monthname": parseddate.strftime("%B"), "date": date, "count": count, "percent": percent}

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

		line = """<div class="toot box"><!-- %(data)s -->
<div class="avatar">
<img class="avatar" src="./avatar.png" />
<a href="%(url)s" target="_blank">Link</a>
</div>
<div class="content">
<b>talkative fishy</b> <span class="at">@blackle</span>
%(content)s
<div class="images">
%(images)s
</div>
</div>
</div>""" % {"data": str(toot), "url": toot["url"], "content": toot["content"], "images": images}
		lines += line
		# file.write(line.encode('utf8'))
	return lines

def main():

	toots = pickle.load( open( "toots.pk", "rb" ) )
	monthly = pickle.load( open( "monthly.pk", "rb" ) )

	class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
		def do_GET(self):
			parsedpath = urlparse(self.path)
			if parsedpath.path == '/':
				self.send_response(200)
				self.send_header("Content-type", "text/html")
				self.end_headers()
				monthkeys = sorted(monthly.keys())
				date = monthkeys[0]
				query_components = parse_qs(urlparse(self.path).query)
				if "date" in query_components:
					date = query_components["date"][0]

				body = months_to_html(monthly, date)
				body += toots_to_html(monthly[date])
				body = TEMPLATE % {"body": body}

				self.wfile.write(body.encode('utf8'))
				return
			return http.server.SimpleHTTPRequestHandler.do_GET(self)

	PORT = 8001
	print("port:",PORT)
	# handler = MyHttpRequestHandler(toots, monthly)
	my_server = socketserver.TCPServer(("", PORT), MyHttpRequestHandler)
	# Star the server
	my_server.serve_forever()

	# toots = {}
	# monthly = defaultdict(list)
	# # whitelist_keys = ["id", "type", "summary", "inReplyTo", "published", "url", "sensitive", "content", "directMessage", "endTime", "closed", "oneOf"]
	# with open('outbox.json', 'rb') as f:
	# 	j = bigjson.load(f)
	# 	totalItems = j["totalItems"]
	# 	allItems = j["orderedItems"]
	# 	print("Loading all items into memory")
	# 	for i in tqdm(range(totalItems)):
	# 		item = allItems[i]
	# 		if (item["type"] != "Create"):
	# 			continue
	# 		obj = item["object"].to_python()
	# 		toots[obj["id"]] = obj #{ key: obj[key] for key in whitelist_keys if key in obj }
	# 		date = dateutil.parser.isoparse(obj["published"])
	# 		date = datetime.date(year=date.year, month=date.month, day=1)
	# 		monthly[str(date)].append(obj)
	# months = sorted(monthly.keys(), reverse=True)
	# for month in months:
	# 	print(month, len(monthly[month]))
	# pickle.dump( monthly, open( "monthly.pk", "wb" ) )
	# pickle.dump( toots, open( "toots.pk", "wb" ) )

if __name__ == "__main__":
	main()
