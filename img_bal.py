import cv2
import os
import sys
import xml.etree.ElementTree as ET
import image_mining_big as getim
import new_caption as cap
import versions as vrs
import os
import csv

TITLE_CONST = 'title'
VOLUME_CONST = 'partNumber'
YEAR_CONST = "dateIssued"
ISSUE_CONST = "partNumber"
LANGUAGE_CONST = "language"

def convert_jp2_to_png(folder_in, folder_out):
    files = os.listdir(folder_in)
    number_of_imgs = 0
    for i, file in enumerate(files):
        file_path = os.path.join(folder_in, file)
        if os.path.isfile(file_path):
            number_of_imgs += 1
            image = cv2.imread(file_path)
            cv2.imwrite(folder_out+'\\'+str(number_of_imgs)+'.png', image)
            # cv2.imwrite(folder_out+'\\'+str(i)+'.png', image)
            # print(i)
    return number_of_imgs

def normilize_date(date : str):
    date_span = date.split('-')
    start = '-01-01-'
    end = '-12-31'
    result = ""
    if len(date_span) == 2:
        result = date_span[0] + start + date_span[1] + end
    elif len(date_span) == 1:
        result = date_span[0] + start + date_span[0] + end

    return result

def get_clean_tag(tag, length):    
    return tag[len(tag)-length:]

def xml_to_dict_recursive(root, attr_name):
    res = []
    for child in root:
        if not child:
            if (get_clean_tag(child.tag, len(attr_name)) == attr_name):
                res.append(child.text)
                return res
        else:
            res += xml_to_dict_recursive(child, attr_name)
    return res

def get_page_nums_inds(root):
    ORDER_KEY = "ORDER"
    ORDERLABEL_KEY = "ORDERLABEL"
    nums = []
    inds = []
    for c in root.iter():
        if (ORDER_KEY in c.attrib.keys() and ORDERLABEL_KEY in c.attrib.keys()):
            nums.append(c.attrib[ORDER_KEY])
            inds.append(c.attrib[ORDERLABEL_KEY])
    return nums, inds

def metadata_reader(file):
    tree = ET.parse(file)
    root = tree.getroot()
    KEY = 'ID'
    KEY2 = "LABEL"
    LABEL = "Physical_Structure"
    TITLE_ID = 'MODSMD_TITLE_0001'
    TITLE2_ID = 'DCMD_TITLE_0001'
    VOLUME_ID = 'MODSMD_VOLUME_0001'
    ISSUE_ID = 'MODSMD_ISSUE_0001'
    res_title = ""
    res_lang = ""
    res_volume = ""
    res_issue = ""
    res_year = ""
    page_nums = []
    page_inds = []
    for child in root:
        if (KEY in child.attrib.keys() and child.attrib['ID'] == TITLE_ID):
            title = xml_to_dict_recursive(child, TITLE_CONST)#title
            if len(title)>0: res_title = title[0]
        elif (KEY in child.attrib.keys() and child.attrib[KEY] == TITLE2_ID):#language
            lang = xml_to_dict_recursive(child, LANGUAGE_CONST)
            if len(lang)>0: res_lang = lang[0]
        elif (KEY in child.attrib.keys() and child.attrib[KEY] == VOLUME_ID):#volume
            volume = xml_to_dict_recursive(child, VOLUME_CONST)
            if len(volume)>0: res_volume = volume[0]
            year = xml_to_dict_recursive(child, YEAR_CONST)
            if len(year) > 0: res_year = normilize_date(year[0])
        elif (KEY in child.attrib.keys() and child.attrib[KEY] == ISSUE_ID):#issue
            issue = xml_to_dict_recursive(child, ISSUE_CONST)
            if (len(issue)>0): res_issue = issue[0]
        elif (KEY2 in child.attrib.keys() and child.attrib[KEY2] == LABEL):
            page_nums, page_inds = get_page_nums_inds(child)
        
    return [res_title, res_lang, res_volume, res_year, res_issue, page_nums, page_inds]

