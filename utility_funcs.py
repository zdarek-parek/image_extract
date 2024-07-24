import os
import requests
import time
import json
import unidecode
import csv

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
    bad_chars = [' ', '.', ',', ';', '\'', '-', ':']
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


def create_csv_writer(csvfile:str):
    fieldnames = ['journal name', 'issue', 'volume', 'publication date',
                    'page number', 'page index', 'image number', 
                    'caption', 'area in percentage', 'x1', 'y1', 'x2', 'y2', 'image',
                    'width_page', 'height_page', 'language', 
                    'img address', 'author', 'publisher']
    # csvfile = issue_dir_name+'_data.csv'
    f = open(csvfile, 'w', encoding='UTF8', newline='')
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter = ";")
    writer.writeheader()
    return writer, f

def language_formatting(lang:str)->str:
    '''for the database'''
    if lang == "ces": return "cs"
    if lang == "fra": return "fr"
    if lang == "rus": return "ru"
    if lang == "deu": return "de"

def delete_diacritics(s:str)->str:
    return unidecode.unidecode(s)

def create_entity(page_index, number, caption, area_percentage, coords, metadata, im_prefix, p_w, p_h, lang,
                  img_addr, author, publisher):
    journal_name, publication_date, volume, issue_number = metadata
    caption = caption.replace(';', ' ')
    return {"journal name": journal_name,
            "issue":issue_number,
            "volume":volume,
            "publication date":publication_date,
            "page number": "",
            "page index": page_index,
            "image number": number,
            "caption":caption,
            "area in percentage":area_percentage,
            "x1":coords[0],
            "y1":coords[1],
            "x2":coords[2],
            "y2":coords[3],
            "image": (f"{im_prefix}{page_index}_{number}.jpeg"),
            "width_page":p_w, 
            "height_page": p_h, 
            "language":lang,
            "img address":img_addr,
            "author":author, 
            "publisher":publisher}

# print(1024/1409)
# print(3956/5328)