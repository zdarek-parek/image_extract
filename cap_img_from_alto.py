import requests
import xml.etree.ElementTree as ET
import numpy as np
# import cv2
import utility_funcs as ut
import os
import new_caption as nc

# def highlight_bbox(img:np.ndarray, bbox:list[int])->np.ndarray:
#     cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[0]+bbox[2], bbox[1]+bbox[3]), (0, 0, 255), 2)
#     return img

# def highlight_bboxes(img_path:str, ill_bboxes:list[list[int]]):
#     img = cv2.imread(img_path)
#     for bbox in ill_bboxes:
#         img = highlight_bbox(img, bbox)
#     cv2.imwrite("bboxes_fr.jpeg", img)
#     return


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

def get_second_identifier(page_url:str)->str:
    split_url = page_url.split('/')
    if len(split_url) > 3:
        return split_url[-3]
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


def get_element_width_height(e:ET.Element)->list[int]:
    ''' Returns width and height of the element.'''
    attr = e.attrib
    if ('WIDTH' in attr.keys()) and ('HEIGHT' in attr.keys()):
        return [int(attr['WIDTH']), int(attr['HEIGHT'])]
    return [0, 0]

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


def parse_string(string:ET.Element)->str:
    content = get_element_content(string)
    # coords = get_element_coordinates(string)
    return content

def parse_text_line(text_line:ET.Element)->list[str]:
    string_flag = 'String'
    text = []
    for child in text_line:
        if child.tag.endswith(string_flag):
            text.append(parse_string(child))
    return text

def parse_text_block(text_block:ET.Element)->list[str]:
    text_line_flag = 'TextLine'
    text = []
    for child in text_block:
        if child.tag.endswith(text_line_flag):
            text += parse_text_line(child)
    return text

def parse_illustration(illustartion:ET.Element)->list[int]:
    '''Returns coordinates of an illustration in page.'''
    coords = get_element_coordinates(illustartion)
    return coords


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
        if child.tag.endswith(bbox_flag):
            blocks.append(child)
    return blocks

def parse_page(page:ET.Element, bbox_flag:str)->list[ET.Element]:
    # page_attr = page.attrib
    # w, h = get_element_width_height(page)
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
    x1, y1, x2, y2 = ill_bbox[0], ill_bbox[1], ill_bbox[0]+ill_bbox[2], ill_bbox[1]+ill_bbox[3] # image in page
    x3, y3, x4, y4 = text_bbox[0], text_bbox[1], text_bbox[0]+text_bbox[2], text_bbox[1]+text_bbox[3] # text block
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
    x1, y1, x2, y2 = ill_coords[0], ill_coords[1], ill_coords[0]+ill_coords[2], ill_coords[1]+ill_coords[3] # image in page
    x3, y3, x4, y4 = bbox[0], bbox[1], bbox[0]+bbox[2], bbox[1]+bbox[3] # text block

    if y1 < y4 and y2 > y3: return True
    return False

def is_possible_to_contain_caption_up_down(ill_coords:list[int], bbox:list[int]):
    x1, y1, x2, y2 = ill_coords[0], ill_coords[1], ill_coords[0]+ill_coords[2], ill_coords[1]+ill_coords[3] # image in page
    x3, y3, x4, y4 = bbox[0], bbox[1], bbox[0]+bbox[2], bbox[1]+bbox[3] # text block

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
                    return get_element_width_height(child2)
            
    return [0, 0]

def get_highres_img_url(url:str, alto_path:str)->str:
    # "https://gallica.bnf.fr/services/ajax/pagination/page/SINGLE/ark:/12148/bpt6k9740716w/f17.item"
    # "https://gallica.bnf.fr/iiif/ark:/12148/bpt6k9740716w/f17/full/3956,5328/0/native.jpg"

    w, h = find_page_width_height(alto_path)
    id1 = get_identifier(url)
    id2 = get_second_identifier(url)
    page_num = get_page_num(url)
    highres_url = "https://gallica.bnf.fr/iiif/ark:/%s/%s/f%s/full/%d,%d/0/native.jpg" % (id2, id1, page_num, w, h)
    return highres_url


