nonBreakSpace = u'\xa0'
from bs4 import BeautifulSoup as bs
from dateutil.parser import parse
import os, sys
import pandas as pd
sys.path.insert(1, os.path.join(sys.path[0], '../..'))
import utils
import requests

cwd = os.path.abspath(os.path.dirname(sys.argv[0]))
parent_path = os.path.abspath('')

header = ["page", "claim", "claim_label", "tags", "source_list", "claim_source_domain", "claim_source_url", "date"]
baselink = "https://www.factcheck.org/fake-news/page/"
dataset = pd.read_csv(cwd+'/factcheck.csv', sep='\t')

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
			footer = soup.find("footer")
			sources = utils.getSources(content)
			source_list = utils.fix_origin_list(sources)
			(source_url,source_domain) = utils.fix_source(page,sources)
			class_list = ["issue","location","person"]
			tag_list = []
			for e in footer.findAll("li",class_=class_list):
				tag_list += e.findAll("a")
			tags = [e.text for e in tag_list]

			if ((source_url is not None) and (len(source_list) > 0)):
				# CREATE ENTRY
				entry = [page,claim,verdict,tags,source_list,source_domain,source_url,date]
				dataset.loc[page] = entry
			else:
				utils.inputLogError(page,"NO SOURCE:","factcheck")
			

	# SAVE DATASET
	dataset.to_csv(cwd+"/factcheck.csv", sep='\t', header=header, index=False)

	utils.update_last_saved_page(num_pages-pagenumber,"factcheck")
