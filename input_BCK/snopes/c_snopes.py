from dateutil.parser import parse
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys, os
import pandas as pd
sys.path.insert(1, os.path.join(sys.path[0], '../..'))
import utils

cwd = os.path.abspath(os.path.dirname(sys.argv[0]))
parent_path = os.path.abspath('')
infofile = parent_path+"/infofile.txt"

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")
chrome_driver = parent_path+"/chromedriver"

browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)

header = ["page", "claim", "claim_label", "tags", "source_list", "claim_source_domain", "claim_source_url", "date"]
baseurl = "https://www.snopes.com/fact-check/page/"
dataset = pd.read_csv(cwd+'/snopes.csv', sep='\t')

num_pages = utils.get_num_of_pages("snopes")
last_saved_page = utils.get_last_saved_page("snopes")
jumped = 0
print(last_saved_page)
for pagenumber in reversed(range(1,num_pages-last_saved_page)):
	url = baseurl+str(pagenumber)+"/"
	browser.get(url)
	data = browser.page_source
	soup = bs(data,"html.parser")
	lwrapper = soup.find("div", {"class":"list-group"})
	articlelist = lwrapper.findAll("article")
	for article in articlelist:
		page = article.find("a")['href']
		print("P> {} T> {}".format(pagenumber,page))
		# ALREADY SAVED
		if page in dataset.page.unique():
			jumped+=1; print("Already saved article: ",page)
			continue
	
		browser.get(page)
		data = browser.page_source
			
		soup = bs(data,"html.parser")

		if "Page not found" in browser.title:
			utils.logError(page,"REQUEST:","snopes")
			continue
		try:	
			date = soup.find("meta",{"property":"DC.date.issued"})['content']
		except:
			date = soup.find("span",{"class":"date-published"}).text
		date = parse(date).strftime('%Y/%m/%d')
		content = soup.find("div",{"class":"entry-content article-text"})

		# CONTENT
		if (content is None):
			jumped+=1; print("Content is None: ",page)
			utils.logError(page,"CONTENT:","snopes")
			continue
		
		
		# CONTENT IS NONE
		if (content.find("div", {"class":"claim"}) is None):
			#CLAIM
			if (content.p is not None):
				claim = utils.getOnlyText(content.p).lower().lstrip("Claim: ")
			else:
				jumped+=1; print("NO CLAIM: {} {} \n\n".format(page,jumped))
				utils.logError(page,"NO CLAIM:","snopes")
				continue
			
			# VERDICT
			if soup.find("title").text.lower().startswith("false"):
				verdict = "false"
			elif soup.find("title").text.lower().startswith("true"):
				verdict = "true"
			elif content.find("div", {"class":"claim-old"}) is not None:
				verdict = utils.getOnlyText(content.find("div", {"class":"claim-old"}))
			elif content.find("a", {"class":"claim"}) is not None:
				verdict = utils.getOnlyText(content.find("a", {"class":"claim"}))
			else:
				jumped+=1; print("NO VERDICT: {} {} \n\n".format(page,jumped))
				utils.logError(page, "NO VERDICT:","snopes")
				continue
		# CONTENT IS NOT NONE
		else:
			if content.find("p", {"itemprop":"claimReviewed"}) is not None:
				claim = content.find("p", {"itemprop":"claimReviewed"}).text.strip()
			else:
				claim = content.p.text.strip()
			verdict = content.find("div", {"class":"claim"})['class'][1]
		

		# get the whole rest of the html:
		html = soup.new_tag('div')
		article_text = soup.find("div",{"class":"article-text-inner"})
		for idx,elem in enumerate(article_text):
			text = utils.getOnlyText(elem).lower()
			if "origin" == text:
				c = soup.new_tag("div")
				for e in article_text.contents[idx:]:
					if "Contact us" in utils.getOnlyText(e):
						break
					else:
						html.append(e)

		assert claim is not None, "Claim is None"
		assert html is not None, "HTML is None"

		claim = " ".join(claim.split())
		verdict = " ".join(verdict.split())
		
		# TAGS
		tags = bs(data,"html.parser").find("meta",{"name":"news_keywords"})['content'].split(",")
		source_elems = [e for e in html.findAll('a') if e.has_attr("href")]
		source_list = source_list = utils.fix_origin_list(source_elems)

		# FIX SOURCE URL
		(source_url,source_domain) = utils.fix_source(page,source_elems)

		if (source_url is not None) and (len(source_list)>0):
			# CREATE ENTRY
			entry = [page,claim,verdict,tags,source_list,source_domain,source_url,date]
			dataset.loc[page] = entry

	# SAVE DATASET
	print("salvou")
	dataset.to_csv(cwd+"/snopes.csv", sep='\t', header=header, index=False)

	utils.update_last_saved_page(num_pages-pagenumber,"snopes")
browser.quit()
