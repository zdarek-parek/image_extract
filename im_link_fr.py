import os
import utility_funcs as ut
import csv
import image_mining_big as getim
import new_caption as cap
import versions as vrs


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

    img_label = '.highres'
    img_url = img_url+img_label
    return img_url

def create_img_name(journal_name:str, volume:str, issue:str)->str:
    name = journal_name+"_"+volume+"_"+issue
    name = ut.format_string(name)
    return name

def language_formatting_for_text_detection(lang:str)->str: #TODO: find more languages in french
    lang = ut.delete_diacritics(lang)
    if lang == "français":return "fra"
    return "fra" # default, if it is not possible to recognize language in json file

def convert_month_to_number(month:str)->str:
    month = ut.delete_diacritics(month.lower())
    months = {'janvier':1, 'fevrier':2, 'mars':3, 
              'avril':4, 'mai':5, 'juin':6, 
              'juillet':7, 'aout':8, 'septembre':9, 
              'octobre':10, 'novembre':11, 'decembre':12}

    return months[month]

def format_publication_date(date:str)->str:
    '''Converts publication date 1 avril 1900 to database format 1900-04-01-1900-12-31'''
    split_date = date.split(' ')
    pub_date = ""
    if len(split_date) == 3: #day, month, year
        day = split_date[0]
        month = convert_month_to_number(split_date[1])
        year = split_date[2]
        pub_date = "%s-%s-%s-%s-%s-%s" % (year, month, day, year, month, day)
    elif len(split_date) == 2:
        month = convert_month_to_number(split_date[0])
        year = split_date[1]
        pub_date = "%s-%s-%s-%s-%s-%s" % (year, month, "01", year, month, "31")
    elif len(split_date) == 1:
        year = split_date[0]
        pub_date = "%s-%s-%s-%s-%s-%s" % (year, "01", "01", year, "12", "31")
    return pub_date

def convert_month_to_issue_number(pub_date:str)->str:
    '''Extracts issue number as a month from 01 juillet 1909 ->  7'''
    split_date = pub_date.split(' ')
    issue = ""
    if len(split_date) == 3:
        issue = convert_month_to_number(split_date[1])
    elif len(split_date) == 2:
        issue = convert_month_to_number(split_date[0])
    return issue

def process_image(img_path:str, img_url:str, lang:str, writer:csv.DictWriter, info:list[str], page_index:str, res_dir:str):
    journal_name, author, publisher, publication_date, l, issue_number, year = info
    year = format_publication_date(publication_date) # database format
    image_name_prefix = "%s_%s_%s_" % (journal_name, publication_date, issue_number)
    image_name_prefix = ut.format_string(image_name_prefix)
    lang = language_formatting_for_text_detection(lang)
    infos = [journal_name, publication_date, "", issue_number]

    boxes, p_h, p_w = getim.util(img_path, lang)
    if len(boxes) > 0: #page contains images
        captions, degrees_to_rotate = cap.util(img_path, boxes, lang) 
        percentages = vrs.get_versions(page_index, image_name_prefix, img_path, boxes, res_dir, degrees_to_rotate)
        for j in range(len(boxes)):
            entity = ut.create_entity(page_index, j+1, captions[j], percentages[j], boxes[j], infos, 
                                    image_name_prefix, p_w, p_h, ut.language_formatting(lang), 
                                    img_url, author, publisher)
            # three last are 'author', 'publisher', 'publication date'
            writer.writerow(entity)
    return

def work_with_page(page_item:dict, root_dir:str, writer:csv.DictWriter, info:list[str],  year:str, issue_month:str, issue_temp_fol:str, res_dir:str, index:int):
    page_index = page_item['contenu']
    if page_index == "NP": page_index = page_index+"_"+str(index)
    page_url = page_item['url']
    img_url = convert_url_to_img_url(page_url, root_dir)

    img_name = create_img_name(info[0], year, issue_month) +"_"+ ut.format_string(page_index)+".jpeg"
    img_path = os.path.join(issue_temp_fol, img_name)
    success = ut.save_img(img_url, img_path)
   
    if success:
        process_image(img_path, img_url, info[4], writer, info, page_index, res_dir)
        # print("processed image", img_name)
    return success

def create_result_dirs_and_files(issue_dir_name:str): # dir where extracted reproduction will be
    result_root = "result"
    result_dir = os.path.join(result_root, issue_dir_name)#extracted reproductions
    ut.create_dir(result_dir)
    result_dir_big = os.path.join(result_dir, 'big_original')
    ut.create_dir(result_dir_big)
    csvfile = issue_dir_name+'_data.csv'
    csvfile_path = os.path.join(result_root, csvfile)
    return result_dir, csvfile_path


def work_with_pages(url:str, root_dir:str, info:list[str], journal_name:str, year:str, issue_month:str, issue_temp_fol:str)->bool:
    pages_json_url = convert_to_json(url)
    pages_json_file = os.path.join(root_dir, 'pages.json') 
    response_ok = ut.read_api_url(pages_json_url, pages_json_file)
    if not response_ok: return
    content = ut.load_json(pages_json_file)
    pages = content['fragment']['contenu']

    issue_dir_name = "%s_%s_%s" % (info[0], year, issue_month)#for the page images
    issue_dir_name = ut.format_string(issue_dir_name)
    issue_temp_fol = os.path.join(issue_temp_fol, issue_dir_name)
    ut.create_dir(issue_temp_fol)

    res_dir, csvfile_path = create_result_dirs_and_files(issue_dir_name)
    writer, file = ut.create_csv_writer(csvfile_path)
    infos = info + [issue_month, year]
    for i in range(len(pages)):
    # for page in pages:
        success = work_with_page(pages[i], root_dir, writer, infos, year, issue_month, issue_temp_fol, res_dir, i)
        if not success:
            file.close()
            os.remove(csvfile_path)
            os.rmdir(os.path.join(res_dir, "big_original"))
            os.rmdir(res_dir)
            os.rmdir(issue_temp_fol)
            return False
    return True

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

