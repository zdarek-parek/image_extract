import os
import utility_funcs as ut



def convert_to_json(url:str)->str:
    conversion_part = "/info.json"
    json_url = url + conversion_part
    return json_url

def convert_url_to_img_url(url:str, root_dir:str)->str:
    '''
    This function downloads json file describing one page, 
    finds image link,
    coverts it to a link where the image is,
    returns it.
    '''
    page_json_url = convert_to_json(url)
    page_json_file = os.path.join(root_dir, 'page.json') 
    response_ok = ut.read_api_url(page_json_url, page_json_file)
    if not response_ok: return
    content = ut.load_json(page_json_file)

    img_url = content['fragment']['parameters']['externalPageArkUrl']

    img_label = 'highres'
    img_url = img_url+img_label
    return img_url

def create_img_name(journal_name:str, volume:str, issue:str)->str:
    name = journal_name+"_"+volume+"_"+issue
    name = ut.format_string(name)
    return

def process_image():
    return

def work_with_page(page_item:dict, root_dir:str, info:list[str], journal_name:str, year:str, issue_month:str, issue_temp_fol:str, res_dir:str, index:int):
    page_index = page_item['contenu']
    if page_index == "NP": page_index = page_index+"_"+str(index)
    page_url = page_item['url']
    img_url = convert_url_to_img_url(page_url, root_dir)

    img_name = create_img_name(info[0], year, issue_month) +"_"+ ut.format_string(page_index)+".jpeg"
    img_path = os.path.join(issue_temp_fol, img_name)
    success = ut.save_img(img_url, img_path)
    if success:
        process_image(img_path, lang, writer, info, page_index, res_dir)
        # print("processed image", img_name)
    return success

    return


def work_with_pages(url:str, root_dir:str, info:list[str], journal_name:str, year:str, issue_month:str, issue_temp_fol:str, res_dir:str):
    pages_json_url = convert_to_json(url)
    pages_json_file = os.path.join(root_dir, 'pages.json') 
    response_ok = ut.read_api_url(pages_json_url, pages_json_file)
    if not response_ok: return
    content = ut.load_json(pages_json_file)
    pages = content['fragment']['contenu']
    for i in range(len(pages)):
    # for page in pages:
        work_with_page(pages[i], root_dir, info, journal_name, year, issue_month, issue_temp_fol, res_dir, i)
    return

'''
def extract_metadata_not_valid(info:dict)->dict:
    #won't be used because json file contains 
    #  french labels with diactritics (prone to errors), instead indexation will be 
    # used assuming single pattern for every json file of an issue
    meta = {}
    info_list = info['contenu'][0]['contenu']
    web_meta_labels = ["Title", "Author", "Publisher", "Publication date", "Contributor", "Language"]
    # 0, 1, 2, 3, 4, 9
    for info_item in info_list:
        k = info_item['key']['contenu']
        if k in web_meta_labels:
            meta[k] = info_item['value']['contenu']
    return meta
'''


def extract_metadata(info:dict)->list[str]:
    info_list = info['contenu'][0]['contenu']
    # 0, 1, 2, 3, 4, 9
    title = info_list[0]['value']['contenu']
    author = info_list[1]['value']['contenu']
    publisher = info_list[2]['value']['contenu']
    publication_date = info_list[4]['value']['contenu']
    lang = info_list[9]['value']['contenu']
    meta = [title, author, publisher, publication_date, lang]
    return meta

def work_with_issue_xml(xml_url:str, root_dir:str)->str:
    '''Extracts an url, which contains issue data from xml file'''

    issue_xml_file = os.path.join(root_dir, 'issue.xml')
    response_ok = ut.read_api_url(xml_url, issue_xml_file)
    if not response_ok: return
    file = open(issue_xml_file,  encoding="utf8", mode='r')
    content = file.read()
    words = content.split(' ')
    content_label = "content=\""
    url_label = "https://"
    content_url = ""
    for word in words:
        if word.startswith(content_label+url_label):
            content_url = word
            break
    url = content_url.split("\"")[1] if len(content_url.split("\"")) > 2 else ""
    return url

