from dateutil.parser import parse
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys, os
import pandas as pd
sys.path.insert(1, os.path.join(sys.path[0], '../..'))
import utils

cwd = os.path.abspath(os.path.dirname(sys.argv[0]))
root_path = os.path.abspath('')
infofile = root_path+"/input/infofile.txt"
logfile = cwd+"/logfile.txt"

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")
chrome_driver = root_path+"/chromedriver"

browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)

header = ["page", "claim", "claim_label", "tags", "source_list", "claim_source_domain", "claim_source_url", "date"]
categories = ["","category/Culture","category/Viral", "category/Apple","category/Business%252FTech","category/World","category/US"]
dataset = pd.read_csv(cwd+'/emergent.csv', sep='\t')
base_url = "http://www.emergent.info/"

for idx,cat in enumerate(categories):
	url = base_url+cat
	browser.get(url)
	data = browser.page_source
	soup = bs(data,"html.parser")
	articles = soup.find("ul",{"class":"articles"}).findAll("article",{"class":"article"})
	for article in articles:
		head = article.find("header")
		footer = article.find("footer")
		page = base_url[:-1]+head.find("h2").find("a")['href']
		if page not in dataset.page.unique():
			claim = head.find("h2").find("a").text
			claim_label = head.find("div",{"class":"truthiness"}).find("span").text.lower()
			tags = [e.text for e in footer.findAll("a")]
			if head.find("span",{"class":"article-source"}) is None:
				continue
			(claim_source_url,claim_source_domain) = utils.fix_source(page,[head.find("span",{"class":"article-source"}).find("a")])
			date = head.find("time")['datetime'].split("T")[0]
			date = parse(date).strftime('%Y/%m/%d')
			if claim_source_url is not None:
				entry = [page,claim,claim_label,tags,[claim_source_url],claim_source_domain,claim_source_url,date]
				dataset.loc[page] = entry
			else:
				utils.inputLogError(page,"NO SOURCE:","emergent")

		

dataset.to_csv(cwd+"/emergent.csv", sep='\t', header=header, index=False)

browser.quit()