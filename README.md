# mastodon-data-viewer.py

A viewer for mastodon data written in python. It creates a local server that you can use to browse the data. Designed for large (>40,000) toot archives. Supports full text search and the following post content:

* Content warnings
* Image attachments
* Video attachments
* Audio attachments
* Alt text
* Polls (oneOf or anyOf)

## Install

```bash
pip install -r requirements.txt
```

Then place mastodon-data-viewer.py in your extracted mastodon data directory (the folder with actor.json/outbox.json) and run it. Open a web browser and go to http://localhost:8000

## Screenshots

![Screenshot](screenshot.png?raw=true)

![Screenshot (Dark Mode)](screenshot_dark.png?raw=true)