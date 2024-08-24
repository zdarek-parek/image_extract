import os
import utility_funcs as ut
import csv
import cap_img_from_alto_fr as ci_alto
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
    if month.isnumeric(): return month
    month = ut.delete_diacritics(month.lower())
    months = {'janvier':'01', 'fevrier':'02', 'mars':'03', 
              'avril':'04', 'mai':'05', 'juin':'06', 
              'juillet':'07', 'aout':'08', 'septembre':'09', 
              'octobre':'10', 'novembre':'11', 'decembre':'12'}

    return months[month]

def format_publication_date(date:str)->str:
    '''Converts publication date 1 avril 1900 to database format 1900-04-01-1900-12-31,
        also converts publication date 1897-04-01 to 1897-04-01-1897-04-01'''
    
    split_date = []
    if '-' in date:
        split_date = date.split('-')
    elif ' ' in date:
        split_date = date.split(' ')
    else:
        split_date = [date]

    if len(split_date[0]) == 4: # firts is a year
        split_date.reverse()
    
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

def extract_metadata(info:dict)->list[str]:
    '''
    Uses set of keys to extract important metadata.
    '''

    meta_dict = {'Titre':'', 'Auteur':'', 'Editeur':'', 'Date d\'edition':'', 'Contributeur':'', 'Langue':''}
    info_list = info['contenu'][0]['contenu']
    for info in info_list:
        key = ut.delete_diacritics(info['key']['contenu'])
        if key in meta_dict.keys():
            meta_dict[key] = info['value']['contenu']
    meta = list(meta_dict.values())
    return meta


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


def process_page_image(img_path:str, img_url:str, writer:csv.DictWriter, info:list[str], page_index:str, res_dir:str, journal_n:str, p_writer:csv.DictWriter):
    journal_name, author, publisher, publication_date, contributor, l, issue_number, year = info
    publication_date = format_publication_date(publication_date) # database format
    image_name_prefix = "%s_%s_%s_" % (ut.format_string(journal_n), ut.format_string(publication_date), ut.format_string(issue_number))
    lang = language_formatting_for_text_detection(l)
    infos = [journal_name, publication_date, "", issue_number]

    # boxes, p_h, p_w = getim.util(img_path, lang)
    boxes, captions, degrees_to_rotate, p_w, p_h, highres_img_url = ci_alto.utility(img_url, res_dir)
    success = ut.save_img(highres_img_url, img_path)
    if len(boxes) > 0: #page contains images
        percentages = vrs.get_versions(page_index, image_name_prefix, img_path, boxes, res_dir, degrees_to_rotate)
        for j in range(len(boxes)):
            entity = ut.create_entity(page_index, "", j+1, captions[j], percentages[j], boxes[j], infos, 
                                    image_name_prefix, p_w, p_h, ut.language_formatting(lang), 
                                    highres_img_url, author, publisher, contributor)
            # 3 last are 'author', 'publisher', 'contributor'
            writer.writerow(entity)
    page_entity = ut.create_page_entity(page_index, "", infos, p_w, p_h, ut.language_formatting(lang),
                                        highres_img_url, author, publisher, contributor)
    p_writer.writerow(page_entity)
    return success

def work_with_page(page_item:dict, root_dir:str, writer:csv.DictWriter, info:list[str], journal_name:str, issue_temp_fol:str, res_dir:str, p_writer:csv.DictWriter):
    page_index = page_item['contenu']
    page_url = page_item['url']
    img_url = convert_url_to_img_url(page_url, root_dir)

    page_index = page_index + '_' + ci_alto.get_page_num(img_url)
    img_name =  ut.format_string(page_index)+".jpeg"
    img_path = os.path.join(issue_temp_fol, img_name)

    success = process_page_image(img_path, img_url, writer, info, page_index, res_dir, journal_name, p_writer)
    return success

