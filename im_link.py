import requests
import json
import os
from unidecode import unidecode
import csv
import image_mining_big as getim
import new_caption as cap
import versions as vrs
import time
import utility_funcs as ut

def find_lib(url:str)->str:
    divider = '/'
    url_dirs = url.split(divider)
    if len(url_dirs) < 5:
        return
    NDK = "ndk.cz"
    KRAMERIUS_NKP = "kramerius5.nkp.cz"
    NKP = "nkp"
    MZK = "mzk"
    MLP = "mlp"
    if url_dirs[2] == NDK:
        return NKP
    if url_dirs[2] == KRAMERIUS_NKP:
        return NKP
    if url_dirs[3] == MZK:
        return MZK
    if url_dirs[3] == MLP:
        return MLP
    return

def find_id(url:str)->str:
    divider = '/'
    domens = url.split(divider)
    id_flag = "uuid:"
    for i in range(len(domens)):
        if len(domens[i]) >= 5:
            if domens[i][:5] == id_flag:
                ids = domens[i].split('?')
                return ids[0]
    return

def convert_to_iiif(url:str)->str:
    lib_abbr = find_lib(url)
    if lib_abbr == None:
        return None
    uuid = find_id(url)
    if uuid == None:
        return None
    head = "https://iiif."
    library_domain = f"digitalniknihovna.cz/{lib_abbr}/"
    iiif_url = head+library_domain+uuid
    return iiif_url


def parse_json(name:str)->dict: #load+json in utility_func
    file = open(name, 'r', encoding='UTF8')
    content = json.loads(file.read())
    return content

def extract_metadata(metadata:dict)->dict:#find doc type and language
    md = {'lang':'ces'} #default
    lang_map = {"němčina":"deu", "francouzština":"fra", "ruština":"rus", "čeština":"ces"}
    for m in metadata:
        if m["label"]["cz"][0] == "Jazyk":
            md['lang'] = lang_map[m["value"]["none"][0]]
        if m["label"]["cz"][0] == "Typ dokumentu":
            md['doctype'] = m["value"]["cz"][0]
    return md

def extract_part_num(metadata:dict)->str:
    for m in metadata:
        if m["label"]["cz"][0] == "Číslo části":
            return m["value"]["none"][0]
    return None

def extract_monografy_name(metadata:dict)->str:
    for m in metadata:
        if m["label"]["cz"][0] == "Název":
            return m["value"]["none"][0]
    return None


def create_dir(dir_name:str)->None:
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    return

def create_result_dirs_and_files(issue_dir_name:str):
    result_root = "result"
    result_dir = os.path.join(result_root, issue_dir_name)#extracted reproductions
    create_dir(result_dir)
    result_dir_big = os.path.join(result_dir, 'big_original')
    create_dir(result_dir_big)
    csvfile = issue_dir_name+'_data.csv'
    csvfile_path = os.path.join(result_root, csvfile)
    return result_dir, csvfile_path

def work_with_monografy(content:dict, lang:str, out_dir:str):
    monografy_name = extract_monografy_name(content["metadata"])

    monografy_out_dir = os.path.join(out_dir, monografy_name)
    monografy_out_dir = ut.format_string(monografy_out_dir)
    create_dir(monografy_out_dir)

    items = content["items"]

    res_dir, csvfile_path = create_result_dirs_and_files(ut.format_string(monografy_name))
    writer, file = ut.create_csv_writer(csvfile_path)
    infos = [monografy_name, "", "", ""]
    for item in items:
        success = work_with_page(item, monografy_out_dir, writer, infos, res_dir, lang)
        if not success:
            return
    return

def work_with_periodical(content:dict, lang:str, out_dir:str, root_dir:str, volume_start:int, issue_start:int):
    # print(lang)
    journal_name = content["label"]["none"][0]
    out_dir = os.path.join(out_dir, journal_name)
    out_dir = ut.format_string(out_dir)
    create_dir(out_dir)
    items = content["items"]
    
    if volume_start > len(items): volume_start = 0 #if the start is greayer than the number of items
    
    for i in range(volume_start, len(items)):
    # for item in items:
        work_with_year(items[i], journal_name, lang, out_dir, root_dir, issue_start)
        issue_start = 0
        # volume_start = 0
    return

