import os
import xml.etree.ElementTree as ET
import csv

import utility_funcs as ut
import cap_img_from_alto_deu as ci_alto
import versions as vrs



STRUCT_MAP_TAG = "structMap"

def extract_journal_web_name(url:str)->str:
    '''
    Extracts web name of the journal assuming that given url
    is of the given format: https://digi.ub.uni-heidelberg.de/diglit/antiquitaeten_zeitung
    '''
    split_url = url.split('/')
    return split_url[-1]

def convert_to_xml(url:str)->str:
    # https://digi.ub.uni-heidelberg.de/diglitData/mets/antiquitaeten_zeitung.xml
    # https://digi.ub.uni-heidelberg.de/diglit/antiquitaeten_zeitung

    web_name = extract_journal_web_name(url)
    xml_url = "https://digi.ub.uni-heidelberg.de/diglitData/mets/%s.xml" % (web_name)

    return xml_url

def convert_mets_url_to_iiifv3(mets_url:str)->str:
    '''
    Converts mets url https://digi.ub.uni-heidelberg.de/diglit/antiquitaeten_zeitung1893/mets
    to iiif v.3 url https://digi.ub.uni-heidelberg.de/diglit/iiif3/antiquitaeten_zeitung1893/manifest
    '''

    split_mets_url = mets_url.split('/')
    journal_name_year = split_mets_url[-2]
    iiif_url = "https://digi.ub.uni-heidelberg.de/diglit/iiif3/%s/manifest" % (journal_name_year)
    return iiif_url

def find_href_in_attrib(el:ET.Element)->str:
    href_tag = 'href'
    keys = el.attrib.keys()
    for k in keys:
        if k.endswith(href_tag):
            return el.attrib[k]
    return ""

def parse_struct_map(struct_map:ET.Element)->list[str]:
    volume_mets_hrefs = []
    for el in struct_map:
        for el2 in el:
            for el3 in el2:
                href = find_href_in_attrib(el3)
                if len(href) > 0: volume_mets_hrefs.append(href)
    return volume_mets_hrefs

def find_volume_mets_urls(journal_xml:str)->list[str]:
    tree = ET.parse(journal_xml)
    root = tree.getroot()
    volumes = []
    for el in root:
        if el.tag.endswith(STRUCT_MAP_TAG):
            volumes = parse_struct_map(el)
    return volumes

def find_journal_name(journal_xml:str)->str:
    dmdSec_tag = "dmdSec"
    title_tag = "title"
    # title_info_tag = "titleInfo"
    tree = ET.parse(journal_xml)
    root = tree.getroot()

    for el in root:
        if el.tag.endswith(dmdSec_tag):
            for el2 in el:
                for el3 in el2:
                    for el4 in el3:
                        if el4.tag.endswith(title_tag):
                            return el4.text
    return ""

def add_zero_to_date(date:str)->str:
    if len(date) == 1: return "0%s" % (date)
    return date


def format_single_date(date:str)->str:
    '''Format a single date not a timespan.'''
    if len(date) == 0: return date
    pub_date = ""
    split_date = date.split('.')
    if len(split_date) == 3:
        day = add_zero_to_date(split_date[0])
        month = add_zero_to_date(split_date[1])
        year = split_date[2]
        pub_date = "%s-%s-%s-%s-%s-%s" % (year, month, day, year, month, day)
    elif len(split_date) == 2:
        month = add_zero_to_date(split_date[0])
        year = split_date[1]
        pub_date = "%s-%s-%s-%s-%s-%s" % (year, month, "01", year, month, "31")
    elif len(split_date) == 1:
        year = split_date[0]
        pub_date = "%s-%s-%s-%s-%s-%s" % (year, "01", "01", year, "12", "31")
    return pub_date

def format_half_date(date:str, month:str, day:str)->str:
    if len(date) == 0: return date
    pub_date = ""
    year = ""
    split_date = date.split('.')
    if len(split_date) == 3:
        day = add_zero_to_date(split_date[0])
        month = add_zero_to_date(split_date[1])
        year = split_date[2]
    elif len(split_date) == 2:
        month = add_zero_to_date(split_date[0])
        year = split_date[1]
    elif len(split_date) == 1:
        year = split_date[0]
    pub_date = "%s-%s-%s" % (year, month, day)
    return pub_date

def format_publication_date(date:str)->str:
    if len(date) == 0: return date

    pub_date = ""
    split_date = date.split('-') #might be a span 1.1987-1988
    if len(split_date) == 1:
        pub_date = format_single_date(date)
    elif len(split_date) == 2:
        first_date = format_half_date(split_date[0], month="01", day="01")
        second_date = format_half_date(split_date[1], month="12", day="31")
        pub_date = "%s-%s" % (first_date, second_date)

    return pub_date