def work_with_pages(url:str, root_dir:str, info:list[str], journal_name:str, year:str, issue_month:str, issue_num:str, issue_temp_fol:str)->bool:
    pages_json_url = convert_to_json(url)
    pages_json_file = os.path.join(root_dir, 'pages.json') 
    response_ok = ut.read_api_url(pages_json_url, pages_json_file)
    if not response_ok: return
    content = ut.load_json(pages_json_file)
    pages = content['fragment']['contenu']

    issue_month = issue_month + '_' + issue_num
    issue_dir_name = "%s_%s_%s" % (journal_name, year, issue_month)#for the page images
    issue_dir_name = ut.format_string(issue_dir_name)
    issue_temp_fol = os.path.join(issue_temp_fol, issue_dir_name)
    ut.create_dir(issue_temp_fol)

    res_dir, csvfile_path, csvfile_pages_path = ut.create_result_dirs_and_files(issue_dir_name)
    writer, file = ut.create_csv_writer(csvfile_path, ut.IMG_HEAD_CSV)
    p_writer, p_file = ut.create_csv_writer(csvfile_pages_path, ut.PAGE_HEAD_CSV)
    infos = info + [issue_month, year]
    for i in range(len(pages)):
        success = work_with_page(pages[i], root_dir, writer, infos, journal_name, issue_temp_fol, res_dir, p_writer)
        if not success:
            file.close()
            os.remove(csvfile_path)
            p_file.close()
            os.remove(csvfile_pages_path)
            os.rmdir(os.path.join(res_dir, "big_original"))
            os.rmdir(res_dir)
            os.rmdir(issue_temp_fol)
            return False
    return True

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

def work_with_issue(issue:dict, root_dir:str, journal_name:str, year:str, issue_month:str, issue_num:str, issue_temp_fol:str)->bool:
    issue_url = issue['url']
    issue_url = work_with_issue_xml(issue_url, root_dir)
    if len(issue_url) > 0:
        issue_json_url = convert_to_json(issue_url)
        issue_json_file = os.path.join(root_dir, 'issue.json') 
        response_ok = ut.read_api_url(issue_json_url, issue_json_file)
        if not response_ok: return

        content = ut.load_json(issue_json_file)
        info = content['InformationsModel']
        info = extract_metadata(info)
        pages_url = content['PageAViewerFragment']['contenu']['PaginationViewerModel']['url']

        success = work_with_pages(pages_url, root_dir, info, journal_name, year, issue_month, issue_num, issue_temp_fol)
        return success
    else:
        pre_issue_url = issue['url']
        pre_issue_json_url = convert_to_json(pre_issue_url)
        pre_issue_json_file = os.path.join(root_dir, 'pre_issue.json') 
        response_ok = ut.read_api_url(pre_issue_json_url, pre_issue_json_file)
        if not response_ok: return
        content = ut.load_json(pre_issue_json_file)

        issue_parts = content['PeriodicalPageFragment']['contenu']['SearchResultsFragment']['contenu']['ResultsFragment']['contenu']

        for i in range(len(issue_parts)):
            if issue_parts[i]['active'] == True:
                issue_title = issue_parts[i]['title']
                issue_num_num = '_'+str(i)
                success = work_with_issue(issue_title, root_dir, journal_name, year, issue_month, issue_num+issue_num_num, issue_temp_fol)
        return success


def work_with_month(month:dict, root_dir:str, journal_name:str, year:str, temp_fol:str, issue_start:str)->str:
    issue_month = convert_month_to_number(month['parameters']['nom'])
    content_rows = month['contenu']
    
    processed_items_counter = 0
    issue_count_in_one_month = 0
    for row in content_rows:
        content_row = row['contenu']

        for cr in content_row:
            if cr['active']:
                issue_count_in_one_month += 1
                if processed_items_counter >= issue_start: # ability to tell the program where to start
                    success = work_with_issue(cr, root_dir, journal_name, year, issue_month, str(issue_count_in_one_month), temp_fol)
                processed_items_counter += 1
    return True

def work_with_one_month_issue(issue:dict, root_dir:str, journal_name:str, year:str, year_temp_fol:str)->bool:
    issue_month = issue['PageAViewerFragment']['contenu']['IssuePaginationFragment']['currentPage']['contenu']
    issue_month = convert_month_to_issue_number(issue_month)
    issue_num = "1"
    # issue_temp_fol = os.path.join(year_temp_fol, ut.format_string(issue_month))
    # ut.create_dir(issue_temp_fol)
    info = issue['InformationsModel']
    info = extract_metadata(info)
    pages_url = issue['PageAViewerFragment']['contenu']['PaginationViewerModel']['url']
    
    success = work_with_pages(pages_url, root_dir, info, journal_name, year, issue_month, issue_num, year_temp_fol)
    return success

