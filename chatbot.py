import os
import openai
import gradio as gr
from dotenv import load_dotenv
import requests
import json

load_dotenv()

OPEN_AI_KEY = os.getenv('OPEN_AI_KEY')
POP_ENDPOINT = os.getenv('POP_ENDPOINT')
TOKEN = os.getenv('TOKEN')

openai.api_key = OPEN_AI_KEY
CONFIG = None

# file name to image description
image_dict = {}

def create_prompt(detected_objects):
  # Create object description string
  object_descriptions = ", ".join([f"{count} {object_ if count > 1 else object_.rstrip('s')}" 
                                    for object_, count in detected_objects.items()])
      
  # Handle grammatical number for people/person
  object_descriptions = object_descriptions.replace("1 people", "1 person")
    
  # Generate prompt
  prompt = (f"The image features a scene with {object_descriptions}. "
            "Craft a concise, short, description of the image, "
            "try including potential interactions or activities that might be happening.")
      
  return prompt

def fetch_pop_config(pop_endpoint, token):
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    response = requests.get(pop_endpoint, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise("Error fetching config")


def sort_and_count(labels):
    """
    Takes a list of labels and returns a sorted dictionary
    where the keys are the labels and the values are the counts of each label.
    """
    count_dict = {}
    for label in labels:
        if label in count_dict:
            count_dict[label] += 1
        else:
            count_dict[label] = 1

    # Sort the dictionary by label
    sorted_dict = dict(sorted(count_dict.items()))
    return sorted_dict

def get_prompt_from_eyepop(file_path, config):
    # Use a with statement to ensure the file is closed after its suite finishes
    with open(file_path, "rb") as f:
        # Create a dictionary to hold the file data
        files = {"file": f}

        url = f"{config['url']}/pipelines/{config['pipeline_id']}/source?mode=preempt&processing=sync"
        headers = {"accept": "application/json"}

        response = requests.post(url, headers=headers, files=files)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            classy_labels = [obj["classLabel"] for obj in data[0]["objects"]]
            # sort objects
            sorted_objects: dict = sort_and_count(classy_labels)
            # generate prompt
            return create_prompt(sorted_objects)
        else:
            raise("The party's over, there was an error:", response.content)

def add_file(history, file):
  history = history + [[[file.name,], None]]
  # get image prompt from eyepop
  image_prompt = get_prompt_from_eyepop(file.name, CONFIG)
  # map file name to eyepop prompt
  image_dict[file.name] = image_prompt
  return history

def clear(msg):
  return ""

def user(user_message, history):
  return history + [[user_message, None]]

def predict(message, history):
    print(1,history)
    history_openai_format = []
    image_file = None
    for human, assistant in history:
        # gradio likes tuples for images, gpt does not, so we need to check
        if isinstance(human, tuple):
          image_file = human[0]
          human = human[0]
          #print(image_file)
        # if assistant is not None, then we have a response from gpt
        if assistant:
          history_openai_format.append({"role": "user", "content": human })
          history_openai_format.append({"role": "assistant", "content":assistant})
      
    # check if message is a filepath and add descrption
    if not isinstance(message, str):  
      image_description = image_dict[image_file]
      message = image_description
      
    '''
    if image_file:
      if isinstance(history[-1], tuple):
        print("!!!!!!!!!!!", history[-1])
      # get image description from dictionary and inject prompt 
      image_description = image_dict[image_file]
      message = message + '\n' + image_description
    '''
      
    history_openai_format.append({"role": "user", "content": message})
    print(2, history_openai_format)
  
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

CSS ="""
.contain { display: flex; flex-direction: column; }
.gradio-container { height: 100vh !important; }
#component-0 { height: 100%; }
#chatbot { flex-grow: 1; overflow: auto;}
"""

title_markdown = ("""
<h2 align="center"> EyePop Multimodal Chatbot 🐙 </h2>            
""")

with gr.Blocks(css=CSS) as demo:
  
  gr.Markdown(title_markdown)
  
  chatbot = gr.Chatbot(
    elem_id="chatbot",
    bubble_full_width=False,
    avatar_images=(None, "./eyepop.png"),
    show_label=False
  )
  
  with gr.Row():
    msg = gr.Textbox(
      scale=4,
      show_label=False,
      placeholder="Enter text and press enter, or upload an image",
      container=False
    )
    btn = gr.UploadButton("upload image 🖼️", file_types=["image"])
    
    file_msg = btn.upload(add_file, [chatbot, btn], [chatbot], queue=False) \
    .then(predict, [btn, chatbot], chatbot) \
    .then(clear, msg, msg)

    msg.submit(user, [msg, chatbot], [chatbot], queue=False) \
    .then(predict, [msg, chatbot], chatbot) \
    .then(clear, msg, msg)
  
if __name__ == "__main__":
  CONFIG = fetch_pop_config(POP_ENDPOINT, TOKEN)
  demo.queue().launch()