def work_with_year(year_item:dict, journal_name:str, lang:str, out_dir:str, root_dir:str, issue_start:int):
    uuid = year_item["id"]
    year = year_item["label"]["none"][0]
    year_json_name = os.path.join(root_dir, "year.json")
    response_ok = ut.read_api_url(uuid, year_json_name)
    if not response_ok: return True
    content = parse_json(year_json_name)
    volume = extract_part_num(content["metadata"])
    out_dir = os.path.join(out_dir, year)
    out_dir = ut.format_string(out_dir)
    create_dir(out_dir)
    items = content["items"]

    if issue_start > len(items): issue_start = 0 # if the start is greayer than the number of items
    
    for i in range(issue_start, len(items)):
    # for item in items:
        success = work_with_issue(items[i], journal_name, year, volume, lang, out_dir, root_dir)
        if not success:
            os.rmdir(out_dir)
            return False
    return True

def find_publication_date(metadata:dict)->str:
    for item in metadata:
        if item['label']['cz'][0] == "Vydáno":
            return item['value']['none'][0]
    return ""

def convert_month_to_number(month:str)->str:
    month = ut.delete_diacritics(month.lower())
    months = {'leden':'01', 'unor':'02', 'brezen':'03', 
              'duben':'04', 'kveten':'05', 'cerven':'06', 
              'cervenec':'07', 'srpen':'08', 'zari':'09', 
              'rijen':'10', 'listopad':'11', 'prosinec':'12'}

    return months[month]

def formta_publication_date(date:str)->str:
    publication_date = ""
    if len(date) == 0: return publication_date
    time_span = date.split('-')
    if len(time_span) == 1: # single date, not a span
        single_date = time_span[0].split('.')
        if len(single_date) == 1: # a year or month year
            month_year = single_date[0].split(' ')
            if len(month_year) == 2: # month year, month a word not a number
                month = convert_month_to_number(month_year[0]) 
                year = month_year[1]
                publication_date = "%s-%s-%s-%s-%s-%s" % (year, month, "01", year, month, "31")
            elif len(month_year) == 1:
                year = month_year[0]
                publication_date = "%s-%s-%s-%s-%s-%s" % (year, "01", "01", year, "12", "31")
        elif len(single_date) == 2:
            month = single_date[0]
            year = single_date[1]
            publication_date = "%s-%s-%s-%s-%s-%s" % (year, month, "01", year, month, "31")
        elif len(single_date) == 3:
            day = single_date[0]
            month = single_date[1]
            year = single_date[2]
            publication_date = "%s-%s-%s-%s-%s-%s" % (year, month, day, year, month, day)
    elif len(time_span) == 2: # it is a time span, at this point it can process only 08.-09.1904
        first_month = time_span[0]
        second_month_year = time_span[1]
        single_date1 = first_month.split('.')
        single_date2 = second_month_year.split('.')
        if len(single_date2) == 2 and len(single_date1) == 2:
           month1 = single_date1[0]
           month2 = single_date2[0]
           year = single_date2[1]
           publication_date = "%s-%s-%s-%s-%s-%s" % (year, month1, "01", year, month2, "31")

    return publication_date