def get_small_blocks(blocks:list[ET.Element], limit:int, criterion_index:int)->list[ET.Element]:
    small_close_text_blocks = []
    for block in blocks: # get rid of close blocks which are two times higher than the closest block
        if get_element_coordinates(block)[criterion_index]/2 < limit:
            small_close_text_blocks.append(block)
        else:
            break
    return small_close_text_blocks

def analyze_read_cap_blocks(blocks:list[ET.Element])->list[str]:
    if len(blocks) == 0:
        return []
    else:
        text = read_caption(blocks)
        if len(text) > 30:
            closest_text = read_caption([blocks[0]])
            return closest_text
        else:
            return text
    

def get_element_bbox_square(e:ET.Element)->int:
    w, h = get_element_width_height(e)
    return w*h

def read_caption(text_blocks:list[ET.Element])->list[str]:
    '''Returns text, which is in the given list of elements.'''
    blocks = []
    for text_block in text_blocks:
        blocks += parse_text_block(text_block)
    return blocks

def find_nearest_text_bottom(ill_coords, text_blocks:list[ET.Element], width_orig:int, height_orig:int)->tuple:
    sorted_blocks = sorted(text_blocks, key = lambda b: get_element_coordinates(b)[1]) # 1. sort according to the distance from the image

    closest_text_block = sorted_blocks[0]
    x0, y0, w0, h0 = get_element_coordinates(closest_text_block)
    dist_between_img_and_text_block = y0 - (ill_coords[1]+ill_coords[3])
    res = [closest_text_block]
    for i in range(1, len(sorted_blocks)): # 2. discard too small, too big text blocks or far blocks
        x, y, w, h = get_element_coordinates(sorted_blocks[i])
        if (y - (y0+h0)) < height_orig/100:
            if (1_000 <= get_element_bbox_square(sorted_blocks[i]) <= ill_coords[2]*ill_coords[3]/2):
                res.append(sorted_blocks[i])

    if len(res) == 0: return [], -1
    elif len(res) == 1:
        if get_element_width_height(closest_text_block)[1] < ill_coords[3]/2: # already checked if the size is appropriate (2.), now need to make sure that it is nit too high
            # dist_between_img_and_text_block = y0 - (ill_coords[1]+ill_coords[3])
            res_words = analyze_read_cap_blocks(res)
            return res_words, dist_between_img_and_text_block
        return [], -1
    else: # 3. find text blocks that are close to the closest text block to the image
        small_close_text_blocks = get_small_blocks(res, h0, 3)
        result = analyze_read_cap_blocks(small_close_text_blocks)
        if (0 < len(result) <= 30):
            return result, dist_between_img_and_text_block
        else: return [], -1

def work_with_bottom(ill_coords:list[int], text_blocks:list[ET.Element], width:int, height:int)->tuple:
    if len(text_blocks) > 0:
        caption_words, distance = find_nearest_text_bottom(ill_coords, text_blocks, width, height)
        if len(caption_words) > 0:
            caption = " ".join(caption_words)
            if len(caption) != 0:
                return caption, distance, 0
    return "", -1, 0

