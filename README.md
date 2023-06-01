---
title: Event Summarizer
emoji: 
sdk: gradio
sdk_version: 3.32.0
python_version: 3.10.0
app_file: app.py
pinned: false
---

# Event(brite) Summarizer

Tool for summarizing Eventbrite events for inclusion in event calendars.  Takes in a URL and a generic prompt, which are fed into a Large Language Model (in this case OpenAI) along with the event scrapes the title, subtitle, and event details.

Originally created for http://sf.funcheap.com 

Environment Requirements:
- Python 3.10
- Environment variables `OPENAI_API_KEY` and `EVENTBRITE_API_KEY`, available through the [Eventbrite API Page](https://www.eventbrite.com/platform/api).

## Eventbrite-specific notes

I assume that the event 'description' and 'summary' fields contain the same content (verified with checking 10 urls)

The API does not return the event title or subtitle, so we use Beautifulsoup to extract them.

The user-generated event description can be hard to parse from raw HTML, but is served succinctly via the API.  The Eventbrite API appears to use `utf-8-sig` encoding. To handle that encoding, we replace `\uffef` with a null string.

These inputs (title, subtitle, details) are combined and fed in along with the prompt.


# TODO:

- [X] Handle errors - will currently error gracelessly on expired events 
- [ ] Meaningfully use feedback / integrate with Weights & Biases
- [ ] Allow auto-regeneration of text if output does not meet expectation (exclusion characters, etc)
- [ ] Dropdown for model type