def work_with_issue(issue_item:dict, journal_name:str, year:str, volume:str, lang:str, out_dir:str, root_dir:str):
    uuid = issue_item["id"]
    issue_json_name = os.path.join(root_dir, "issue.json")
    response_ok = ut.read_api_url(uuid, issue_json_name)
    if not response_ok: return True
    content = parse_json(issue_json_name)
    issue_number = extract_part_num(content["metadata"])
    publication_date = find_publication_date(content["metadata"])
    publication_date = formta_publication_date(publication_date)
    
    issue_dir_name = "%s_%s_%s_%s" % (journal_name, year, volume, issue_number)#for the images
    issue_dir_name = ut.format_string(issue_dir_name)
    issue_res_dir = os.path.join(out_dir, issue_dir_name)
    create_dir(issue_res_dir)
    
    items = content["items"]

    res_dir, csvfile_path = create_result_dirs_and_files(issue_dir_name)
    writer, file = ut.create_csv_writer(csvfile_path)
    infos = [journal_name, publication_date, volume, issue_number]

    for item in items:
        success = work_with_page(item, issue_res_dir, writer, infos, res_dir, lang)
        if not success:
            file.close()
            os.remove(csvfile_path)
            os.rmdir(os.path.join(res_dir, "big_original"))
            os.rmdir(res_dir)
            os.rmdir(issue_res_dir)
            return False
    
    return True


def process_image(img_file:str, img_url:str, lang:str, writer:csv.DictWriter, infos:list, page_index:str, res_dir:str):
    journal_name, publication_date, volume, issue_number = infos
    image_name_prefix = "%s_%s_%s_%s_" % (journal_name, publication_date, volume, issue_number)
    boxes, p_h, p_w = getim.util(img_file, lang)
    if len(boxes) > 0: #page contains images
        captions, degrees_to_rotate = cap.util(img_file, boxes, lang) 
        percentages = vrs.get_versions(page_index, image_name_prefix, img_file, boxes, res_dir, degrees_to_rotate)
        for j in range(len(boxes)):
            entity = ut.create_entity(page_index, j+1, captions[j], percentages[j], boxes[j], infos, 
                                    image_name_prefix, p_w, p_h, ut.language_formatting(lang), 
                                    img_url, "", "")
            # three last are 'author', 'publisher'
            writer.writerow(entity)
    return

def work_with_page(page_item:dict, out_dir:str, writer:csv.DictWriter, infos:list, res_dir:str, lang:str):
    page_index = page_item["label"]["none"][0]
    img_url = page_item["items"][0]["items"][0]["body"]["id"]

    img_name = os.path.splitext(os.path.basename(out_dir))[0] +"_"+ ut.format_string(page_index)+".jpeg"
    img_path = os.path.join(out_dir, img_name)
    success = ut.save_img(img_url, img_path)
    if success:
        process_image(img_path, img_url, lang, writer, infos, page_index, res_dir)
        # print("processed image", img_name)
    return success

def work_with_journal(url:str, out_dir:str, root_dir:str, volume_start:int, issue_start:int):
    journal_json_file = os.path.join(root_dir, 'journal.json')
    response_ok = ut.read_api_url(url, journal_json_file)
    if not response_ok: return
    content = parse_json(journal_json_file)
    metadata = extract_metadata(content["metadata"])
    if metadata["doctype"] == "Monografie":
        work_with_monografy(content, metadata["lang"], out_dir)
    if metadata["doctype"] == "Periodikum":
        work_with_periodical(content, metadata["lang"], out_dir, root_dir, volume_start, issue_start)
    return

def delete_json_files(root_folder:str):
    files_to_delete = ["journal.json", "year.json", "issue.json"]
    for file in files_to_delete:
        if os.path.exists(os.path.join(root_folder, file)):
            os.remove(os.path.join(root_folder, file))
    return

def utility(url:str, volume_start:int, issue_start:int):
    api_url = convert_to_iiif(url)
    if api_url == None:
        print("invalid url:", url)
        return
    out_dir = 'temp'
    create_dir(out_dir)
    result_out_dir = 'result'
    create_dir(result_out_dir)
    work_with_journal(api_url, out_dir, out_dir, volume_start, issue_start)
    delete_json_files(out_dir)
    return

# utility('https://www.digitalniknihovna.cz/mzk/periodical/uuid:b75722a2-935c-11e0-bdd7-0050569d679d', 0, 9)
# url = "https://api.kramerius.mzk.cz/search/api/client/v7.0/items/uuid:34f1d3f5-935d-11e0-bdd7-0050569d679d/ocr/alto"