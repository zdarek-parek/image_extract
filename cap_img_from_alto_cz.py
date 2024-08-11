import os
import utility_funcs as ut
import alto_parser as ap
import numpy as np
import math

'''
def highlight_bbox(img:np.ndarray, bbox:list[int], coords:list[int])->np.ndarray:
    h, w, _ = img.shape
    wc, hc = coords
    c1 = w/wc
    c2 = h/hc
    print(bbox)
    bbox[0] = math.floor(bbox[0] * c1)
    bbox[2] = math.floor(bbox[2] * c1)
    bbox[1] = math.floor(bbox[1]*c2)
    bbox[3] = math.floor(bbox[3]*c2)
    print(c1, c2)
    print(bbox)
    cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[0]+bbox[2], bbox[1]+bbox[3]), (0, 0, 255), 2)
    return img

def highlight_bboxes(img_path:str, ill_bboxes:list[ET.Element], coords:list[int]):
    img = cv2.imread(img_path)
    print(img.shape)
    for bbox in ill_bboxes:
        print(bbox.tag)
        img = highlight_bbox(img, ap.get_element_coordinates(bbox), coords)
    cv2.imwrite("bboxes_cz.jpeg", img)
    return

'''


def get_uuid(url:str)->str:
    '''Finds the first uuid in the given url'''
    split_page_url = url.split('/')
    uuid = [d for d in split_page_url if d.startswith('uuid:')]
    uuid_ = ""
    if len(uuid) != 0:
        uuid_ = uuid[0]
    return uuid_

def convert_img_url_to_best_img_url(url:str, dims:list[int])->str:
    uuid = get_uuid(url)
    ocr_img_url = "https://api.kramerius.mzk.cz/search/iiif/%s/full/%d,%d/0/default.jpg" % (uuid, dims[0], dims[1])

    if ut.is_img_request_ok(ocr_img_url):
        return ocr_img_url

    max_url = "https://api.kramerius.mzk.cz/search/iiif/%s/full/max/0/default.jpg" % (uuid)
    return max_url

def adjust_img_bbox(bbox:list[int], ocr_page_dims:list[int], phys_page_dims:list[int])->list[int]:
    width_coeff = phys_page_dims[0] / ocr_page_dims[0]
    height_coeff = phys_page_dims[1] / ocr_page_dims[1]
    bbox[0] = math.floor(bbox[0]*width_coeff)
    bbox[1] = math.floor(bbox[1]*height_coeff)
    bbox[2] = math.ceil(bbox[2]*width_coeff)
    bbox[3] = math.ceil(bbox[3]*height_coeff)
    return bbox

def process_page_alto(alto_path:str, ocr_page_dims:list[int], phys_page_dims:list[int]):
    illustrations = ap.find_interesting_bboxes_in_alto(alto_path, ap.ILLUSTRATION_FLAG)
    text_blocks = ap.find_interesting_bboxes_in_alto(alto_path, ap.TEXT_BLOCK_FLAG)

    width, height = ocr_page_dims
    imgs = []
    caps = []
    angles = []
    for illustration in illustrations:
        if ap.is_big_enough(illustration, width, height):
            text_blocks_dict = ap.match_bboxes_to_illustrations(illustration, text_blocks)
            caption, angle = ap.find_caption(illustration, text_blocks_dict, width, height)
            caps.append(caption)
            angles.append(angle)
            x, y, w, h = ap.get_element_coordinates(illustration)
            ad_x, ad_y, ad_w, ad_h = adjust_img_bbox([x, y, w, h], ocr_page_dims, phys_page_dims)
            imgs.append([ad_x, ad_y, ad_x+ad_w, ad_y+ad_h])
    imgs, caps, angles = ap.delete_inscribed_bboxes(imgs, caps, angles)
    return imgs, caps, angles, width, height


def convert_page_url_to_alto_url(page_url:str)->str:
    split_page_url = page_url.split('/')
    uuid = [d for d in split_page_url if d.startswith('uuid:')]
    if len(uuid) != 1:
        return ""
    uuid_ = uuid[0]

    alto_url = "https://api.kramerius.mzk.cz/search/api/client/v7.0/items/%s/ocr/alto" % (uuid_)
    return alto_url

def utility(page_url:str, dir_for_alto:str, img_path:str)->tuple:
    alto_url = convert_page_url_to_alto_url(page_url)
    alto_path = os.path.join(dir_for_alto, "page_alto.xml")
    ut.download_alto_file(alto_url, alto_path)

    ocr_page_dims = ap.find_page_width_height(alto_path)
    ocr_img_url = convert_img_url_to_best_img_url(page_url, ocr_page_dims)
    success = ut.save_img(ocr_img_url, img_path)
    phys_page_dims = ut.get_img_dims(img_path)

    imgs, caps, angles, w, h = process_page_alto(alto_path, ocr_page_dims, phys_page_dims)
    ut.delete_file(alto_path)
    return imgs, caps, angles, w, h, ocr_img_url, success

# url = "https://api.kramerius.mzk.cz/search/iiif/uuid:1f979f1d-435e-11dd-b505-00145e5790ea/full/full/0/default.jpg"
# utility(url, "temp")