'''
def format_publication_date(date:str)->str: 
    if len(date) == 0: return date
    pub_date = ""
    split_date = date.split('.')
    if len(split_date) == 3:
        day = add_zero_to_date(split_date[0])
        month = add_zero_to_date(split_date[1])
        year = split_date[2]
        pub_date = "%s-%s-%s-%s-%s-%s" % (year, month, day, year, month, day)
    elif len(split_date) == 2:
        month = add_zero_to_date(split_date[0])
        year = split_date[1]
        pub_date = "%s-%s-%s-%s-%s-%s" % (year, month, "01", year, month, "31")
    elif len(split_date) == 1:
        year = split_date[0]
        pub_date = "%s-%s-%s-%s-%s-%s" % (year, "01", "01", year, "12", "31")
    return pub_date
'''


def find_publication_date(meta:dict)->str:
    for m in meta:
        if m['label']['en'][0] == 'Date':
            date = m['value']['none'][0]
            date_split = date.split('.')
            date_without_prefix = date_split[1] if len(date_split) == 2 else date
            return date_without_prefix
    return ""

def get_alto_link(ocr_link:str, out_dir:str)->str:
    ocr_json_file = os.path.join(out_dir, 'ocr.json')
    response_ok = ut.read_api_url(ocr_link, ocr_json_file)
    if not response_ok: return
    content = ut.load_json(ocr_json_file)
    alto_link = content['items'][0]['body']['id']
    return alto_link

def work_with_page_image(img_path:str, page_image_url:str, writer:csv.DictWriter, metadata:list[str], page_index:str, res_dir:str, page_writer:csv.DictWriter, alto_link:str):
    journal_name, publication_date, _, issue = metadata
    image_name_prefix = "%s_%s_%s_" % (ut.format_string(ut.shorten_name(journal_name)), ut.format_string(publication_date), ut.format_string(ut.shorten_name(issue)))
    lang = "deu"
    infos = [journal_name, format_publication_date(publication_date), "", issue]

    boxes, captions, degrees_to_rotate, p_w, p_h, highres_img_url = ci_alto.utility(page_image_url, res_dir, alto_link, img_path)
    # success = ut.save_img(highres_img_url, img_path)
    # print("bboxes before cutting:", boxes)
    if len(boxes) > 0:
        percentages = vrs.get_versions(page_index, image_name_prefix, img_path, boxes, res_dir, degrees_to_rotate)
        for j in range(len(boxes)):
            entity = ut.create_entity(page_index, "", j+1, captions[j], percentages[j], boxes[j], infos,
                                      image_name_prefix, p_w, p_h, ut.language_formatting(lang),
                                      highres_img_url, "", "", "")
            writer.writerow(entity)
    page_entity = ut.create_page_entity(page_index, "", infos, p_w, p_h, ut.language_formatting(lang),
                                        highres_img_url, "", "", "")
    page_writer.writerow(page_entity)
    return 

def work_with_page(page:dict, metadata:list[str], out_dir:str, temp_folder:str, writer:csv.DictWriter, page_writer:csv.DictWriter, res_dir:str):
    canvas_id = page['id']

    page_json_file = os.path.join(out_dir, 'page.json')
    response_ok = ut.read_api_url(canvas_id, page_json_file)
    if not response_ok: return

    content = ut.load_json(page_json_file)
    page_index = content['label']['none'][0]
    page_image_url = content['items'][0]['items'][0]['body']['id']
    alto_link = get_alto_link(content['annotations'][0]['id'], out_dir)

    img_name =  ut.format_string(page_index)+".jpeg"
    img_path = os.path.join(temp_folder, img_name)

    work_with_page_image(img_path, page_image_url, writer, metadata, page_index, res_dir, page_writer, alto_link)

    return

def work_with_pages_range(page_range:dict, metadata:list[str], out_dir:str, temp_folder:str, writer:csv.DictWriter, page_writer:csv.DictWriter, res_dir:str, previous:str)->str:
    pages = page_range["items"]
    start = 0
    if len(pages) > 0 and pages[0]['id'] == previous: start = 1

    for i in range(start, len(pages)):
        work_with_page(pages[i], metadata, out_dir, temp_folder, writer, page_writer, res_dir)
        previous = pages[i]['id']
    return previous

