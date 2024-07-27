import requests
import xml.etree.ElementTree as ET
import numpy as np
import cv2
import utility_funcs as ut
import os
import new_caption as nc

def highlight_bbox(img:np.ndarray, bbox:list[int])->np.ndarray:
    cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[0]+bbox[2], bbox[1]+bbox[3]), (0, 0, 255), 2)
    return img

def highlight_bboxes(img_path:str, ill_bboxes:list[list[int]]):
    img = cv2.imread(img_path)
    for bbox in ill_bboxes:
        img = highlight_bbox(img, bbox)
    cv2.imwrite("bboxes_fr.jpeg", img)
    return


right_flag = "right"
left_flag = "left"
up_flag = "up"
bottom_flag = "bottom"


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


def get_element_width_height(attr:dict)->list[int]:
    ''' Returns width and height of the element.'''
    return [attr['WIDTH'], attr['HEIGHT']]

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


def find_elements_in_composed_block(composed_block:ET.Element, bbox_flag:str)->list[ET.Element]:
    '''returns elements with given flag found in a composed block of the alto file.'''
    blocks = []
    for child in composed_block:
        if child.tag.endswith(bbox_flag):
            blocks.append(child)
    return blocks

def parse_bottom_margin(bottom_margin:ET.Element):# so far assumption: no important info in that area
    return

def parse_print_space(print_space:ET.Element, bbox_flag:str)->list[ET.Element]:
    composed_block_flag = 'ComposedBlock'

    blocks = []
    for child in print_space:
        if child.tag.endswith(composed_block_flag):
            blocks += find_elements_in_composed_block(child, bbox_flag)
    return blocks

def parse_page(page:ET.Element, bbox_flag:str)->list[ET.Element]:
    page_attr = page.attrib
    w, h = get_element_width_height(page_attr)
    bottom_margin_flag = 'BottomMargin'
    print_space_flag = 'PrintSpace'

    blocks = []
    for child in page:
        if child.tag.endswith(bottom_margin_flag):
            parse_bottom_margin(child)
        elif child.tag.endswith(print_space_flag):
            blocks += parse_print_space(child, bbox_flag)

    return blocks

def parse_layout(layout:ET.Element, bbox_flag:str)->list[ET.Element]:
    page_flag = 'Page'

    blocks = []
    for child in layout:
        if child.tag.endswith(page_flag):
            blocks += parse_page(child, bbox_flag)

    return blocks


def find_interesting_bboxes_in_alto(alto_file_path:str, bbox_flag:str)->list[ET.Element]:
    tree = ET.parse(alto_file_path)
    root = tree.getroot()
    layout_flag = "Layout"

    blocks = []
    for child in root:
        if child.tag.endswith(layout_flag):
            blocks += parse_layout(child, bbox_flag)
            
    return blocks


def get_pos(ill_bbox:list[int], text_bbox:list[int])->str:
    '''Returns a position of the bbox in relation to the image if the bbox has a probability of containing caption.'''
    x1, y1, x2, y2 = ill_bbox[0], ill_bbox[2], ill_bbox[0]+ill_bbox[2], ill_bbox[2]+ill_bbox[3] # image in page
    x3, y3, x4, y4 = text_bbox[0], text_bbox[2], text_bbox[0]+text_bbox[2], text_bbox[2]+text_bbox[3] # text block
    if x2 < x3: 
        if is_possible_to_contain_caption_right_left(ill_bbox, text_bbox):
            return right_flag
    if x4 < x1:
        if is_possible_to_contain_caption_right_left(ill_bbox, text_bbox):
            return left_flag
    if y1 > y4: 
        if is_possible_to_contain_caption_up_down(ill_bbox, text_bbox):
            return up_flag
    if y2 < y3:
        if is_possible_to_contain_caption_up_down(ill_bbox, text_bbox):
            return bottom_flag
    return ''

def is_possible_to_contain_caption_right_left(ill_coords:list[int], bbox:list[int]):
    x1, y1, x2, y2 = ill_coords[0], ill_coords[2], ill_coords[0]+ill_coords[2], ill_coords[2]+ill_coords[3] # image in page
    x3, y3, x4, y4 = bbox[0], bbox[2], bbox[0]+bbox[2], bbox[2]+bbox[3] # text block

    if y1 < y4 and y2 > y3: return True
    return False

def is_possible_to_contain_caption_up_down(ill_coords:list[int], bbox:list[int]):
    x1, y1, x2, y2 = ill_coords[0], ill_coords[2], ill_coords[0]+ill_coords[2], ill_coords[2]+ill_coords[3] # image in page
    x3, y3, x4, y4 = bbox[0], bbox[2], bbox[0]+bbox[2], bbox[2]+bbox[3] # text block

    if x1 < x4 and x2 > x3: return True
    return False

def match_bboxes_to_illustrations(illustration:ET.Element, bboxes:list[ET.Element])->dict:
    '''Returns dictionary, which contains text blocks around the image which are the most probable to contain caption. '''
    ill_coords = get_element_coordinates(illustration)
    bboxes_pos = {right_flag:[], left_flag:[], up_flag:[], bottom_flag:[]}
    for bbox in bboxes:
        bb_coords = get_element_coordinates(bbox)
        pos = get_pos(ill_coords, bb_coords)
        if len(pos) > 0:
            bboxes_pos[pos].append(bbox)

    return bboxes_pos


def find_page_width_height(alto_path:str)->list[int]:
    tree = ET.parse(alto_path)
    root = tree.getroot()
    layout_flag = "Layout"

    blocks = []
    for child in root:
        if child.tag.endswith(layout_flag):
            page_flag = 'Page'
            for child2 in child:
                if child2.tag.endswith(page_flag):
                    return get_element_width_height(child2.attrib)
            
    return 0, 0