def work_with_issue(issue:dict, root_dir:str, journal_name:str, year:str, issue_month:str, issue_temp_fol:str)->bool:
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

    success = work_with_pages(pages_url, root_dir, info, journal_name, year, issue_month, issue_temp_fol)
    return success

def work_with_month(month:dict, root_dir:str, journal_name:str, year:str, temp_fol:str, issue_start:str):
    issue_month = convert_month_to_number(month['parameters']['nom'])
    content_rows = month['contenu']
    
    processed_items_counter =0
    for row in content_rows:
        content_row = row['contenu']

        for cr in content_row:
            if cr['active']:
                if processed_items_counter >= issue_start: # ability to tell the program where to start
                    # issue_temp_fol = os.path.join(temp_fol, ut.format_string(issue_month))
                    # issue_res_fol = os.path.join(res_dir, ut.format_str(issue_month))
                    # ut.create_dir(issue_temp_fol)
                    # ut.create_dir(issue_res_fol)

                    success = work_with_issue(cr, root_dir, journal_name, year, issue_month, temp_fol)
                    if not success:
                        os.rmdir(temp_fol)
                        return False

    return True

def work_with_one_month_issue(issue:dict, root_dir:str, journal_name:str, year:str, year_temp_fol:str)->str:
    issue_month = issue['PageAViewerFragment']['contenu']['IssuePaginationFragment']['currentPage']['contenu']
    issue_month = convert_month_to_issue_number(issue_month)
    # issue_temp_fol = os.path.join(year_temp_fol, ut.format_string(issue_month))
    # ut.create_dir(issue_temp_fol)
    info = issue['InformationsModel']
    info = extract_metadata(info)
    pages_url = issue['PageAViewerFragment']['contenu']['PaginationViewerModel']['url']

    success = work_with_pages(pages_url, root_dir, info, journal_name, year, issue_month, year_temp_fol)
    return success

def work_with_volume(volume:dict, root_dir:str, journal_name:str, temp_fol:str, issue_start:int):
    year = volume['description']

    year_temp_fol = os.path.join(temp_fol, ut.format_string(year))
    # year_res_fol = os.path.join(res_fol, ut.format_str(year))
    ut.create_dir(year_temp_fol)
    # ut.create_dir(year_res_fol)

    volume_url = volume['url']
    volume_json_url = convert_to_json(volume_url)
    volume_json_file = os.path.join(root_dir, 'volume.json') 
    response_ok = ut.read_api_url(volume_json_url, volume_json_file)
    if not response_ok: return

    content = ut.load_json(volume_json_file)
    if 'PeriodicalPageFragment' in content.keys():
        monthes = content['PeriodicalPageFragment']['contenu']['CalendarPeriodicalFragment']['contenu']['CalendarGrid']['contenu']
        for m in monthes:
            success = work_with_month(m, root_dir, journal_name, year, year_temp_fol, issue_start)
    elif 'PageAViewerFragment' in content.keys():
        success = work_with_one_month_issue(content, root_dir, journal_name, year, year_temp_fol,)

    return


def work_with_volumes(volumes:dict, root_dir:str,  journal_name:str, temp_fol:str, volume_start:int, issue_start:int):
    rows_of_volumes = volumes['contenu']['CalendarGrid']['contenu'] #list of rows
    processed_volumes_counter = 0
    for row in rows_of_volumes:
        row_content = row['contenu']
        
        for rc in row_content:
            if len(rc['url'])>0:
                if processed_volumes_counter >= volume_start: # ability to tell the program where to start
                    work_with_volume(rc, root_dir, journal_name, temp_fol, issue_start)
                processed_volumes_counter +=1

    # print(c)
    return
 
def work_with_journal(url:str, root_dir:str, volume_start:int, issue_start:int):
    journal_json_file = os.path.join(root_dir, 'journal.json')
    response_ok = ut.read_api_url(url, journal_json_file)
    if not response_ok: return
    content = ut.load_json(journal_json_file)
    
    journal_name = content['PeriodicalPageFragment']['contenu']['PageModel']['parameters']['title']
    volumes = content['PeriodicalPageFragment']['contenu']['CalendarPeriodicalFragment']

    journal_folder_temp = os.path.join(root_dir, ut.format_string(journal_name))
    # journal_folder_res = os.path.join(res_dir, ut.format_str(journal_name))
    ut.create_dir(journal_folder_temp)
    # ut.create_dir(journal_folder_res)
    work_with_volumes(volumes, root_dir, journal_name, journal_folder_temp, volume_start, issue_start)
    return

def utility(url:str, volume_start:int, issue_start:str)->None:
    api_url = convert_to_json(url)
    if api_url == None:
        print("invalid url:", url)
        return
    out_dir = 'temp' #here will be json files
    ut.create_dir(out_dir)
    result_out_dir = 'result'
    ut.create_dir(result_out_dir)
    work_with_journal(api_url, out_dir, volume_start, issue_start)
    # ut.delete_json_files(out_dir)
    return


# url = "https://gallica.bnf.fr/ark:/12148/cb34446843c/date.r="
# utility(url, 0, 0)

# TODO: fix month - make it an issue, year format yyyy-mm-dd-yyyy-mm-dd everywhere except for pdf, ocr, error monthes