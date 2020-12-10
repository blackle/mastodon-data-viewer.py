# mastodon-data-viewer.py

A viewer for mastodon data written in python. It creates a local server that you can use to browse the data. Designed for large (>40,000) toot archives. Supports the following post content:

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

Then place mastodon-data-viewer.py in your extracted mastodon data directory (the folder with actor.json/outbox.json) and run it.

## Screenshot

![Screenshot](screenshot.png?raw=true)