def get_element_bbox_square(e:ET.Element)->int:
    w, h = get_element_width_height(e)
    return w*h

def read_caption()->str:
    '''Returns text, which is in the given element or list of elements'''
    return

def find_nearest_text_bottom(ill_coords, text_blocks:list[ET.Element], width_orig:int, height_orig:int):
    sorted_blocks = sorted(text_blocks, key = lambda b: get_element_coordinates(b)[1]) # 1. sort according to the distance from the image

    closest_text_block = sorted_blocks[0]
    res = []
    for i in range(1, len(sorted_blocks)): # 2. discard too small or too big text blocks
        if (1_000 <= get_element_bbox_square(sorted_blocks[i]) <= ill_coords[2]*ill_coords[3]/2):
            res.append(sorted_blocks[i])

    if len(res) == 0:
        if get_element_width_height(closest_text_block)[1] < ill_coords[3]/2: # already checked if the size is appropriate (2.), now need to make sure that it is nit too high
            ctb_coords = get_element_coordinates(closest_text_block)
            dist_between_img_and_text_block = ctb_coords[1] - (ill_coords[1]+ill_coords[3])
            return [closest_text_block], dist_between_img_and_text_block
        return res, -1
    else: # 3. find text blocks that are close to the closest text block to the image
        
        close_text = sorted(res, key = lambda b: b[1])
        #TODO: write alg to find close text_blocks to the closest text block to the image
        # if get_element_bbox_square(cap_box) > width_orig*height_orig/4 and height_orig > 2_000:
        #     return [], -1
        # elif len(sorted_blocks) > 0 and is_in_textcolumn(cap_box, sorted_blocks):
        #     return [], -1
        # elif (cap_box[2]-cap_box[0])/(cap_box[3]-cap_box[1]) < 10 and get_element_bbox_square(cap_box) > width_orig*height_orig/5:#500_000
        #     return [], -1
        # elif nc.is_too_high(height_orig, cap_box) and height_orig > 2_000:#if small area, text can be big
        #     return [], -1
        # elif len(close_text) > 0 and 3_000 < get_element_bbox_square(close_text[0])  and abs(close_text[0][1]-cap_box[3]) < min_distance*2/3:
        #     return [], -1
        # elif cap_box[3]-cap_box[1] < 10:
        #     return [], -1
        # else:
        #     '''
        #     if len(close_text) == 1 and (get_box_square(close_text[0])/get_box_square(cap_box)) < 1:
        #         if not ((get_box_square(cap_box) + get_box_square(close_text[0])) > max_wid*max_hei/4 and max_hei > 1_000):
        #             sparse_cap_box = [cap_box, close_text[0]]
        #             bigger_cap_box = get_caption_box(sparse_cap_box)
        #             cap_box = bigger_cap_box
        #     return cap_box, cap_box[1]
        #     '''
        #     sparse_cap_boxes = []##test
        #     for cap_b in close_text:
        #         if (not ((get_element_bbox_square(cap_box) + get_element_bbox_square(cap_b)) > max_wid*max_hei/8 and max_hei > 1_000) and
        #             (cap_b[2]-cap_b[0])/(cap_b[3]-cap_b[1]) > 5):#TODO:test const
        #             sparse_cap_boxes.append(cap_b)
        #         else: 
        #             sparse_cap_boxes = []#if there is a big block of text, then only cap_box
        #             break
        #     sparse_cap_boxes.append(cap_box)
        #     bigger_cap_box = get_caption_box(sparse_cap_boxes)
        #     return bigger_cap_box, bigger_cap_box[1]

def work_with_bottom(ill_coords:list[int], text_blocks:list[ET.Element], width:int, height:int)->tuple:
    if len(text_blocks) > 0:
        cap_box, distance = find_nearest_text_bottom(ill_coords, text_blocks, width, height)
    if len(cap_box) > 0:
        caption = read_caption(cap_box)
        caption = " ".join(caption.strip().split())
        if (len(caption.split(' ')) <= 30 and len(caption) != 0):
            return caption, distance, 0
    return "", -1, 0
    
    


def find_caption(illustration:ET.Element, text_blocks:dict, width:int, height:int)->str:
    ill_coords = get_element_coordinates(illustration)
    cap_bot, angle, distance = work_with_bottom(ill_coords, text_blocks[bottom_flag], width, height)
    caption = ""
    return caption

def process_page_alto(alto_path:str):
    illustration_flag = 'Illustration'
    text_block_flag = 'TextBlock'
    illustrations = find_interesting_bboxes_in_alto(alto_path, illustration_flag)
    text_blocks = find_interesting_bboxes_in_alto(alto_path, text_block_flag)

    width, height = find_page_width_height(alto_path)

    for illustration in illustrations:
        text_blocks_dict = match_bboxes_to_illustrations(illustration, text_blocks)
        caption = find_caption(illustration, text_blocks_dict, width, height)

    return




def utility(page_url:str, dir_for_alto:str):
    '''Receives page url, calls functions, which find img bboxes and captions.'''
    alto_url = convert_page_url_to_alto_url(page_url)
    alto_path = os.path.join(dir_for_alto, "page_alto.xml")
    ut.download_alto_file(alto_url, alto_path)
    process_page_alto(alto_path)
    return


url = "https://gallica.bnf.fr/services/ajax/pagination/page/SINGLE/ark:/12148/bpt6k9740716w/f17.item"
utility(url, '.')
