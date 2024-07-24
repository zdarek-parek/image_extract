import requests
import xml.etree.ElementTree as ET
import numpy as np
import cv2

def highlight_bbox(img:np.ndarray, bbox:list[int])->np.ndarray:
    ery = img.shape[0]
    erx = img.shape[1]
    cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[0]+bbox[2], bbox[1]+bbox[3]), (0, 0, 0), 2)
    # cv2.imshow('bbox', img)
    # cv2.waitKey()
    return img

def highlight_bboxes(img:np.ndarray, ocr_file_name:str):
    im = cv2.imread(img)
    tree = ET.parse(ocr_file_name)
    root = tree.getroot()
    print(root.tag, root.attrib)
    print()
    layout_flag = "Layout"
    text = []
    for child in root:
        if ends_with(child.tag, layout_flag):
            for gc in child:
                for ggc in gc:
                    for gggc in ggc:
                        if ends_with(gggc.tag, "TextBlock"):
                            for g4c in gggc:
                                ats = g4c.attrib
                                im = highlight_bbox(im, [int(ats["HPOS"]), int(ats["VPOS"]), int(ats["WIDTH"]), int(ats["HEIGHT"]) ])

    cv2.imwrite("bboxes_fr.jpeg", im)
    
    return

def extract_alto_url(img_url:str)->str:
    '''
    given url of the page image the function will 
    compose url of the xmpl file of the page
    '''
    alto_url = ""
    return alto_url

def download_alto_file(url:str)->str:
    response = requests.get(url)
    r = response.content
    print(response.ok)
    alto_file_name = "alto_fr.xml"
    with open(alto_file_name, "wb") as binary_file:
        binary_file.write(r)
    return alto_file_name

def ends_with(str_to_check:str, pattern:str)->bool:
    lp = len(pattern)
    ls = len(str_to_check)
    if str_to_check[ls-lp:] == pattern:
        return True
    return False

def get_attributes(attrs:dict)->dict:
    needed_attrs = [ "HEIGHT", "HPOS", "WIDTH", "VPOS", "CONTENT"]
    res_attrs = {}
    for at in needed_attrs:
        res_attrs[at] = attrs[at]

    return res_attrs

def alto_parser(alto_file_name:str):
    tree = ET.parse(alto_file_name)
    root = tree.getroot()
    print(root.tag, root.attrib)
    print()
    layout_flag = "Layout"
    text = []
    for child in root:
        if ends_with(child.tag, layout_flag):
            for gc in child:
                for ggc in gc:
                    for gggc in ggc:
                        if ends_with(gggc.tag, "TextBlock"):
                            for g4c in gggc:
                                for g5c in g4c:
                                    if ends_with(g5c.tag, "String"):
                                        print(get_attributes(g5c.attrib))
    return

def find_caption(alto_file_name:str, img_box:list[int])->str:

    caption = ""
    return caption

def util(img_bbox:list[int], img_url:str):
    '''This function receives image coordinates and img url'''
    ocr_url = extract_alto_url(img_url)
    alto_file_name = download_alto_file(ocr_url)
    caption = find_caption(alto_file_name, img_bbox)
    return

# url = "https://api.kramerius.mzk.cz/search/api/client/v7.0/items/uuid:34f1d3f5-935d-11e0-bdd7-0050569d679d/ocr/alto"
# url_fr = "https://gallica.bnf.fr/RequestDigitalElement?O=bpt6k5401509q&E=ALTO&Deb=10"
# url = "https://gallica.bnf.fr/RequestDigitalElement?O=bpt6k9740716w&E=ALTO&Deb=17"

# download_alto_file(url)
# alto_f_name = 'alto_cz.xml'
# alto_parser(alto_f_name)

img = r"C:\Users\dasha\Desktop\py_projects\native.jpg"
highlight_bboxes(img, "alto_fr.xml")
