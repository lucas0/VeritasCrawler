import datetime
import time
from bs4 import BeautifulSoup as bs
import requests
import pandas as pd
import os
from dateutil.parser import parse
from urllib.parse import urlparse

cwd = os.getcwd()
header = ["page", "claim", "claim_label", "tags", "claim_source_domain", "claim_source_url", "date"]
dataset = pd.read_csv(cwd+'/snopes2.csv', sep='\t')

for article in list(os.walk("/Users/lucas/Developer/DatasetCrawl/snopes"))[1:]:
	print(article[0])
	with open(article[0]+"/info.txt", "r+") as info:
		data = info.readlines()

	for e in data:
		if "Link: " in e:
			page = e.split("Link: ")[1].replace('\r', '').replace('\n', '')
			
	if page not in dataset.page.unique():
		for e in data:
			if "Title: " in e:
				claim = e.split("Title: ")[1].replace('\r', '').replace('\n', '')
			if "Verdict: " in e:
				claim_label = e.split("Verdict: ")[1].replace('\r', '').replace('\n', '')
			if "Date: " in e:
				date = "20"+e.split("Date: ")[1]
				date = parse(date).strftime('%Y/%m/%d').replace('\r', '').replace('\n', '')

		data = requests.get(page).text
		tags = bs(data,"html.parser").find("meta",{"name":"news_keywords"})['content'].split(",")

		with open(article[0]+"/article.html", "r+") as html:
			data = html.read()

		soup = bs(data,"html.parser")
		source_elem = soup.find(lambda tag: tag.name=='a' and tag.has_attr("href"))

		if source_elem is None:
			continue

		claim_source_url = source_elem['href']
		parsed_url = urlparse(claim_source_url)
		claim_source_domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_url)
		if ("snopes" in claim_source_domain) or (":///" in claim_source_domain):
			continue

		entry = [page,claim,claim_label,tags,claim_source_domain,claim_source_url,date]
		dataset.loc[page] = entry

	adjust = 0
	dataset.to_csv(cwd+"/snopes.csv", sep='\t', header=header, index=False)