#-*- coding: utf-8 -*-
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

cwd = os.path.abspath(os.path.dirname(sys.argv[0]))
parent_path = os.path.abspath('')
infofile = parent_path+"/infofile.txt"
logfile = cwd+"/logfile.txt"
content_path = parent_path+'/eatiht/datasets'

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")
chrome_driver = parent_path+"/chromedriver"

browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)

header = ["page", "claim", "claim_label", "tags", "source_list", "claim_source_domain", "claim_source_url", "date"]
header_e = ["page","claim","claim_label","tags","claim_source_domain","claim_source_url","date_check","source_body","date_fake"]

base_urls = ["https://www.truthorfiction.com/category/fact-checks","https://www.truthorfiction.com"]

for base_url in base_urls:
	num_pages = utils.get_num_of_pages(base_url, False)
	last_saved_page = utils.get_last_saved_page(base_url)
	subpage = base_urls.index(base_url)
	for pagenumber in reversed(range(1,num_pages-last_saved_page+1)):
		page = "/page/"+str(pagenumber)
		print(base_url+page)
		req = requests.get(base_url+page)
		soup = bs(req.text,"html.parser")
		if subpage == 0:
			articles = soup.findAll("div",{"class":"col-md-12"})[1]
		else:
			articles = soup.find("div",{"class":"col-md-6"})
		articles = articles.findAll("div",{"class":"tt-post"})
		for article in articles:
			dataset = pd.read_csv(cwd+'/tof.csv', sep='\t')
			content_df = pd.read_csv(content_path+'/tof_e_content.csv', sep='\t')
			page = article.find("a",{"class":"tt-post-title"})['href']
			saved = dataset.page.unique().tolist() + content_df.page.unique().tolist()
			if page not in saved:
				print("Page not found in dataset, crawling: ", page)
				try:
					with eventlet.Timeout(35):
						title = article.find("a", {"class":"tt-post-title"}).text.replace('\r', '').replace('\n', '')
						browser.get(page)
						soup = bs(browser.page_source,"html.parser")
				except:
					continue
				try:
					main_article = soup.findAll("div",{"class":"tt-content"})[1]
					title = title.replace("—","-").replace("–", "-")
					s_title = main_article.p.text.replace("—","-").replace("–", "-")
					if len(title.split("-")) < 2:
						check = 0
						claim = soup.find("div",{"class":"claim-description"}).text
						claim_label = soup.find("div",{"class":"rating-description"}).text
					elif len(s_title.split("-")) >= 2:
						check = 1
						split = s_title.split("-")
						(claim,claim_label) = (''.join(split[:-1]),split[-1])
					else:
						check = 2
						split = title.split("-")
						(claim,claim_label) = (''.join(split[:-1]),split[-1])
	
					date = article.find("span", {"class":"tt-post-date"})
					if date is not None:
						date = date.text	
					else:
						date = soup.find("span", {"class":"tt-post-date-single"}).text

					tags = soup.find("ul",{"class":"tt-tags"})
					if tags is not None:
						tags = [e.text for e in tags.findAll("a")]

					author = article.find("span", {"class":"tt-post-author-name"})
					if author is not None:
						author = author.text
					else:
						author = soup.find("meta",{"name":"author"})['content']

					sources = [e for e in main_article.findAll("a") if (e.has_attr('href'))]
					source_list = utils.fix_origin_list(sources)
				except Exception as e:
					print (str(check)+"Unexpected error:", e)
					utils.inputLogError(page,"REACT ERROR:","tof")
					continue
				
				claim_source_url,claim_source_domain = utils.fix_source(sources)
				date = parse(date).strftime('%Y/%m/%d')
				claim = claim.strip()
	
				example = soup.find("div", {"class":"content-source"})
				#if there is example, entry will be saved to tof_e_content.csv
				if example is not None:
					example = example.blockquote.findAll("p")
					example = ''.join([e.text+"\n" for e in example])
					entry = [page,claim,claim_label,tags,claim_source_domain,claim_source_url,date,example,""]
					for i,e in enumerate(entry):
						if e is not None:
							print(header_e[i],"\t\t\t",len(e))
					content_df.loc[page] = entry
				
				elif ((claim_source_url is not None) and len(source_list)>0):
					# CREATE ENTRY FOR GENERATE STANCES CSV.PY
					entry = [page,claim,claim_label,tags, source_list, claim_source_domain,claim_source_url,date]
					dataset.loc[page] = entry
				else:
					utils.inputLogError(page,"NO SOURCE:","tof")
	
			dataset.to_csv(cwd+"/tof.csv", sep='\t', header=header, index=False)
			content_df.to_csv(content_path+"/tof_e_content.csv", sep='\t', header=header_e, index=False)
	
		utils.update_last_saved_page(num_pages-pagenumber,base_url)

browser.quit()
