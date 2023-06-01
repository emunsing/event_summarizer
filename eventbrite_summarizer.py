import requests
from bs4 import BeautifulSoup
import json
import os
from collections import OrderedDict

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

from langchain.prompts import PromptTemplate


NULLIFY_STRINGS = ['\n', '–\xa0']

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

def get_eventbrite_json(event_id):
    headers = {'Authorization': 'Bearer {}'.format(EVENTBRITE_API_KEY)}
    params = {}

    base_url = "https://www.eventbriteapi.com/v3/events/{id}?expand=ticket_classes"

    r = requests.get(base_url.format(id=event_id), headers=headers, params=params)
    effective_encoding =  'utf-8-sig' #r.apparent_encoding  #
    r.encoding = effective_encoding

    return json.loads(r.text)


def get_eventbrite_structured_content(event_id):
    headers = {'Authorization': 'Bearer {}'.format(EVENTBRITE_API_KEY)}
    params = {}

    base_url = "https://www.eventbriteapi.com/v3/events/{id}/structured_content/"

    r = requests.get(base_url.format(id=event_id), headers=headers, params=params)
    effective_encoding =  'utf-8-sig' #r.apparent_encoding  #
    r.encoding = effective_encoding

    return json.loads(r.text)

def get_venue_details(venue_id):
    headers = {'Authorization': 'Bearer {}'.format(EVENTBRITE_API_KEY)}
    params = {}

    base_url = "https://www.eventbriteapi.com/v3/venues/{venue_id}"

    r = requests.get(base_url.format(venue_id=venue_id), headers=headers, params=params)
    effective_encoding =  'utf-8-sig' #r.apparent_encoding  #
    r.encoding = effective_encoding
    venue_json = json.loads(r.text)

    venue_details = {}
    venue_details['venue_name'] = venue_json.get('name', '')

    if 'address' in venue_json:
        venue_details['venue_address'] = venue_json['address'].get('localized_address_display', '')
    else:
        venue_details['venue_address'] = ''

    return venue_details


def get_event_details(event_json):
    # Parse the structured content:
    content = event_json['modules'][0]['data']['body']['text']
    content = content.replace('\ufeff', '')  # Remove byte order mark for utf-8-sig decoding.

    soup = BeautifulSoup(content, 'html.parser')

    details = soup.get_text(separator=' ')
    return details


def parse_ticket_prices(ticket_json):
    ticket_prices = {}

    for t in ticket_json:
        if t['free']:
            ticket_prices[t['name']] = 0
            continue
        else:
            cost = t['cost']
            if cost is not None:
                ticket_prices[t['name']] = float(cost['major_value'])
    return ticket_prices


def get_full_event_info(event_url):

    full_event_info = OrderedDict()
    event_id = get_event_id(event_url)
    

    event_json = get_eventbrite_json(event_id)
    full_event_info['title'] = event_json['name']['text']
    full_event_info['subtitle'] = event_json['summary']
    full_event_info['url'] = event_url
    full_event_info['timezone'] = event_json['start']['timezone']
    full_event_info['start_time'] = event_json['start']['local']
    full_event_info['end_time'] = event_json['end']['local']

    try:
        raw_ticket_prices = parse_ticket_prices(event_json['ticket_classes'])
        full_event_info['free'] = min(raw_ticket_prices.values()) == 0
        full_event_info['tickets'] = '\n'.join([f'{k}: ${v:.02f}' for k, v in raw_ticket_prices.items()])
    except AttributeError as e:
        print("Error while parsing ticket prices")
        print(e)
        full_event_info['free'] = event_json['is_free']
        full_event_info['tickets'] = 'See event site for tickets'

    # The venue detail getter handles issues internally
    venue_details = get_venue_details(event_json['venue_id'])
    full_event_info.update(venue_details)

    try:
        structured_content = get_eventbrite_structured_content(event_id)
        full_event_info['description'] = get_event_details(structured_content)
    except IndexError as e:
        print("Error while parsing venue info")
        print(e)
        full_event_info['description'] = ''
        
    return full_event_info


def summarize_event(event_info_dict, prompt, modeltype="text-davinci-003", temperature=0.3):
    if 'gpt' in modeltype:
        llm = ChatOpenAI(model_name=modeltype, temperature=temperature)
        messages = [
            # SystemMessage(content="You are an excellent journalist working for a fun publication targeting young professionals and young families."),
            HumanMessage(content=prompt.format(**event_info_dict))
        ]
        res = llm(messages).content

    else:
        llm = OpenAI(model_name=modeltype, temperature=temperature)
        res = llm(prompt.format(**event_info_dict))

    output_lines = res.strip().replace('\n\n','\n').split('\n')

    leader = output_lines[0]
    assert("Leader: ") in leader
    leader = leader.replace("Leader: ","")

    summary = ' '.join(output_lines[1:])
    assert("Summary: ") in summary
    summary = summary.replace("Summary: ","")
    
    return leader, summary

def get_eventbrite_summary(event_url, prompt, modeltype="text-davinci-003", temperature=0.3):
    """
    error_handling in "skip", "attempt", 
    """

    event_info_dict = get_full_event_info(event_url)
    leader, summary = summarize_event(event_info_dict, prompt, modeltype, temperature)
    event_info_dict['leader_line'] = leader
    event_info_dict['summary'] = summary

    return event_info_dict

def get_multiple_event_info(event_url_list, prompt, modeltype="text-davinci-003", temperature=0.3):
    res = {}

    for i, url in enumerate(event_url_list):
        print(url)
        res[i] = get_eventbrite_summary(url, prompt, modeltype=modeltype, temperature=temperature)
    
    return res
