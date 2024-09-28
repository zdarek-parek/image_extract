import os
import cv2
import math
# from PIL import Image
import xml.etree.ElementTree as ET

import utility_funcs as ut
import alto_parser as ap
import image_mining_big as im

# def resize_image(img_path:str):
#     img = Image.open(img_path)
#     big = img.resize((3938, 6155))
#     big.save("big.png")
#     return

# def draw_bboxes(bboxes:list[list[int]]):
#     img = cv2.imread(r"C:\Users\dasha\Desktop\py_projects\big.png")
#     for bbox in bboxes:

#         cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[0]+bbox[2], bbox[1]+bbox[3]), (0, 0, 255),  4)
    
#     cv2.imwrite(r"C:\Users\dasha\Desktop\py_projects\rec_big.jpg", img) 
#     return

# def find_text_lines(bbox, lines, ocr_dims, phys_dims):
#     for l in bbox:
#         x, y, w, h = ap.get_element_coordinates(l)
#         x2, y2, w2, h2 = adjust_img_bbox([x, y, w, h], ocr_dims, phys_dims)
#         lines.append([x2, y2, w2, h2])
#     return lines

# def highlight_bboxes(bboxes, ocr_dims:list[int], phys_dims:list[int]):
#     res = []
#     for bbox in bboxes:
#         if len(list(bbox)) == 0: 
#             x, y, w, h = ap.get_element_coordinates(bbox)
#             if h > 100 and w > 100:
#                 # x2, y2, w2, h2 = adjust_img_bbox([x, y, w, h], ocr_dims, phys_dims)
#                 # res.append([x2, y2, w2, h2])
#                 res.append([x, y, w, h])
#         # find_text_lines(bbox, res, ocr_dims, phys_dims)
    
#     draw_bboxes(res)
#     return



def adjust_img_bbox(bbox:list[int], width_coeff:float, height_coeff:float)->list[int]:

    x = math.floor(bbox[0]*width_coeff)
    y = math.floor(bbox[1]*height_coeff) 
    w = math.ceil(bbox[2]*width_coeff)
    h = math.ceil(bbox[3]*height_coeff)

    return [x, y, w, h]

def adjust_bboxes(bboxes:list[list[int]], ocr_page_dims:list[int], phys_page_dims:list[int])->list[list[int]]:
    width_coeff = ocr_page_dims[0] / phys_page_dims[0] # phys to ocr
    height_coeff = ocr_page_dims[1] / phys_page_dims[1]

    # width_coeff = phys_page_dims[0] / ocr_page_dims[0] # ocr to phys
    # height_coeff = phys_page_dims[1] / ocr_page_dims[1]

    adjusted_bboxes = []
    for bbox in bboxes:
        new_bbox = adjust_img_bbox(bbox, width_coeff, height_coeff)
        adjusted_bboxes.append(new_bbox)

    return adjusted_bboxes

def change_format(bboxes:list[list[int]])->list[list[int]]:
    res_bboxes = []

    for bbox in bboxes:
        x1, y1, x2, y2 = bbox
        res_bboxes.append([x1, y1, x2-x1, y2-y1])
    return res_bboxes

def find_potential_img_blocks(blocks:list[ET.Element], width:int, height:int)->list[list[int]]:
    empty_blocks = []
    for block in blocks:
        if len(list(block)) == 0: 
            _, _, w, h = ap.get_element_coordinates(block)
            if h > int(height*0.05) and w > int(width*0.05):
                empty_blocks.append(ap.get_element_coordinates(block))

    return empty_blocks

def process_page_alto(alto_path:str, ocr_dims:list[int], phys_dims:list[int], img_path:str)->tuple:
    
    width, height = ap.find_page_width_height(alto_path)
    phys_w, phys_h = phys_dims

    text_blocks = ap.find_interesting_bboxes_in_alto(alto_path, ap.TEXT_BLOCK_FLAG)
    # empty_blocks = find_potential_img_blocks(text_blocks, width, height)#empty_boxes
    # img_boxes = adjust_bboxes(adjusted_bboxes, ocr_dims, phys_dims) #adjusted_boxes

    # if len(empty_blocks) == 0: return [], [], [], phys_w, phys_h

    img_boxes, _, _ = im.util(img_path, 'deu')
    img_boxes = change_format(img_boxes)
    adjusted_bboxes = adjust_bboxes(img_boxes, ocr_dims, phys_dims)
    
    imgs = []
    caps = []
    angles = []
    for i in range(len(adjusted_bboxes)):
        if ap.is_big_enough(adjusted_bboxes[i], width, height):
            text_blocks_dict = ap.match_bboxes_to_illustrations(adjusted_bboxes[i], text_blocks)
            caption, angle = ap.find_caption(adjusted_bboxes[i], text_blocks_dict, width, height)
            caps.append(caption)
            angles.append(angle)
            x, y, w, h = img_boxes[i]
            imgs.append([x, y, x+w, y+h])
    imgs, caps, angles = ap.delete_inscribed_bboxes(imgs, caps, angles)
    return imgs, caps, angles, phys_w, phys_h

def utility(page_image_url:str, dir_for_alto:str, alto_link:str, img_path:str):
    alto_path = os.path.join(dir_for_alto, "page_alto.xml")

    ut.download_alto_file(alto_link, alto_path)
    highres_img_url = page_image_url
    ocr_page_dims = ap.find_page_width_height(alto_path)
    
    success = ut.save_img(highres_img_url, img_path)
    phys_page_dims = ut.get_img_dims(img_path)
    imgs, caps, angles, w, h = process_page_alto(alto_path, ocr_page_dims, phys_page_dims, img_path)
    ut.delete_file(alto_path)
    return imgs, caps, angles, w, h, highres_img_url

# utility('https://digi.ub.uni-heidelberg.de/iiif/3/dkd1899_1900%3A237.jpg/full/max/0/default.jpg', 
#         '.', 
#         "https://digi.ub.uni-heidelberg.de/diglitData4/alto_cache/dkd1899_1900/237.xml", 
#         'try.png')

