import requests
import json
import os
from .utils import paths
from dotenv import load_dotenv

load_dotenv(paths.env_path)


def process_workflow(workflow):
    inputMessage = f"Topic: {workflow['VideoTopic']} Type of Content: {workflow['TypeOfContent']} Key Points: {workflow['KeyPoints']}"
    API_URL = "https://www.stack-inference.com/run_deployed_flow?flow_id=64e30750e93e91d17c292b29&org=c31156ff-2281-4f4f-812b-25136c36f6d0"
    headers = {
        'Authorization': f'Bearer {os.getenv("STACKAI")}',
        'Content-Type': 'application/json'
    }
    payload = {
        "in-0": inputMessage
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for non-2xx HTTP status codes
        workflow['stackAiResponse'] = response.json()["out-0"]
        content = str(response.json()["out-0"])

        content = content.replace(
            "[\"choosen-framework", "{\"choosen-framework")
        terminating = content.split(" ")[-1][-6::1]
        to_replace = "".join(
            [char for char in terminating if char in '"\n}]}'])
        by_replace = '"}]}'
        terminating_replace = terminating.replace(to_replace, by_replace)
        content = content.replace(terminating, terminating_replace).replace(
            "\\", "").replace("\n", "")
        content = json.loads(content)
        content["b-roll"] = __format_json(content)

        with open(paths.content_path, "w") as file:
            json.dump(content, file)

    except requests.exceptions.RequestException as error:
        raise Exception(f"Error in Stack AI: {error}")


def __format_json(data: dict):
    new_b_rolls = []
    for b_roll in data["b-roll"]:
        new_b_rolls.append({
            "sentence": b_roll["sentence"],
            "keywords": [keyword.lower() for keyword in str(b_roll["keyword"]).split(", ")]
        })
    data["b-roll"] = new_b_rolls
    return new_b_rolls


if __name__ == "__main__":
    # Example usage:
    workflow = {
        'VideoTopic': 'Books',
        'TypeOfContent': 'Informative',
        'KeyPoints': 'Inspirational'
    }

    try:
        process_workflow(workflow)
        # print(workflow['stackAiResponse'])
    except Exception as e:
        print(e)
