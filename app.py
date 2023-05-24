from eventbrite_summarizer import get_eventbrite_summary
import gradio as gr

description = "Event Summarizer with custom prompting"
title = "Event Summarizer"

top_level_prompt_stub = """You are a journalist writing a calendar of events, and need to create succinct, fun, and energizing summaries of events in 1-2 sentences. You will be given a description of an event you need to summarize; please respond with your brief, fun, and engaging summary."""

prompt_textbox = gr.Textbox(value=top_level_prompt_stub)
url_textbox = gr.Textbox(value='https://www.eventbrite.com/e/greenermind-summit-2023-tickets-576308392917',
                         placeholder='full eventbrite url')

demo = gr.Interface(fn=get_eventbrite_summary,
					description=description,
                    inputs=[url_textbox, prompt_textbox],
                    outputs=['text']
                   )
demo.launch()
