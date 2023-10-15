import os
from dotenv import load_dotenv
import requests

load_dotenv()


def fetch_pop_config(pop_endpoint, token):
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}

    response = requests.get(pop_endpoint, headers=headers)

    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        # Handle the error as you see fit
        return None


def get_json_from_eyepop_file(file_path, config):
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
            print("Success:", data)

        else:
            print("The party's over, there was an error:", response.content)


# Load environment variables from .env file

pop_endpoint = os.getenv("pop_endpoint")
token = os.getenv("token")


config = fetch_pop_config(pop_endpoint, token)

file_path = "/Users/namdar/Projects/eyepop-multimodal-chat/photo_for_demo3.jpeg"

get_json_from_eyepop_file(file_path, config)
