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


def format_string(s:str):
    '''Gets rid of diacriticts and punctution.'''

    format_str = unidecode.unidecode(s)
    bad_chars = [' ', '.', ',', ';', '\'']
    for c in bad_chars:
        format_str = format_str.replace(c, '_')
    return format_str


def save_img(url:str, img_name:str):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"}
    time.sleep(1)
    response = requests.get(url, headers=headers)
    if response.ok:
        with open(img_name, "wb") as f:
            f.write(response.content)
    return response.ok