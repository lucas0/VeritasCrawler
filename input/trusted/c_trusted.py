from dateutil.parser import parse
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys, os
import pandas as pd

cwd = os.path.abspath(os.path.dirname(sys.argv[0]))
root_path = os.path.abspath('')
infofile = root_path+"/input/infofile.txt"
logfile = cwd+"/logfile.txt"

chrome_options = Options()
chrome_options.add_argument("--headless")
#chrome_options.add_argument("--window-size=1920x1080")
chrome_driver = root_path+"/chromedriver"

header = ["page", "claim", "claim_label", "tags", "origin_list", "date"]
categories = ["","category/Culture","category/Viral", "category/Apple","category/Business%252FTech","category/World","category/US"]
dataset = pd.read_csv(cwd+'/emergent.csv', sep='\t')
base_url = "http://www.emergent.info/"

total_articles = 0
for idx,cat in enumerate(categories):
        print("+++ "+cat+" +++")
        url = base_url+cat
        browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        browser.get(url)
        soup = bs(browser.page_source,"html.parser")
        browser.quit()
        articles = soup.find("ul",{"class":"articles"}).findAll("article",{"class":"article"})
        for page_num,article in enumerate(articles):
                total_articles += 1
                dataset = pd.read_csv(cwd+'/emergent.csv', sep='\t')
                head = article.find("header")
                footer = article.find("footer")
                page = base_url[:-1]+head.find("h2").find("a")['href']
                if page not in dataset.page.unique():
                        print(page)
                        claim = head.find("h2").find("a").text
                        claim_label = head.find("div",{"class":"truthiness"}).find("span").text.lower()
                        tags = [e.text for e in footer.findAll("a")]
                        #if head.find("span",{"class":"article-source"}) is None:
                        #       continue
                        browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
                        browser.get(page)
                        soup = bs(browser.page_source, "html.parser")
                        browser.quit()

                        articles_ul = soup.body.main.find("div", class_= ["page-claim-body"]).find("ul", {"class":"articles"})
                        if articles_ul is None:
                            articles.append(article)
                            continue
                        rel_articles = articles_ul.findAll("h4", {"class":"article-list-title"})

                        origins = []
                        for rel_article in rel_articles:
                            stance = rel_article.find("span",{"class":"indicator"})['class']
                            if "indicator-for" in stance:
                                origin_elem = rel_article.find("a")
                                origins.append(origin_elem['href'])

                        print("Number of origins:", len(origins))
                        date = head.find("time")['datetime'].split("T")[0]
                        date = parse(date).strftime('%Y/%m/%d')
                        if len(origins) > 0:
                                entry = [page,claim,claim_label,tags,origins,date]
                                dataset.loc[page] = entry

                dataset.to_csv(cwd+"/emergent.csv", sep='\t', header=header, index=False)

print("Total Articles: ",total_articles)
browser.quit()
