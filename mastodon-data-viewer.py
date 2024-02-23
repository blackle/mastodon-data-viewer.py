#!/usr/bin/env python3
import bigjson
from tqdm import tqdm
import dateutil.parser
import datetime
import re
from collections import defaultdict
import pickle
import http.server
import socketserver
from urllib.parse import urlparse
from urllib.parse import parse_qs
from urllib.parse import urlencode
import threading
import argparse
import os
from os import path
import hashlib

DEFAULT_HOST 			= "localhost"
DEFAULT_PORT 			= 8000
DEFAULT_ARCHIVE_PATH	= "./"

LINK_ICON = """<svg xmlns="http://www.w3.org/2000/svg" width="16.25" height="16.495" viewBox="0 0 4.3 4.364"><path d="M4.298.028L2.74.492l.43.368-2.039 2.1.395.373 2.002-2.105.393.382zM1.273.18A1.277 1.277 0 000 1.454V3.09c.002.702.57 1.271 1.273 1.273h1.674A1.277 1.277 0 004.22 3.091V1.944h-.544V3.09a.72.72 0 01-.73.729H1.274a.72.72 0 01-.728-.729V1.454a.72.72 0 01.728-.728h1.281V.18z" color="#000"/></svg>"""

DM_ICON = """<svg xmlns="http://www.w3.org/2000/svg" width="16.25" height="16.495" viewBox="0 0 4.3 4.364"><path d="M1.02.31a.921.921 0 00-.876.666l1.999 1.155L4.172.958A.922.922 0 003.3.31H1.02zm3.198 1.202L2.143 2.711.103 1.533v1.602c0 .502.415.916.918.916H3.3a.922.922 0 00.917-.916V1.512z" color="#000"/></svg>"""

REPLY_ICON = """<svg xmlns="http://www.w3.org/2000/svg" width="16.25" height="16.495" viewBox="0 0 4.3 4.364"><path d="M2.089 2.789v-.725c2.434 0-.28 1.516-1.519 1.97 2.26 0 6.146-3.08 1.519-3.08V.26L.136 1.47z" color="#000"/></svg>"""

TEMPLATE_START = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>mastodon-data-viewer.py</title>
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
	width: 100%;
}

.dates {
  width: 450px;
	max-width: 100%;
  position: fixed;
  top: 10px;
  right: 10px;
  box-sizing: border-box;
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
	overflow:hidden;
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
  max-width: 650px;
  width: 100%;
  margin: 20px auto 20px auto;
  box-sizing: border-box;
  
  display: flex;
  flex-wrap: nowrap;
  align-items: flex-start;
}

@media (max-width: 1600px) {
	.dates {
		position: initial;
	  margin: 20px auto 20px auto;
	}
}

@media (max-width: 800px) {
	.toot {
  	max-width: 800px;
	}
}

.content {
  flex-grow: 1;
  margin-left: 10px;
  overflow-wrap: anywhere;
}

span.postdate {
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
	width: 100%;
}

