import os
import utility_funcs as ut
import cap_img_from_alto as ci_alto_fr
import cv2
import numpy as np
import xml.etree.ElementTree as ET
import urllib

def highlight_bbox(img:np.ndarray, bbox:list[int], coords:list[int])->np.ndarray:
    h, w = coords[1] - img.shape[0], coords[0] - img.shape[1]
    # bbox[0] -= w
    # bbox[1] -= h
    cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[0]+bbox[2], bbox[1]+bbox[3]), (0, 0, 255), 2)
    return img

def highlight_bboxes(img_path:str, ill_bboxes:list[ET.Element], coords:list[int]):
    img = cv2.imread(img_path)
    print(img.shape)
    for bbox in ill_bboxes:
        print(bbox.tag)
        img = highlight_bbox(img, ci_alto_fr.get_element_coordinates(bbox), coords)
    cv2.imwrite("bboxes_cz.jpeg", img)
    return
#2035, 2702

def find_print_space_width_height(alto_path:str)->list[int]:
    tree = ET.parse(alto_path)
    root = tree.getroot()
    layout_flag = "Layout"

    blocks = []
    for child in root:
        if child.tag.endswith(layout_flag):
            page_flag = 'Page'
            for child2 in child:
                if child2.tag.endswith(page_flag):
                    print_space_flag = 'PrintSpace'
                    for child3 in child2:
                        if child3.tag.endswith(print_space_flag):
                            return ci_alto_fr.get_element_width_height(child3)
            
    return [0, 0]

def find_margins(layout:ET.Element):
    margins = []
    page_content = []
    for child in layout:
        page_flag = 'Page'
        for child2 in child:
            if child2.tag.endswith(page_flag):
                for child3 in child2:
                    page_content.append(child3)


    return

def work_with_alto_file(alto_path:str, url:str):
    # tree = ET.parse(alto_path)
    # root = tree.getroot()
    # layout_flag = "Layout"
    

    # blocks = []
    # for child in root:
    #     if child.tag.endswith(layout_flag):
    #         layout = child
    #         find_margins(layout)
    # tbs = ci_alto_fr.find_interesting_bboxes_in_alto(alto_path, 'Illustration')
    tbs = ci_alto_fr.find_interesting_bboxes_in_alto(alto_path, 'TextBlock')

    coords = ci_alto_fr.find_page_width_height(alto_path)
    if coords[0] == 0:
        coords = find_print_space_width_height(alto_path)

    # ut.save_img(url, 'img_cz.jpeg')
    highlight_bboxes('img_cz.jpeg', tbs, coords)

    return


def convert_page_url_to_alto_url(page_url:str)->str:
    split_page_url = page_url.split('/')
    uuid = [d for d in split_page_url if d.startswith('uuid:')]
    if len(uuid) != 1:
        return ""
    uuid_ = uuid[0]

    alto_url = "https://api.kramerius.mzk.cz/search/api/client/v7.0/items/%s/ocr/alto" % (uuid_)
    return alto_url

def utility(page_url:str, dir_for_alto:str)->tuple:
    alto_url = convert_page_url_to_alto_url(page_url)
    alto_path = os.path.join(dir_for_alto, "page_alto.xml")

    # ut.download_alto_file(alto_url, alto_path)
    work_with_alto_file(alto_path, url)

    return

# url = "https://api.kramerius.mzk.cz/search/iiif/uuid:1f9750ef-435e-11dd-b505-00145e5790ea/full/full/0/default.jpg"
# url = "https://api.kramerius.mzk.cz/search/iiif/uuid:1f9729da-435e-11dd-b505-00145e5790ea/full/full/0/default.jpg"
# url = "https://api.kramerius.mzk.cz/search/iiif/uuid:34f1d3f5-935d-11e0-bdd7-0050569d679d/full/full/0/default.jpg"
url = "https://api.kramerius.mzk.cz/search/iiif/uuid:1f9729da-435e-11dd-b505-00145e5790ea/full/1500,1907/0/default.jpg"
utility(url, "temp")

# PrintSpace HEIGHT="2538" WIDTH="1870" - img 1847, 2521
# <PrintSpace HEIGHT="2499" WIDTH="1834" 1834, 2499
# PrintSpace HEIGHT="2539" WIDTH="1872" 1847, 2521
# <PrintSpace HEIGHT="2502" WIDTH="1837" 2502, 1837
# <PrintSpace HEIGHT="2546" WIDTH="1881" 2521, 1847