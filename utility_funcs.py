import os
import requests
import time
import json
import unidecode
import csv



last_request_time = 0

def check_time():
    current_time = time.time()
    if (current_time - last_request_time) < 10:
        time.sleep(10 - (current_time - last_request_time))

def create_dir(dir_name:str)->None:
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    return


def read_api_url(api_url:str, file_name:str)->bool:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"}
    check_time()
    time.sleep(1)
    response = requests.get(api_url, headers=headers)
    global last_request_time
    last_request_time = time.time()
    tries = 5
    while (not response.ok and tries > 0):
        check_time()
        time.sleep(1)
        response = requests.get(api_url, headers=headers)
        last_request_time = time.time()
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

def download_alto_file(url:str, file_name:str)->str:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"}
    check_time()
    time.sleep(1)
    response = requests.get(url, headers=headers)
    global last_request_time
    last_request_time = time.time()
    if not response.ok:
        for _ in range(5):
            check_time()
            time.sleep(1)
            response = requests.get(url, headers=headers)
            last_request_time = time.time()
    r = response.content
    
    with open(file_name, "wb") as binary_file:
        binary_file.write(r)
    return file_name

def format_string(s:str):
    '''Gets rid of diacriticts and punctution.'''

    format_str = unidecode.unidecode(s)
    bad_chars = [' ', '.', ',', ';', '\'', '-', ':']
    for c in bad_chars:
        format_str = format_str.replace(c, '_')
    return format_str

def save_img_unsafe(url:str, img_name:str):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"}
    check_time()
    time.sleep(1)
    response = requests.get(url, headers=headers)
    global last_request_time
    last_request_time = time.time()
    if response.ok:
        with open(img_name, "wb") as f:
            f.write(response.content)
    return response.ok
    
def save_img(url:str, img_name:str):
    try:
        response_ok = save_img_unsafe(url, img_name)
        return response_ok
    except Exception as e:
        print("Error occured. The error is ", e)
        time.sleep(60)
        response_ok = save_img_unsafe(url, img_name)
        return response_ok



def create_csv_writer(csvfile:str):
    fieldnames = ['journal name', 'issue', 'volume', 'publication date',
                    'page number', 'page index', 'image number', 
                    'caption', 'area in percentage', 'x1', 'y1', 'x2', 'y2', 'image',
                    'width_page', 'height_page', 'language', 
                    'img address', 'author', 'publisher', 'contributor']
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
                  img_addr, author, publisher, contributor):
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
            "publisher":publisher,
            "contributor":contributor}


