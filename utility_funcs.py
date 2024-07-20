import os
import requests
import time
import json
import unidecode

def create_dir(dir_name:str)->None:
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    return


def read_api_url(api_url:str, file_name:str)->bool:
    time.sleep(1)
    response = requests.get(api_url)
    tries = 5
    while (not response.ok and tries > 0):
        time.sleep(1)
        response = requests.get(api_url)
        tries -= 1

    r = response.content
    with open(file_name, mode = "wb") as binary_file:
        binary_file.write(r)
    return response.ok


def delete_json_files(root_folder:str):
    files_to_delete = ["journal.json", "year.json", "issue.json", "issue.xml", "pages.json", "page.json"]
    for file in files_to_delete:
        if os.path.exists(os.path.join(root_folder, file)):
            os.remove(os.path.join(root_folder, file))
    return

def load_json(name:str)->dict:
    file = open(name, 'r', encoding='UTF8')
    content = json.loads(file.read())
    return content


def make_str_pretty(s:str):
    '''Gets rid of diacriticts and punctution.'''
    s = unidecode.unidecode(s)
    to_replace = [' ', ';', ',', '\'']
    for p in to_replace:
        s = s.replace(p, ' ')

    return s