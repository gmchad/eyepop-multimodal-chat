import os
from dotenv import load_dotenv
import requests
import json

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
            classy_labels = [obj["classLabel"] for obj in data[0]["objects"]]
            sorted_objects = sort_and_count(classy_labels)
            print(sorted_objects)
            output_string = "\n".join(
                f"{key}: {value}" for key, value in sorted_objects.items()
            )
            # Write the string to a file
            with open("output.txt", "w") as file:
                file.write(output_string)
        else:
            print("The party's over, there was an error:", response.content)


# Load environment variables from .env file

pop_endpoint = os.getenv("pop_endpoint")
token = os.getenv("token")


config = fetch_pop_config(pop_endpoint, token)

file_path = "/Users/namdar/Projects/eyepop-multimodal-chat/photo_for_demo3.jpeg"

get_json_from_eyepop_file(file_path, config)
