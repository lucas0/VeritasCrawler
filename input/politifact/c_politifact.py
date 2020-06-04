import re
import eventlet
eventlet.monkey_patch()
from dateutil.parser import parse
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys, os, requests
import pandas as pd
sys.path.insert(1, os.path.join(sys.path[0], '../..'))
import utils

cwd = os.path.abspath(__file__+'/..')
crawling_path = os.path.abspath(cwd+'/../..')
infofile = crawling_path+"/infofile.txt"
logfile = cwd+"/logfile.txt"
content_path = crawling_path+'/eatiht/datasets'

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--no-sandbox")
chrome_driver = crawling_path+"/chromedriver"

browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)

header = ["page", "claim", "claim_label", "tags", "origin_list", "origin_domain", "origin_url", "date", "author"]
dataset = pd.read_csv(cwd+'/politifact.csv', sep='\t')
base_url = "http://www.politifact.com"

num_pages = utils.get_num_of_pages("politifact")
last_saved_page = utils.get_last_saved_page("politifact")

for pagenumber in reversed(range(1,num_pages-last_saved_page)):
        page = "/truth-o-meter/statements/?page="+str(pagenumber)
        req = requests.get(base_url+page)
        soup = bs(req.text,"html.parser")
        articles = soup.find("section",{"class":"scoretable"}).findAll("div",{"class":"scoretable__item"})
        for article in articles:
                page = base_url+article.find("p",{"class":"statement__text"}).find("a")['href']
                if page not in dataset.page.unique():
                        try:
                                with eventlet.Timeout(15):
                                        print(pagenumber, page)
                                        claim = article.find("p",{"class":"statement__text"}).find("a").text.replace('\r', '').replace('\n', '')
                                        claim = re.sub(r"^[\t\s\"\']*(.*)[\t\s\n\r\"\']*$", r'\1', claim)
                                        who = article.find("div", {"class":"statement__source"}).find("a").text.replace('\r', '').replace('\n', '')
                                        claim_label = article.find("div",{"class":"meter"}).find("img")['alt'].lower()
                                        title = bs(requests.get(page).text,"html.parser").title.text
                                        if title == "PolitiFact | Ooooh, not good. 404 error":
                                                continue

                                        browser.get(page)
                                        soup = bs(browser.page_source,"html.parser")
                        except:
                                continue

                        try:
                                meta = soup.find("p",{"class":"statement__meta"}).text
                                data = browser.page_source
                                sidebar = bs(data,"html.parser").find("div",{"class":"widget__content"})
                                tags = [e.text for e in sidebar.findAll("p")[3].findAll("a")]
                                origins = [e.a for e in sidebar.div.findAll("p") if (e.a is not None) and (e.a.has_attr('href'))]
                                origin_list = utils.cleanOrigins(origins)
                        except Exception as e:
                                utils.inputLogError(page,"REACT ERROR:","politifact")
                                continue


                        date = parse(sidebar.p.text.split(":")[1].split(" at ")[0]).strftime('%Y/%m/%d')
                        author = sidebar.findAll("p")[1].text.split(":")[1].strip()

                        if (len(origin_list) > 0):
                                origin_url = origin_list[0]
                                origin_domain = utils.getDomain(origin_url)
                                # CREATE ENTRY
                                entry = [page, claim, claim_label, tags, origin_list, origin_domain, origin_url, date, author]
                                dataset.loc[page] = entry
                        else:
                                utils.inputLogError(page,"NO ORIGIN:","politifact")


                dataset.to_csv(cwd+"/politifact.csv", sep='\t', header=header, index=False)

        utils.update_last_saved_page(num_pages-pagenumber,"politifact")

browser.quit()
