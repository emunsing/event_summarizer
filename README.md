# Event(brite) Summarizer

Tool for summarizing Eventbrite events for inclusion in event calendars.  Takes in a URL and a generic prompt, which are fed into a Large Language Model (in this case OpenAI) along with the event scrapes the title, subtitle, and event details  

Environment Requirements:
- Python 3.10
- Environment variables `OPENAI_API_KEY` and `EVENTBRITE_API_KEY`, available through the [Eventbrite API Page](https://www.eventbrite.com/platform/api).

## Eventbrite-specific notes

The API does not return the event title or subtitle, so we use Beautifulsoup to extract them.

The user-generated event description can be hard to parse from raw HTML, but is served succinctly via the API.  The Eventbrite API appears to use `utf-8-sig` encoding. To handle that encoding, we replace `\uffef` with a null string.

These inputs (title, subtitle, details) are combined and fed in along with the prompt.


# TODO:

[ ] Handle Facebook events
[ ] Handle errors - will currently error gracelessly on expired events 
[ ] Meaningfully use feedback / integrate with Weights & Biases
[ ] Allow auto-regeneration of text if output does not meet expectation (exclusion characters, etc)
[ ] Dropdown for model type

