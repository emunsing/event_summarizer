import requests
from bs4 import BeautifulSoup
import json
import os

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
import gradio as gr

EVENTBRITE_API_KEY = os.environ['EVENTBRITE_API_KEY']

def get_event_id(url):
    uid = url.split('?')[0]
    uid = uid.split('/')[-1]
    uid = uid.split('-')[-1]
    return uid

def get_title_subtitle_from_event(event_url):
    # Get the title and subtitle
    res = requests.get(url=event_url)
    soup = BeautifulSoup(res.content, 'html.parser')
    tag_classes = {'title': 'event-title',
                   'subtitle': 'summary',
                   'details': 'has-user-generated-content'}
    title = soup.find(class_ = tag_classes['title']).text
    subtitle = soup.find(class_ = tag_classes['subtitle']).text
    return title, subtitle

def get_event_details(event_url):
    # Now get details:

    event_id = get_event_id(event_url)
    headers = {'Authorization': 'Bearer {}'.format(EVENTBRITE_API_KEY)}
    params = {}

    base_url = "https://www.eventbriteapi.com/v3/events/{id}/structured_content/"

    r = requests.get(base_url.format(id=event_id), headers=headers, params=params)
    effective_encoding =  'utf-8-sig' #r.apparent_encoding  #
    r.encoding = effective_encoding

    res_tree = json.loads(r.text)

    content = res_tree['modules'][0]['data']['body']['text']
    content = content.replace('\ufeff', '')  # Remove byte order mark for utf-8-sig decoding.

    soup = BeautifulSoup(content, 'html.parser')

    details = soup.get_text(separator=' ')
    return details

def get_eventbrite_summary(event_url, top_level_prompt_stub):

    title, subtitle = get_title_subtitle_from_event(event_url)
    details = get_event_details(event_url)

    temperature = 0.3
    openai_modeltype = "text-davinci-003"

    top_level_prompt = top_level_prompt_stub + """
    Event Title:{title}
    Event Subtitle: {subtitle}
    Event Description:
    {description}"""
    
    prompt = PromptTemplate(
        input_variables=['title', 'subtitle', 'description'],
        template=top_level_prompt,
    )

    chat_prompt = prompt.format_prompt(title=title, subtitle=subtitle, description=details)

    llm = OpenAI(model_name=openai_modeltype, temperature=temperature)
    res = llm(chat_prompt.to_messages()[0].content)
    return res.strip()

top_level_prompt_stub = """You are a journalist writing a calendar of events, and need to create succinct, fun, and energizing summaries of events in 1-2 sentences. You will be given a description of an event you need to summarize; please respond with your brief, fun, and engaging summary."""


prompt_textbox = gr.Textbox(value=top_level_prompt_stub)
url_textbox = gr.Textbox(value='https://www.eventbrite.com/e/greenermind-summit-2023-tickets-576308392917',
                         placeholder='full eventbrite url')

demo = gr.Interface(fn=get_eventbrite_summary,
                    inputs=[url_textbox, prompt_textbox],
                    outputs=['text']
                   )
demo.launch()