def work_with_batch(img_f, batch_path):
    DATA_FILE_FLAG = "mets"
    metadata = []
    jp2_folder = batch_path+'\\'+'usercopy'
    page_count = 0
    if os.path.exists(jp2_folder):#if there is a folder with jp2s
        files = os.listdir(batch_path)
        for file in files:
            file_path = os.path.join(batch_path, file)
            if os.path.isfile(file_path) and file_path.endswith('.xml') and len(file)>3 and file[0:4].lower() == DATA_FILE_FLAG:
                metadata = metadata_reader(file_path)
        
        batch_name = os.path.splitext(os.path.basename(batch_path))[0]
        folder_name = img_f#+"\\"+batch_name
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)

        page_count = convert_jp2_to_png(jp2_folder, folder_name)
        
    return metadata, page_count

def image_name(metadata):
    parsed_meta = metadata
    if len(parsed_meta) < 4: return ""
    split_pn = metadata[0].split(' ')
    name = ""
    for i in range(len(split_pn)):
        name += split_pn[i][0]
    issue = parsed_meta[1]
    volume = parsed_meta[2]
    year = parsed_meta[3]
    res_name = name+"_%s_%s_%s_" % (year, volume, issue)
    return res_name

def create_folder(folder_name, location):
    new_dir = location+folder_name
    if not os.path.exists(new_dir):
        os.mkdir(new_dir)
        os.mkdir(new_dir+'/'+'big_original')
        return new_dir
    else:
        return new_dir

def create_entity(page_num, page_index, number, caption, area_percentage, coords, metadata, im_prefix, p_w, p_h, lang):
    parsed_meta = [metadata[0], metadata[4], metadata[2], metadata[3]]
    parsed_meta[0] = parsed_meta[0].replace(';', '_') 
    caption = caption.replace(';', ' ')
    return {"journal name": parsed_meta[0],
            "issue":parsed_meta[1],
            "volume":parsed_meta[2],
            "year":parsed_meta[3],
            "page number": page_num,
            "page index": page_index,
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
            "language":lang}

def language_formatting(lang):#for the database
    if lang == "ces": return "cs"
    if lang == "fra": return "fr"
    if lang == "rus": return "ru"
    if lang == "deu": return "de"

def process_data(bfolder:str, metadata:list, output_folder:str, lang_op:str, imgfolder:str, page_count:int):
    parsed_meta = [metadata[0], metadata[4], metadata[2], metadata[3]]
    if len(parsed_meta[0]) == 0: image_name_prefix = ""
    else: image_name_prefix = image_name(parsed_meta)

    journal_info = os.path.splitext(os.path.basename(bfolder))[0]#batch name
    output_dir = create_folder(journal_info, output_folder)
    fieldnames = ['journal name', 'issue', 'volume', 'year',
              'page number', 'page index', 'image number', 
              'caption', 'area in percentage', 'x1', 'y1', 'x2', 'y2', 'image',
              'width_page', 'height_page', 'language']
    csvfile = output_dir+'_data.csv'
    with open(csvfile, 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter = ";")
        writer.writeheader()
        for i in range(1, page_count+1):#page numbers start from 1
            file = imgfolder + "/%d.png" % i
            boxes, p_h, p_w = getim.util(file, lang_op)
            if len(boxes) > 0: #page contains images
                captions, degrees_to_rotate = cap.util(file, boxes, lang_op)
                if (i >= len(metadata[5])): #assumption: page number always has page index
                    pnum, pind = str(i+1), ""
                else:
                    if (i >= len(metadata[6])): pind = ""
                    else: pind =  metadata[6][i]
                    pnum = metadata[5][i]
                percentages = vrs.get_versions(pnum, image_name_prefix, file, boxes, output_dir, degrees_to_rotate)
                for j in range(len(boxes)):
                    entity = create_entity(pnum, pind, j+1, captions[j], percentages[j], boxes[j], metadata,
                                           image_name_prefix, p_w, p_h, language_formatting(lang_op))
                    writer.writerow(entity)
        f.flush()

    return

def util_with_batch(temp_path, res_path, batch_path, lang):
    metadata, page_count = work_with_batch(temp_path, batch_path)
    if len(metadata) == 0:
        return
    process_data(batch_path, metadata, res_path, lang, temp_path, page_count)