def find_nearest_text_top(ill_coords, text_blocks:list[ET.Element], width_orig:int, height_orig:int)->tuple:
    sorted_blocks = sorted(text_blocks, key = lambda b: get_element_coordinates(b)[1]+get_element_coordinates(b)[3], reverse=True)
    
    closest_text_block = sorted_blocks[0]
    x0, y0, w0, h0 = get_element_coordinates(closest_text_block)
    dist_between_img_and_text_block = (ill_coords[1]+ill_coords[3]) - (y0+h0)
    res = [closest_text_block]
    for i in range(1, len(sorted_blocks)): # 2. discard too small, too big text blocks or far blocks
        x, y, w, h = get_element_coordinates(sorted_blocks[i])
        if (y0 - (y+h)) < height_orig/100:
            if (1_000 <= get_element_bbox_square(sorted_blocks[i]) <= ill_coords[2]*ill_coords[3]/2):
                res.append(sorted_blocks[i])
    
    if len(res) == 0: return [], -1
    elif len(res) == 1:
        if get_element_width_height(closest_text_block)[1] < ill_coords[3]/2: # already checked if the size is appropriate (2.), now need to make sure that it is nit too high
            res_words = analyze_read_cap_blocks(res)
            return res_words, dist_between_img_and_text_block
        return [], -1
    else:
        small_close_text_blocks = get_small_blocks(res, h0, 3)
        result = analyze_read_cap_blocks(small_close_text_blocks)
        if (0 < len(result) <= 30):
            return result, dist_between_img_and_text_block
        else: return [], -1

def work_with_top(ill_coords:list[int], text_blocks:list[ET.Element], width:int, height:int)->tuple:
    if len(text_blocks) > 0:
        caption_words, distance = find_nearest_text_top(ill_coords, text_blocks, width, height)
        if len(caption_words) > 0:
            caption = " ".join(caption_words)
            if len(caption) != 0:
                return caption, distance, 0
    return "", -1, 0

def find_nearest_text_right(ill_coords, text_blocks:list[ET.Element], width_orig:int, height_orig:int)->tuple:
    sorted_blocks = sorted(text_blocks, key = lambda b: get_element_coordinates(b)[0])
    
    closest_text_block = sorted_blocks[0]
    x0, y0, w0, h0 = get_element_coordinates(closest_text_block)
    dist_between_img_and_text_block = x0 - (ill_coords[0]+ill_coords[2])
    res = [closest_text_block]
    for i in range(1, len(sorted_blocks)): # 2. discard too small, too big text blocks or far blocks
        x, y, w, h = get_element_coordinates(sorted_blocks[i])
        if (x - (x0+w0)) < width_orig/100:
            if (1_000 <= get_element_bbox_square(sorted_blocks[i]) <= ill_coords[2]*ill_coords[3]/2):
                res.append(sorted_blocks[i])

   
    if len(res) == 0: return [], -1
    elif len(res) == 1:
        if get_element_width_height(closest_text_block)[0] < ill_coords[2]/2: # already checked if the size is appropriate (2.), now need to make sure that it is not too wide
            res_words = analyze_read_cap_blocks(res)
            return res_words, dist_between_img_and_text_block
        return [], -1
    else:
        small_close_text_blocks = get_small_blocks(res, w0, 2)
        result = analyze_read_cap_blocks(small_close_text_blocks)
        if (0 < len(result) <= 30):
            return result, dist_between_img_and_text_block
        else: return [], -1

def work_with_right(ill_coords:list[int], text_blocks:list[ET.Element], width:int, height:int)->tuple:
    if len(text_blocks) > 0:
        caption_words, distance = find_nearest_text_right(ill_coords, text_blocks, width, height)
        if len(caption_words) > 0:
            caption = " ".join(caption_words)
            if len(caption) != 0:
                return caption, distance, 0
    return "", -1, 0

