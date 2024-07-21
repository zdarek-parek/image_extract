import image_mining_big as getim
import new_caption as cap
import versions as vrs
import os
import csv
from unidecode import unidecode
# import cv2
# import re


def parse_metadata(metadata):
    parsed_metadata = ['', '', '', '']
    name_issue_year = metadata.split(', ')
    for i in range(len(name_issue_year)):
        parsed_metadata[i] = name_issue_year[i]
        if i == 3:
            break
    return parsed_metadata

def image_name(metadata):
    parsed_meta = metadata
    split_pn = metadata[0].split(' ')
    name = ""
    for i in range(len(split_pn)):
        name += split_pn[i][0]
    issue = parsed_meta[1]
    volume = parsed_meta[2]
    year = parsed_meta[3]
    res_name = name+"_%s_%s_%s_" % (year, volume, issue)
    return res_name

def util_without_pagenum(input_folder, output_folder, page_count, lang_op, pdf_name, metadata):
    parsed_meta = parse_metadata(metadata)
    if len(parsed_meta[0]) == 0: image_name_prefix = ""
    else: image_name_prefix = image_name(parsed_meta)
    journal_info = os.path.splitext(os.path.basename(pdf_name))[0]
    journal_info = unidecode(journal_info).replace(' ', '_')
    output_dir = create_folder(journal_info, output_folder)
    fieldnames = ['journal name', 'issue', 'volume', 'year',
              'page number', 'page index', 'image number', 
              'caption', 'area in percentage', 'x1', 'y1', 'x2', 'y2', 'image',
              'width_page', 'height_page', 'language', 
              'img address', 'author', 'publisher', 'publication date']
    csvfile = output_dir+'_data.csv'
    with open(csvfile, 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter = ";")
        writer.writeheader()
        for i in range(page_count+1):
            file = input_folder + "/%d.png" % i
            boxes, p_h, p_w = getim.util(file, lang_op)
            if len(boxes) > 0: #page contains images
                captions, degrees_to_rotate = cap.util(file, boxes, lang_op) 
                page_num = i+1
                percentages = vrs.get_versions(page_num, image_name_prefix, file, boxes, output_dir, degrees_to_rotate)
                for j in range(len(boxes)):
                    entity = create_entity(page_num, j+1, captions[j], percentages[j], boxes[j], metadata, 
                                           image_name_prefix, p_w, p_h, language_formatting(lang_op),
                                           "", "", "", "")
                    # the last four 'img address', 'author', 'publisher', 'publication date'
                    writer.writerow(entity)
        f.flush()

def create_folder(folder_name, location):
    new_dir = location+folder_name
    if not os.path.exists(new_dir):
        os.mkdir(new_dir)
        os.mkdir(new_dir+'/'+'big_original')
        return new_dir
    else:
        return new_dir

def create_entity(page_num, number, caption, area_percentage, coords, metadata, im_prefix, p_w, p_h, lang, 
                  img_addr, author, publisher, publication_date):
    parsed_meta = parse_metadata(metadata)
    parsed_meta[0] = parsed_meta[0].replace(';', '_') 
    caption = caption.replace(';', ' ')
    return {"journal name": parsed_meta[0],
            "issue":parsed_meta[1],
            "volume":parsed_meta[2],
            "year":parsed_meta[3],
            "page number": page_num,
            "page index": "",
            "image number": number,
            "caption":caption,
            "area in percentage":area_percentage,
            "x1":coords[0],
            "y1":coords[1],
            "x2":coords[2],
            "y2":coords[3],
            "image": (f"{im_prefix}{page_num}_{number}.jpeg"),
            "width_page":p_w, 
            "height_page": p_h, 
            "language":lang,
            "img address":img_addr,
            "author":author, 
            "publisher":publisher,
            "publication date":publication_date
            }

def language_formatting(lang):#for the database
    if lang == "ces": return "cs"
    if lang == "fra": return "fr"
    if lang == "rus": return "ru"
    if lang == "deu": return "de"

# file = r"app_EXIM/temp/1901_07_VOLNE_SMERY_V/2.png"
# boxes, p_h, p_w = getim.util(file, 'fra')


# inf = r"C:\Users\dasha\Desktop\py_projects\app_EXIM\temp\1939_Minotaure_12_13"
# outf = r"C:\Users\dasha\Desktop\py_projects\app_EXIM\result\err2"
# pdf_n = r"C:\Users\dasha\Desktop\err2\1939_Minotaure_12_13.pdf"
# util_without_pagenum(inf, outf, 24, "fra", pdf_n, "Minotaur, 13-14, , 1933")