import os
import utility_funcs as ut


def convert_to_json(url:str)->str:
    conversion_part = "/info.json"
    json_url = url + conversion_part
    return json_url




def work_with_volume(volume:dict, root_dir:str):
    year = volume['description']
    volume_url = volume['url']
    volume_json_url = convert_to_json(volume_url)
    volume_json_file = os.path.join(root_dir, 'volume.json') 
    # response_ok = ut.read_api_url(volume_json_url, volume_json_file)
    # if not response_ok: return
    content = ut.load_json(volume_json_file)
    monthes = content['PeriodicalPageFragment']['contenu']['CalendarPeriodicalFragment']['contenu']['CalendarGrid']['contenu']
    for m in monthes:
        print(m.keys())
    return


def work_with_volumes(volumes:dict, root_dir:str):
    rows_of_volumes = volumes['contenu']['CalendarGrid']['contenu'] #list of rows
    c = 0
    for row in rows_of_volumes:
        row_content = row['contenu']
        for rc in row_content:
            if len(rc['url'])>0:
                work_with_volume(rc, root_dir)
                c+=1

    print(c)
    return

def work_with_journal(url:str, root_dir:str):
    journal_json_file = os.path.join(root_dir, 'journal.json')
    # response_ok = ut.read_api_url(url, journal_json_file)
    # if not response_ok: return
    content = ut.load_json(journal_json_file)
    
    journal_name = content['PeriodicalPageFragment']['contenu']['PageModel']['parameters']['title']
    volumes = content['PeriodicalPageFragment']['contenu']['CalendarPeriodicalFragment']

    work_with_volumes(volumes, root_dir)
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
    work_with_journal(api_url, out_dir)
    # ut.delete_json_files(out_dir)
    return


url = "https://gallica.bnf.fr/ark:/12148/cb32857192h/date.r=revue+de+l%27art+ancien+et+moderne.langFR"
utility(url)