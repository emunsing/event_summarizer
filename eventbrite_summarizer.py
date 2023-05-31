import requests
from bs4 import BeautifulSoup
import json
import os

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate


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
    try:
        title = soup.find(class_ = tag_classes['title']).text
    except AttributeError as e:
        raise AttributeError("No event title found on page; has it expired?")
    
    try:
        subtitle = soup.find(class_ = tag_classes['subtitle']).text
    except AttributeError as e:
        raise AttributeError("No subtitle found on page; has it expired?")
    
    return title, subtitle

def get_eventbrite_json(event_url):
    event_id = get_event_id(event_url)
    headers = {'Authorization': 'Bearer {}'.format(EVENTBRITE_API_KEY)}
    params = {}

    base_url = "https://www.eventbriteapi.com/v3/events/{id}/structured_content/"

    r = requests.get(base_url.format(id=event_id), headers=headers, params=params)
    effective_encoding =  'utf-8-sig' #r.apparent_encoding  #
    r.encoding = effective_encoding

    return json.loads(r.text)

def get_event_details(event_json):
    # Now get details:

    content = event_json['modules'][0]['data']['body']['text']
    content = content.replace('\ufeff', '')  # Remove byte order mark for utf-8-sig decoding.

    soup = BeautifulSoup(content, 'html.parser')

    details = soup.get_text(separator=' ')
    return details

def get_eventbrite_summary(event_url, top_level_prompt_stub, error_handling='attempt', modeltype="text-davinci-003", temperature=0.3):
    """
    error_handling in "skip", "attempt", 
    """
    errors = []

    try:
        title, subtitle = get_title_subtitle_from_event(event_url)
    except AttributeError as e:
        errors.append(e)
        print(e)
        title, subtitle = '', ''

    try:        
        event_json = get_eventbrite_json(event_url)
        details = get_event_details(event_json)
    except AttributeError as e:
        errors.append(e)
        print(e)
        details = ''

    if errors and error_handling=='skip':
        return 'Error'
    
    openai_modeltype = modeltype

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
