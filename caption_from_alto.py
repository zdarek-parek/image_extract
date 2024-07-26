import requests
import xml.etree.ElementTree as ET
import numpy as np
import cv2
import utility_funcs as ut
import os


def get_identifier(page_url:str)->str:
    split_url = page_url.split('/')
    if len(split_url) > 2:
        return split_url[-2]
    return ""

def get_page_num(page_url:str)->str:
    split_url = page_url.split('/')
    if len(split_url) > 1:
        item = split_url[-1]
        f_num = item.split('.')[0]
        num = f_num[1:]
        return num
    return ""

def convert_page_url_to_alto_url(page_url:str)->str:
    '''
    Converts page url to the alto url of the page 
    (example of the expected url: 
    'https://gallica.bnf.fr/services/ajax/pagination/page/SINGLE/ark:/12148/bpt6k9740716w/f1.item')
    '''
    
    identifier = get_identifier(page_url)
    page_num = get_page_num(page_url)

    alto_url = "https://gallica.bnf.fr/RequestDigitalElement?O=%s&E=ALTO&Deb=%s" % (identifier, page_num)
    return alto_url

def get_page_width_height(page_attr:dict)->list[int]:
    ''' Returns width and height of the page.'''
    return [page_attr['WIDTH'], page_attr['HEIGHT']]

def highlight_bbox(img:np.ndarray, bbox:list[int])->np.ndarray:
    cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[0]+bbox[2], bbox[1]+bbox[3]), (0, 0, 255), 2)
    return img

def highlight_bboxes(img_path:str, ill_bboxes:list[list[int]]):
    img = cv2.imread(img_path)
    for bbox in ill_bboxes:
        img = highlight_bbox(img, bbox)
    cv2.imwrite("bboxes_fr.jpeg", img)
    return


def get_element_coordinates(e:ET.Element)->list[int]:
    attrs = e.attrib
    if len(attrs) == 0:
        return [-1, -1, -1, -1]
    
    needed_attrs = ["HPOS", "VPOS", "WIDTH", "HEIGHT"]
    res_attrs = []
    for at in needed_attrs:
        if at in attrs.keys():
            res_attrs.append(int(attrs[at]))
        else:
            return [-1, -1, -1, -1]

    return res_attrs
    
def get_element_content(e:ET.Element)->str:
    attrs = e.attrib
    content_attr_flag = "CONTENT"
    if content_attr_flag in attrs.keys():
        return attrs[content_attr_flag]
    return ""

def parse_string(string:ET.Element):
    content = get_element_content(string)
    coords = get_element_coordinates(string)
    return

def parse_text_line(text_line:ET.Element):
    string_flag = 'String'

    for child in text_line:
        if child.tag.endswith(string_flag):
            parse_string(child)
    return

def parse_text_block(text_block:ET.Element):
    text_line_flag = 'TextLine'
    for child in text_block:
        if child.tag.endswith(text_line_flag):
            parse_text_line(child)
    return

def parse_illustration(illustartion:ET.Element)->list[int]:
    '''Returns coordinates of an illustration in page.'''
    coords = get_element_coordinates(illustartion)
    return coords

def parse_composed_block(composed_block:ET.Element):
    illustration_flag = 'Illustration'
    text_block_flag = 'TextBlock'

    illustration_blocks = []
    text_blocks = []
    for child in composed_block:
        if child.tag.endswith(illustration_flag):
            ill_bl = parse_illustration(child)
            illustration_blocks.append(ill_bl)
        elif child.tag.endswith(text_block_flag):
            # parse_text_block(child)
            text_blocks.append(get_element_coordinates(child))
    
    highlight_bboxes(r"C:\Users\dasha\Desktop\py_projects\pic1.jpg", text_blocks)
    return


def parse_bottom_margin(bottom_margin:ET.Element):# so far assumption: no important info in that area
    return

def parse_print_space(print_space:ET.Element):
    composed_block_flag = 'ComposedBlock'
    for child in print_space:
        if child.tag.endswith(composed_block_flag):
            parse_composed_block(child)
    return

def parse_page(page:ET.Element):
    page_attr = page.attrib
    w, h = get_page_width_height(page_attr)
    bottom_margin_flag = 'BottomMargin'
    print_space_flag = 'PrintSpace'

    for child in page:
        if child.tag.endswith(bottom_margin_flag):
            parse_bottom_margin(child)
        elif child.tag.endswith(print_space_flag):
            parse_print_space(child)

    return

def parse_layout(layout:ET.Element):
    page_flag = 'Page'
    for child in layout:
        if child.tag.endswith(page_flag):
            parse_page(child)

    return

def find_illustrations()->list[list[int]]:
    '''Return list of bboxes of images in page image'''

    return

def work_with_alto_file(alto_file_path:str):
    tree = ET.parse(alto_file_path)
    root = tree.getroot()
    layout_flag = "Layout"
    for child in root:
        if child.tag.endswith(layout_flag):
            parse_layout(child)
            
    
        
    return


def find_caption(alto_file_name:str, img_box:list[int])->str:

    caption = ""
    return caption



def utility(page_url:str, dir_for_alto:str):
    '''Receives page url, calls functions, which find img bboxes and captions.'''
    alto_url = convert_page_url_to_alto_url(page_url)
    alto_path = os.path.join(dir_for_alto, "page_alto.xml")
    ut.download_alto_file(alto_url, alto_path)
    work_with_alto_file(alto_path)
    return


url = "https://gallica.bnf.fr/services/ajax/pagination/page/SINGLE/ark:/12148/bpt6k9740716w/f17.item"
utility(url, '.')