def find_nearest_text_left(ill_coords, text_blocks:list[ET.Element], width_orig:int, height_orig:int)->tuple:
    sorted_blocks = sorted(text_blocks, key = lambda b: get_element_coordinates(b)[0] + get_element_coordinates(b)[2], reverse=True)
    
    closest_text_block = sorted_blocks[0]
    x0, y0, w0, h0 = get_element_coordinates(closest_text_block)
    dist_between_img_and_text_block = ill_coords[0] - (x0+w0)
    res = [closest_text_block]
    for i in range(1, len(sorted_blocks)): # 2. discard too small, too big text blocks or far blocks
        x, y, w, h = get_element_coordinates(sorted_blocks[i])
        if ((x+w) - x0) < width_orig/100:
            if (1_000 <= get_element_bbox_square(sorted_blocks[i]) <= ill_coords[2]*ill_coords[3]/2):
                res.append(sorted_blocks[i])

    
    if len(res) == 0: return [], -1
    elif len(res) == 1:
        if get_element_width_height(closest_text_block)[0] < ill_coords[2]/2: # already checked if the size is appropriate (2.), now need to make sure that it is not too wide
            res_words = analyze_read_cap_blocks(res)
            return res_words, dist_between_img_and_text_block
        return [], -1
    else:
        small_close_text_blocks = get_small_blocks(res, w0, 2)
        result = analyze_read_cap_blocks(small_close_text_blocks)
        if (0 < len(result) <= 30):
            return result, dist_between_img_and_text_block
        else: return [], -1

def work_with_left(ill_coords:list[int], text_blocks:list[ET.Element], width:int, height:int)->tuple:
    if len(text_blocks) > 0:
        caption_words, distance = find_nearest_text_left(ill_coords, text_blocks, width, height)
        if len(caption_words) > 0:
            caption = " ".join(caption_words)
            if len(caption) != 0:
                return caption, distance, 0
    return "", -1, 0

def find_caption(illustration:ET.Element, text_blocks:dict, width:int, height:int)->tuple:
    ill_coords = get_element_coordinates(illustration)

    caps_dists = []
    cap_b, distance_b, angle_b = work_with_bottom(ill_coords, text_blocks[bottom_flag], width, height)
    caps_dists.append((cap_b, distance_b))
    cap_t, distance_t, angle_t = work_with_top(ill_coords, text_blocks[up_flag], width, height)
    caps_dists.append((cap_t, distance_t))
    cap_r, distance_r, angle_r = work_with_right(ill_coords, text_blocks[right_flag], width, height)
    caps_dists.append((cap_r, distance_r))
    cap_l, distance_l, angle_l = work_with_left(ill_coords, text_blocks[left_flag], width, height)
    caps_dists.append((cap_l, distance_l))
    caption = nc.fix_multiple_captions(caps_dists)
    return caption, 0

def process_page_alto(alto_path:str)->tuple:
    illustration_flag = 'Illustration'
    text_block_flag = 'TextBlock'
    illustrations = find_interesting_bboxes_in_alto(alto_path, illustration_flag)
    text_blocks = find_interesting_bboxes_in_alto(alto_path, text_block_flag)

    width, height = find_page_width_height(alto_path)
    imgs = []
    caps = []
    angles = []
    for illustration in illustrations:
        text_blocks_dict = match_bboxes_to_illustrations(illustration, text_blocks)
        caption, angle = find_caption(illustration, text_blocks_dict, width, height)
        caps.append(caption)
        angles.append(angle)
        x, y, w, h = get_element_coordinates(illustration)
        imgs.append([x, y, x+w, y+h])

    return imgs, caps, angles, width, height


def delete_alto_file(path:str):
    if os.path.exists(path):
        os.remove(path)
    return

def utility(page_url:str, dir_for_alto:str)->tuple:
    '''Receives page url, calls functions, which find img bboxes and captions.'''
    alto_url = convert_page_url_to_alto_url(page_url)
    alto_path = os.path.join(dir_for_alto, "page_alto.xml")

    ut.download_alto_file(alto_url, alto_path)
    highres_img_url = get_highres_img_url(page_url, alto_path)
    imgs, caps, angles, w, h = process_page_alto(alto_path)
    delete_alto_file(alto_path)
    return imgs, caps, angles, w, h, highres_img_url


# url = "https://gallica.bnf.fr/services/ajax/pagination/page/SINGLE/ark:/12148/bpt6k9740716w/f17.item"
# url = "https://gallica.bnf.fr/ark:/12148/bpt6k9740716w/f119.item"
# utility(url, '.')