def work_with_issue(issue:dict, out_dir:str, temp_folder:str, metadata:list[str]):
    issue_num = issue['label']['none'][0]
    short_issue_num = ut.shorten_name(issue_num)
    metadata[3] = issue_num
    pages = issue['items']

    issue_temp_fol = os.path.join(temp_folder, ut.format_string(short_issue_num))
    ut.create_dir(issue_temp_fol)

    issue_dir_name = "%s_%s_%s" % (ut.shorten_name(metadata[0]), ut.shorten_name(metadata[1]), ut.shorten_name(metadata[3]))#for the page images
    issue_dir_name = ut.format_string(issue_dir_name)
    # issue_temp_fol = os.path.join(issue_temp_fol, issue_dir_name)
    # ut.create_dir(issue_temp_fol)

    res_dir, csvfile_path, csvfile_pages_path = ut.create_result_dirs_and_files(issue_dir_name)
    writer, file = ut.create_csv_writer(csvfile_path, ut.IMG_HEAD_CSV)
    p_writer, p_file = ut.create_csv_writer(csvfile_pages_path, ut.PAGE_HEAD_CSV)

    # previos = ""
    for i in range(len(pages)):
        # if pages[i]['type'] == "Range":
        #     previous = work_with_pages_range(pages[i], metadata, out_dir, issue_temp_fol, writer, p_writer, res_dir, previous)
        # elif pages[i]['type'] == "Canvas":
        work_with_page(pages[i], metadata, out_dir, issue_temp_fol, writer, p_writer, res_dir)
    
    file.close()
    p_file.close()

    big_original_path = os.path.join(res_dir, "big_original")
    ut.clean_if_empty(big_original_path, [csvfile_path, csvfile_pages_path])
    return

def work_with_volume_structure(structures:dict, out_dir:str, temp_folder:str, issue_start:int, metadata:list[str]):
    items = structures[0]['items']
    
    if issue_start > len(items): issue_start = 0
    for i in range(issue_start, len(items)):
        work_with_issue(items[i], out_dir, temp_folder, metadata)
    return

def work_with_volume(mets_url:str, out_dir:str, temp_folder:str, issue_start:str, metadata:list[str]):
    iiif_url = convert_mets_url_to_iiifv3(mets_url)

    volume_json_file = os.path.join(out_dir, 'volume.json')
    response_ok = ut.read_api_url(iiif_url, volume_json_file)
    if not response_ok: return
    content = ut.load_json(volume_json_file)
    publication_date = find_publication_date(content['metadata'])
    # formatted_publication_date = format_publication_date(publication_date)
    metadata[1] = publication_date #formatted_publication_date
    # structures = content['structures']
    # items = content['items']

    year_temp_fol = os.path.join(temp_folder, ut.format_string(publication_date))
    ut.create_dir(year_temp_fol)

    # work_with_volume_structure(structures, out_dir, year_temp_fol, issue_start, metadata)
    work_with_issue(content, out_dir, year_temp_fol, metadata)
    return



def work_with_journal(url:str, out_dir:str, volume_start:int, issue_start:int):
    journal_json_file = os.path.join(out_dir, 'journal.xml')
    response_ok = ut.read_api_url(url, journal_json_file)
    if not response_ok: return

    journal_name = find_journal_name(journal_json_file)
    metadata = [journal_name, '', '', '']
    volume_urls = find_volume_mets_urls(journal_json_file)

    journal_folder_temp = os.path.join(out_dir, ut.format_string(ut.shorten_name(journal_name)))
    ut.create_dir(journal_folder_temp)
    
    if volume_start > len(volume_urls): volume_start = 0
    for i in range(volume_start, len(volume_urls)):
        work_with_volume(volume_urls[i], out_dir, journal_folder_temp, issue_start, metadata)
        issue_start = 0
    
    return



def utility(url:str, volume_start:int, issue_start:int):
    api_url = convert_to_xml(url)
    if api_url == None:
        print("Invalid url: ", url)
        return
    out_dir = 'temp'
    ut.create_dir(out_dir)
    result_dir = 'result'
    ut.create_dir(result_dir)

    work_with_journal(api_url, out_dir, volume_start, issue_start)
    ut.delete_json_files(out_dir)
    return


# url = "https://digi.ub.uni-heidelberg.de/diglit/badische_kunst"
# url = "https://digi.ub.uni-heidelberg.de/diglit/dkd"
url = "https://digi.ub.uni-heidelberg.de/diglit/dkd"
utility(url, 3, 0) #TODO: figure out how to parse second 1899 partition into hefts, get rid of omezeni hledat jen tam kde jsou prazdne textblocks
