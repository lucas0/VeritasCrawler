nonBreakSpace = u'\xa0'
import eventlet
eventlet.monkey_patch()
from dateutil.parser import parse
from bs4 import BeautifulSoup as bs
import os, sys
import requests
import pandas as pd
sys.path.insert(1, os.path.join(sys.path[0], '../..'))
import utils

cwd = os.path.abspath(os.path.dirname(sys.argv[0]))
parent_path = os.path.abspath('')

header = ["page", "claim", "claim_label", "tags", "origin_list", "origin_domain", "origin_url", "date", "author"]
baselink = "https://www.factcheck.org/fake-news/page/"
dataset = pd.read_csv(cwd+'/factcheck.csv', sep='\t')

#given an bs.html tag, returns a list of all <a> elements on it
def getOrigins(content):
        origins = []
        f_origin = 0
        p_list = (i for i in content.contents[1:-1] if isinstance(i,Tag))

        for p in p_list:
                text = p.get_text()
                if (f_origin == 1):
                        origin_elem = p.find("a")
                        if origin_elem != None:
                                origins.append(origin_elem)
                if "sources" == text.lower():
                        f_origin = 1
        return origins

num_pages = utils.get_num_of_pages("factcheck")
last_saved_page = utils.get_last_saved_page("factcheck")

for pagenumber in reversed(range(1,num_pages-last_saved_page)):
        url = baselink+str(pagenumber)+"/"
        print(url)
        req = requests.get(url)

        data = req.text
        soup = bs(data,"html.parser")
        p = soup.findAll("article")
        for i in p:
                claim = i.find("h3", {"class" : "entry-title"}).find("a").text
                page = i.find("h3", {"class" : "entry-title"}).find("a")['href']
                if page not in dataset.page.unique():
                        print("\n\nP> {} T> {} ".format(pagenumber,claim))
                        verdict = utils.getVerdict(i.find("div", {"class" : "entry-content"}).text.replace(nonBreakSpace, ''))

                        req = requests.get(page)
                        data = req.text
                        soup = bs(data,"html.parser")
                        date = soup.find("time", {"class": "entry-date"}).text
                        date = parse(date).strftime('%Y/%m/%d')
                        content = soup.find("div", {"class":"entry-content"})
                        author = soup.find("p", {"class":"byline"}).text.split("By ")[1].strip()
                        footer = soup.find("footer")
                        origins = getOrigins(content)
                        origin_list = utils.cleanOrigins(origins)

                        class_list = ["issue","location","person"]
                        tag_list = []
                        for e in footer.findAll("li",class_=class_list):
                                tag_list += e.findAll("a")
                        tags = [e.text for e in tag_list]

                        if (len(origin_list) > 0):
                                origin_url = origin_list[0]
                                origin_domain = utils.getDomain(origin_url)
                                # CREATE ENTRY
                                entry = [page,claim,verdict,tags,origins_list,origin_domain,origin_url,date, author]
                                dataset.loc[page] = entry
                        else:
                                utils.inputLogError(page,"NO ORIGIN:","factcheck")


        # SAVE DATASET
        dataset.to_csv(cwd+"/factcheck.csv", sep='\t', header=header, index=False)

        utils.update_last_saved_page(num_pages-pagenumber,"factcheck")