def work_with_issue(issue:dict, root_dir:str, journal_name:str, year:str, issue_month:str, issue_temp_fol:str, res_dir:str):
    issue_url = issue['url']
    issue_url = work_with_issue_xml(issue_url, root_dir)
    issue_json_url = convert_to_json(issue_url)
    issue_json_file = os.path.join(root_dir, 'issue.json') 
    response_ok = ut.read_api_url(issue_json_url, issue_json_file)
    if not response_ok: return

    content = ut.load_json(issue_json_file)
    info = content['InformationsModel']
    info = extract_metadata(info)
    pages_url = content['PageAViewerFragment']['contenu']['PaginationViewerModel']['url']

    work_with_pages(pages_url, root_dir, info, journal_name, year, issue_month, issue_temp_fol, res_dir)
    return

def work_with_month(month:dict, root_dir:str, journal_name:str, year:str, temp_fol:str, res_dir:str):
    issue_month = month['parameters']['nom']
    content_rows = month['contenu']
    
    for row in content_rows:
        content_row = row['contenu']

        for cr in content_row:
            if cr['active']:
                issue_temp_fol = os.path.join(temp_fol, ut.format_str(issue_month))
                # issue_res_fol = os.path.join(res_dir, ut.format_str(issue_month))
                ut.create_dir(issue_temp_fol)
                # ut.create_dir(issue_res_fol)

                work_with_issue(cr, root_dir, journal_name, year, issue_month, issue_temp_fol, res_dir)

    return

def work_with_volume(volume:dict, root_dir:str, journal_name:str, temp_fol:str, res_dir:str):
    year = volume['description']

    year_temp_fol = os.path.join(temp_fol, ut.format_str(year))
    # year_res_fol = os.path.join(res_fol, ut.format_str(year))
    ut.create_dir(year_temp_fol)
    # ut.create_dir(year_res_fol)

    volume_url = volume['url']
    volume_json_url = convert_to_json(volume_url)
    volume_json_file = os.path.join(root_dir, 'volume.json') 
    response_ok = ut.read_api_url(volume_json_url, volume_json_file)
    if not response_ok: return

    content = ut.load_json(volume_json_file)
    monthes = content['PeriodicalPageFragment']['contenu']['CalendarPeriodicalFragment']['contenu']['CalendarGrid']['contenu']
    for m in monthes:
        work_with_month(m, root_dir, journal_name, year, year_temp_fol, res_dir)
    return


def work_with_volumes(volumes:dict, root_dir:str,  journal_name:str, temp_fol:str, res_dir:str):
    rows_of_volumes = volumes['contenu']['CalendarGrid']['contenu'] #list of rows
    # c = 0
    for row in rows_of_volumes:
        row_content = row['contenu']
        for rc in row_content:
            if len(rc['url'])>0:
                work_with_volume(rc, root_dir, journal_name, temp_fol, res_dir)
                # c+=1

    # print(c)
    return
 
def work_with_journal(url:str, root_dir:str, res_dir:str):
    journal_json_file = os.path.join(root_dir, 'journal.json')
    response_ok = ut.read_api_url(url, journal_json_file)
    if not response_ok: return
    content = ut.load_json(journal_json_file)
    
    journal_name = content['PeriodicalPageFragment']['contenu']['PageModel']['parameters']['title']
    volumes = content['PeriodicalPageFragment']['contenu']['CalendarPeriodicalFragment']

    journal_folder_temp = os.path.join(root_dir, ut.format_str(journal_name))
    # journal_folder_res = os.path.join(res_dir, ut.format_str(journal_name))
    ut.create_dir(journal_folder_temp)
    # ut.create_dir(journal_folder_res)
    work_with_volumes(volumes, root_dir, journal_name, journal_folder_temp, res_dir)
    return

def utility(url:str)->None:
    api_url = convert_to_json(url)
    if api_url == None:
        print("invalid url:", url)
        return
    out_dir = 'temp' #here will be json files
    ut.create_dir(out_dir)
    result_out_dir = 'result'
    ut.create_dir(result_out_dir)
    work_with_journal(api_url, out_dir, result_out_dir)
    # ut.delete_json_files(out_dir)
    return


url = "https://gallica.bnf.fr/ark:/12148/cb32857192h/date.r=revue+de+l%27art+ancien+et+moderne.langFR"
utility(url)