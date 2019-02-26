from dateutil.parser import parse
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys, os, requests
import pandas as pd
sys.path.insert(1, os.path.join(sys.path[0], '../..'))
import utils
import eventlet
eventlet.monkey_patch()

cwd = os.path.abspath(os.path.dirname(sys.argv[0]))
parent_path = os.path.abspath('')
infofile = parent_path+"/infofile.txt"
logfile = cwd+"/logfile.txt"

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")
chrome_driver = parent_path+"/chromedriver"

browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)

header = ["page", "claim", "claim_label", "tags", "source_list", "claim_source_domain", "claim_source_url", "date"]
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
				with eventlet.Timeout(35):
					print(pagenumber, page)
					claim = article.find("p",{"class":"statement__text"}).find("a").text.replace('\r', '').replace('\n', '')
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
				sources = [e.a for e in sidebar.div.findAll("p") if (e.a is not None) and (e.a.has_attr('href'))]
				source_list = source_list = utils.fix_origin_list(sources)
			except:
				utils.inputLogError(page,"REACT ERROR:","politifact")
				continue

			claim_source_url,claim_source_domain = utils.fix_source(page,sources,meta=meta)
			date = parse(sidebar.p.text.split(":")[1].split(" at ")[0]).strftime('%Y/%m/%d')

			if ((claim_source_url is not None) and (len(source_list) > 0)):
				# CREATE ENTRY
				entry = [page,claim,claim_label,tags, source_list, claim_source_domain,claim_source_url,date]
				dataset.loc[page] = entry
			else:
				utils.inputLogError(page,"NO SOURCE:","politifact")
				

		dataset.to_csv(cwd+"/politifact.csv", sep='\t', header=header, index=False)

	utils.update_last_saved_page(num_pages-pagenumber,"politifact")

browser.quit()