def work_with_volume(volume:dict, root_dir:str, journal_name:str, temp_fol:str, month_start:int, issue_start:int):
    year = volume['description']

    year_temp_fol = os.path.join(temp_fol, ut.format_string(year))
    ut.create_dir(year_temp_fol)

    volume_url = volume['url']
    volume_json_url = convert_to_json(volume_url)
    volume_json_file = os.path.join(root_dir, 'volume.json') 
    response_ok = ut.read_api_url(volume_json_url, volume_json_file)
    if not response_ok: return

    content = ut.load_json(volume_json_file)
    if 'PeriodicalPageFragment' in content.keys():
        months = content['PeriodicalPageFragment']['contenu']['CalendarPeriodicalFragment']['contenu']['CalendarGrid']['contenu']
        for i in range(month_start, len(months)):
            success = work_with_month(months[i], root_dir, journal_name, year, year_temp_fol, issue_start)
            issue_start = 0
    elif 'PageAViewerFragment' in content.keys():
        success = work_with_one_month_issue(content, root_dir, journal_name, year, year_temp_fol)

    return

def work_with_volumes(volumes:dict, root_dir:str,  journal_name:str, temp_fol:str, volume_start:int, month_start:int, issue_start:int):
    rows_of_volumes = volumes['contenu']['CalendarGrid']['contenu'] #list of rows
    processed_volumes_counter = 0
    for row in rows_of_volumes:
        row_content = row['contenu']
        
        for rc in row_content:
            if len(rc['url'])>0:
                if processed_volumes_counter >= volume_start: # ability to tell the program where to start
                    work_with_volume(rc, root_dir, journal_name, temp_fol, month_start, issue_start)
                    month_start = 0 # next volume will be processed from the beginning (first month, first issue)
                    issue_start = 0
                processed_volumes_counter +=1
    return
 
def shorten_journal_name(long_name:str)->str:
    split_name = long_name.split(' - ')
    if len(split_name) > 1: return split_name[0]
    split_name_gap = long_name.split(' ')
    short_name = ' '.join(split_name_gap[:5])
    return short_name

def work_with_journal(url:str, root_dir:str, volume_start:int, month_start:int, issue_start:int):
    journal_json_file = os.path.join(root_dir, 'journal.json')
    response_ok = ut.read_api_url(url, journal_json_file)
    if not response_ok: return
    content = ut.load_json(journal_json_file)
    
    if 'PeriodicalPageFragment' in content.keys():
        journal_name = content['PeriodicalPageFragment']['contenu']['PageModel']['parameters']['title']
        journal_name = shorten_journal_name(journal_name)
        volumes = content['PeriodicalPageFragment']['contenu']['CalendarPeriodicalFragment']

        journal_folder_temp = os.path.join(root_dir, ut.format_string(journal_name))
        ut.create_dir(journal_folder_temp)
        work_with_volumes(volumes, root_dir, journal_name, journal_folder_temp, volume_start, month_start, issue_start)
    elif 'PageAViewerFragment' in content.keys():
        info = content['InformationsModel']
        info = extract_metadata(info)

        journal_name = shorten_journal_name(info[0])
        journal_folder_temp = os.path.join(root_dir, ut.format_string(journal_name))
        ut.create_dir(journal_folder_temp)

        year = info[3]
        year_temp_fol = os.path.join(journal_folder_temp, ut.format_string(year))
        ut.create_dir(year_temp_fol)
        success = work_with_one_month_issue(content, root_dir, journal_name, year, year_temp_fol)
    
    return

def strip_url_from_request(url:str)->str:
    split_url = url.split('?')
    return split_url[0]

def get_rid_of_bad_ending(url:str)->str:
    flag_to_delete = ".planchecontact"
    if url.endswith(flag_to_delete):
        return url[:len(url)-len(flag_to_delete)]
    return url


def utility(url:str, volume_start:int, month_start:int, issue_start:str)->None:
    url = strip_url_from_request(url)
    url = get_rid_of_bad_ending(url)
    api_url = convert_to_json(url)
    if api_url == None:
        print("invalid url:", url)
        return
    out_dir = 'temp' #here will be json files
    ut.create_dir(out_dir)
    result_out_dir = 'result'
    ut.create_dir(result_out_dir)
    work_with_journal(api_url, out_dir, volume_start, month_start, issue_start)
    ut.delete_json_files(out_dir)
    return

