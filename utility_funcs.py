import os
import requests
import time
import json

def create_dir(dir_name:str)->None:
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    return


def read_api_url(api_url:str, json_name:str)->bool:
    time.sleep(1)
    response = requests.get(api_url)
    tries = 5
    while (not response.ok and tries > 0):
        time.sleep(1)
        response = requests.get(api_url)
        tries -= 1

    r = response.content
    with open(json_name, "wb") as binary_file:
        binary_file.write(r)
    return response.ok


def delete_json_files(root_folder:str):
    files_to_delete = ["journal.json", "year.json", "issue.json"]
    for file in files_to_delete:
        if os.path.exists(os.path.join(root_folder, file)):
            os.remove(os.path.join(root_folder, file))
    return

def load_json(name:str)->dict:
    file = open(name, 'r', encoding='UTF8')
    content = json.loads(file.read())
    return content