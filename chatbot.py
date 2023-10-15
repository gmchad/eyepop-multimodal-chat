import os
import openai
import gradio as gr
from dotenv import load_dotenv
load_dotenv()

OPEN_AI_KEY = os.getenv('OPEN_AI_KEY')
openai.api_key = OPEN_AI_KEY

def user(user_message, history):
  return history + [[user_message, None]]

def predict(message, history):
    history_openai_format = []
    for human, assistant in history:
        # this is always None for the latest message
        if assistant:
          history_openai_format.append({"role": "user", "content": human })
          history_openai_format.append({"role": "assistant", "content":assistant})
    history_openai_format.append({"role": "user", "content": message})
  
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages= history_openai_format,
        temperature=1.0,
        stream=True
    )

    history[-1][1] = ""
    for chunk in response:
        if len(chunk['choices'][0]['delta']) != 0:
            history[-1][1] = history[-1][1] + chunk['choices'][0]['delta']['content']
            yield history

with gr.Blocks() as demo:
  chatbot = gr.Chatbot()
  msg = gr.Textbox()
  msg.submit(user, [msg, chatbot], [chatbot], queue=False).then( 
    predict, [msg, chatbot], chatbot)
  
demo.queue().launch()