audio.image {
	height: 50px;
	width: 100%;
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

.pollbar {
    position: relative;
    height: 20px;
    background: #d1f1eb;
    border-radius: 5px;
    overflow: hidden;
}

.pollitem {
    margin-bottom: 15px;
}

.pollmeta {
    text-align: right;
    font-size: 12px;
}

.pollmeta, span.at, span.postdate {
	color: #555;
}

body.dark {
	color: #EEE;
	background: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC4AAAAuAgMAAAAq18OkAAAACVBMVEUkBgxQJB8dOj6dMmyXAAAAe0lEQVR4AWNkY/nGwMrA8JuB6/93RrGGOgZGB4b9DEz1uxlFJyQwMAQwbGBgWDCbcZrIDQYWAYY3DBwK1xiXIevRQujZziiF0DMNRQ+qPUwIPfsZBRB6FjCKIPTcoK4eVP+EIvRcZwzDFQbU1TPwYYASP+TEKVoY4LIHAMTQoQ+1yn7bAAAAAElFTkSuQmCC');
  background-attachment: fixed;
}

body.dark .box {
	background: #1f1d1d
}

body.dark a {
	color: lightblue;
}

body.dark .icon {
	filter: invert();
}

body.dark .fill {
  background: #af4f44;
}

body.dark .monthbar, body.dark .pollbar {
	background: #463d3c;
}

body.dark .monthbar.selected {
	border: 2px solid #BBB;
}

body.dark .pollmeta, body.dark span.at, body.dark span.postdate {
	color: #AAA;
}

.cw {
	margin: 10px 0px;
}
.cw p {
	margin-top: 0px;
}

.searchbar {
    width: 100%;
    margin: 0;
    box-sizing: border-box;
    border-radius: 10px;
    padding: 5px 10px;
    font-size: 20px;
}

form {
    width: 100%;
    box-sizing: border-box;
}
</style>
</head>"""

TEMPLATE_END = """</body>
</html>
"""

def search_bar_html(darkmode, searchtext):
	darkmodestr = "yes" if darkmode else "no"
	return """<div class="search toot box">
	<form action="/" method="GET">
		<input type="input" name="search" class="searchbar" placeholder="search" value="%(searchtext)s">
		<input type="hidden" name="dark" value="%(darkmodestr)s">
	</form>
</div>""" % vars()

def months_to_html(monthly, selected, darkmode, query_components):
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
			monthname = parseddate.strftime("%B")
			selectedclass = "selected" if selected == date else ""
			query_copy = query_components.copy()
			query_copy["date"] = [date]
			if "search" in query_copy:
				del query_copy["search"]
			url = "/?" + urlencode(query_copy, doseq=True)
			months += """<div class="month">
<a title="%(monthname)s" href="%(url)s" class="monthbar %(selectedclass)s">
<div class="fill" style="top:%(percent)d%%;"></div>
</a>
%(count)d
</div>""" % vars()

		years += """<div class="year">
<span class="title">%(year)d</span>
<div class="months">
%(months)s
</div>
</div>""" % vars()

	query_copy = query_components.copy()
	query_copy["dark"] = ["no"] if darkmode else ["yes"]
	themename = "light mode" if darkmode else "dark mode"
	themeurl = "/?" + urlencode(query_copy, doseq=True)

	years += """<a href="%(themeurl)s">%(themename)s</a>""" % vars()

	return """<div class="dates box">%s</div>""" % years

def get_poll_type(toot):
	if "anyOf" in toot:
		return "anyOf", toot["anyOf"]
	if "oneOf" in toot:
		return "oneOf", toot["oneOf"]
	return None, None

def poll_to_html(toot):
	polltype, pollobj = get_poll_type(toot)
	poll = ""
	if polltype is None:
		return poll
	polltype = {"oneOf": "single choice", "anyOf": "multiple choice"}[polltype]

	voteCount = 0
	for pollitem in pollobj:
		voteCount += pollitem["replies"]["totalItems"]

	for pollitem in pollobj:
		polltext = pollitem["name"]
		count = pollitem["replies"]["totalItems"]
		percent = count / voteCount * 100
		barsize = 100 - percent
		poll += """<div class="pollitem"><div class="pollbar"><div class="fill" style="right:%(barsize)d%%"></div></div><span class="polltext">%(polltext)s <span class="pollmeta">(%(count)d votes, %(percent)d%%)</span></span></div>""" % vars()

	end = dateutil.parser.isoparse(toot["endTime"])
	endtime = end.astimezone().strftime("%a, %d %b %Y %I:%M:%S %p")
	poll += """<div class="pollmeta">%(polltype)s poll. %(voteCount)d votes, ended %(endtime)s</div>""" % vars()
	return """<div class="poll box">%s</div>""" % poll

def attachments_to_html(toot):
	images = ""
	for attachment in toot["attachment"]:
		alt = attachment["name"]
		if alt is None:
			alt = ""
		alt = alt.replace("\"", "&quot;")
		mediaType = attachment["mediaType"]
		href = attachment["url"]
		if mediaType.startswith("video"):
			images += """<video controls class="image" title="%(alt)s"><source src="%(href)s" type="%(mediaType)s"></video>""" % vars()
		elif mediaType.startswith("audio"):
			images += """<audio controls class="image" title="%(alt)s"><source src="%(href)s" type="%(mediaType)s"></audio>""" % vars()
		else:
			images += """<a alt="%(alt)s" title="%(alt)s" class="image" href="%(href)s" target="_blank" style="background: url('%(href)s')" ></a>""" % vars()
	if images != "":
			images = """<div class="images">%s</div>""" % images
	return images

def toots_to_html(toots, actor, file):
	toots.sort(reverse=True, key=lambda toot: toot["published"])
	avatar = actor["icon"]["url"]
	name = actor["name"]
	username = actor["preferredUsername"]
	for toot in toots:
		datastr = str(toot)
		poll = poll_to_html(toot)
		images = attachments_to_html(toot)

		date = dateutil.parser.isoparse(toot["published"])
		postdate = date.astimezone().strftime("%a, %d %b %Y %I:%M:%S %p")
		attachments = images + poll
		content = toot["content"] + attachments
		summary = toot["summary"]
		if toot["sensitive"]:
			if summary is None:
				summary = toot["content"]
				content = attachments
			content = """<div class="cw">%(summary)s <button onclick="this.parentNode.nextElementSibling.classList.toggle('hidden');" class="showmore">show more</button></div>
<div class="collapsible hidden">
%(content)s
</div>""" % vars()

		icons = """<a class="icon" href="%(url)s" target="_blank">%(icon)s</a>""" % {"url": toot["url"], "icon": LINK_ICON}
		if "directMessage" in toot and toot["directMessage"]:
			icons += """<a class="icon" title="direct message">%s</a>""" % DM_ICON
		if "inReplyTo" in toot and toot["inReplyTo"] is not None:
			icons += """<a class="icon" href="%(url)s" title="reply">%(icon)s</a>""" % {"url": toot["inReplyTo"], "icon": REPLY_ICON}
		line = """<div class="toot box"><!-- %(datastr)s -->
<div class="avatar">
<img class="avatar" src="%(avatar)s" />
</div>
<div class="content">
%(icons)s
<b>%(name)s</b> <span class="at">@%(username)s</span><br/>
<span class="postdate">%(postdate)s</span>
%(content)s
</div>
</div>""" % vars()
		file.write(line.encode('utf8'))

def load_toots(outbox_path):
	toots = {}
	with open(outbox_path, 'rb') as f:
		j = bigjson.load(f)
		t = tqdm(total=0, unit="toots")
		for item in j["orderedItems"]:
			if (item["type"] != "Create"):
				continue
			obj = item["object"].to_python()
			toots[obj["id"]] = obj
			t.update()
		t.close()

	return toots

def bin_monthly(toots):
	monthly = defaultdict(list)
	# bin the toots into months
	for toot in toots:
		date = dateutil.parser.isoparse(toot["published"]).astimezone()
		date = datetime.date(year=date.year, month=date.month, day=1)
		monthly[str(date)].append(toot)
	return monthly

def search_text_in_toot(toot, searchtext):
	searchregex = re.compile(r"\b" + searchtext + r"\b", flags=re.I)
	def check_key(key):
		return toot[key] is not None and searchregex.search(toot[key])
	if check_key("content") or check_key("summary"):
		return True
	polltype, pollobj = get_poll_type(toot)
	if polltype is not None:
		for pollitem in pollobj:
			if searchregex.search(pollitem["name"]):
				return True
	for attachment in toot["attachment"]:
		if attachment["name"] is not None and searchregex.search(attachment["name"]):
			return True

def main():
	parser = argparse.ArgumentParser(description = "A viewer for mastodon export data")

	parser.add_argument("--hostname", "-n", default=DEFAULT_HOST, help="Hostname for the web server")
	parser.add_argument("--port", "-p", default=DEFAULT_PORT, type=int, help="Port number for the web server")
	parser.add_argument("--archive", "-a", default=DEFAULT_ARCHIVE_PATH, help="Path to Mastodon's outbox.json and actor.json")
	parser.add_argument("--cache", "-c", default="./", help="Path where the cache files will be stored")
	parser.add_argument("--force-update", "-r", default=False, help="Forces rebuild of the toots.pk cache file", action='store_true')
	parser.add_argument("--dont-update", "-u", default=False, help="Does not update the toots cache with data files", action='store_true')
	parser.add_argument("--use-outbox", "-o", default=False, help="Uses outbox.json file regardless of the contents of actor.json", action='store_true')
	args = parser.parse_args()

	if not path.isdir(args.archive):
		os.mkdir(args.archive)
	if not path.isdir(args.cache):
		os.mkdir(args.cache)

	save_cache = False

	toots_path = path.join(args.cache, "toots.pk")
	if args.use_outbox:
		outbox_path = path.join(args.archive, "outbox.json")
	actor_path = path.join(args.archive, "actor.json")
	hash_path = path.join(args.cache, "hash.sha256")
	delta = 0

	for p in [actor_path, outbox_path]:
		if path.isfile(p):
			continue
		print("Failed to find \"{}\"".format(p))
		exit(1)

	with open(path.join(args.archive, "actor.json"), 'rb') as f:
		j = bigjson.load(f)
		actor = j.to_python()

	if not args.use_outbox:
		outbox_path = path.join(args.archive, actor["outbox"])

	with open(outbox_path, 'rb') as f:
		new_hash = hashlib.sha256(f.read()).hexdigest()

	if path.isfile(toots_path) and path.isfile(hash_path) and not args.force_update:
		with open(toots_path, "rb") as f:
			toots = pickle.load(f)
		with open(hash_path, "r") as f:
			current_hash = f.read()

		if new_hash != current_hash and not args.dont_update:
			new_toots = load_toots(outbox_path)
			save_cache = (new_toots != toots)
			if save_cache:
				print("Updating toots cache")
				delta = len(new_toots) - len(toots)
				toots = new_toots
	else:
		print("Building toots cache", end="")
		toots = load_toots(outbox_path)
		delta = len(toots)
		save_cache = True
	
	if save_cache:
		print("Saving toots cache on \"{}\"...".format(toots_path), end="", flush=True)
		with open(toots_path, "wb") as f:
			pickle.dump(toots, f)
		print("OK!")
		print("Saving hash file on \"{}\"...".format(hash_path), end="", flush=True)
		with open(hash_path, "w") as f:
			f.write(new_hash)
		print("OK!")
		print("{} toots {}".format(abs(delta), "added" if delta >= 0 else "removed"))
		
	monthly = bin_monthly(toots.values())
	monthkeys = sorted(monthly.keys())

	class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
		def do_GET(self):
			parsedpath = urlparse(self.path)
			if parsedpath.path == '/':
				self.send_response(200)
				self.send_header("Content-type", "text/html")
				self.end_headers()
				query_components = parse_qs(parsedpath.query)
				darkmode = "dark" in query_components and query_components["dark"][0] == "yes"
				search = "search" in query_components
				date = None
				searchtext = ""
				if search:
					searchtext = query_components["search"][0]
				elif "date" in query_components:
					date = query_components["date"][0]
				else:
					date = monthkeys[-1]

				bodytag = "<body>"
				if darkmode:
					bodytag = "<body class=\"dark\">"

				monthbins = monthly
				results = []
				if search:
					for key in toots:
						toot = toots[key]
						if search_text_in_toot(toot, searchtext):
							results.append(toot)
					if len(results) > 1:
						monthbins = bin_monthly(results)
				elif date in monthly:
					results = monthly[date]
				self.wfile.write(TEMPLATE_START.encode('utf8'))
				self.wfile.write(bodytag.encode('utf8'))
				self.wfile.write(search_bar_html(darkmode, searchtext).encode('utf8'))
				if search:
					titleBox = """<div class="toot box"><h1>Search results for: <i>%s</i></h1></div>\n""" % searchtext
					self.wfile.write(titleBox.encode('utf8'))
				else:
					dateparsed = datetime.datetime.strptime(date, "%Y-%m-%d")
					titleBox = """<div class="toot box"><h1>%s</h1></div>\n""" % dateparsed.strftime("%B %Y")
					self.wfile.write(titleBox.encode('utf8'))
				self.wfile.write(months_to_html(monthbins, date, darkmode, query_components).encode('utf8'))
				toots_to_html(results, actor, self.wfile)

				self.wfile.write(TEMPLATE_END.encode('utf8'))
				return
			return http.server.SimpleHTTPRequestHandler.do_GET(self)

	class ThreadingSimpleServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
		pass

	print("""
	Mastodon-data-viewer is now running.
	Open http://{}:{}/ in a web browser to view your archive.
	Press ctrl+c in this window to stop the application.
	""".format(args.hostname, args.port))
	socketserver.TCPServer.allow_reuse_address = True
	server = ThreadingSimpleServer((args.hostname, args.port), MyHttpRequestHandler)
	server.serve_forever()

if __name__ == "__main__":
	main()
