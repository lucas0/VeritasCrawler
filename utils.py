from bs4 import BeautifulSoup, Tag	
import json
import time
import re
import random
from boilerpipe.extract import Extractor
import ssl
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
try:
    import urllib.request
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
    import urllib2
from langdetect import detect
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dateutil.parser import parse
import unicodedata
import pandas as pd
import numpy as np
import urllib.request
import os
import eventlet
eventlet.monkey_patch()
import requests
import sys
from eatiht import eatiht
sys.setrecursionlimit(10000)


cwd = os.path.dirname(os.path.abspath(__file__))
bad_domains = ["youtube.com", ":///", "vimeo.com", "reddit.com", "twitter.com", "youtu.be"]
fc_agencies = ["snopes.com", "emergent.info", "politifact.com", "factcheck.org", "truthorfiction.com"]
base_urls = {"factcheck":"https://www.factcheck.org/fake-news/","snopes":"https://www.snopes.com/fact-check/page/2/", "politifact":"http://www.politifact.com/truth-o-meter/statements/", "tof":"https://www.truthorfiction.com/category/fact-checks/"}
infofile = cwd+"/input/infofile.txt"

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--dns-prefetch-disable")	
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--single-proces')

chrome_driver = os.path.abspath(cwd+"/chromedriver")

browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)

def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print('{:s} function took {:.3f} ms'.format(f.__name__, (time2-time1)*1000.0))

        return ret
    return wrap


def removeFile(filename):
	try:
		os.remove(filename)
		print('File Removed: '+filename)
	except OSError:
		pass


def inputLogError(url, error, dataset):
	print(error)
	with open(cwd+"/input/"+dataset+"/logfile.txt","a+") as log:
		lines = log.readlines()
	for line in lines:
		if url not in line:
			with open(cwd+"/"+dataset+"/logfile.txt","a+") as log:
				log.write(error+url+"\n")


def getOnlyText(root):
	if root.string != None:
		return root.string
	else:
		return ''.join([getOnlyText(e) for e in root.contents])		


def get_url_domain(url):
	parsed_url = urlparse(url)
	source_domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_url)
	return source_domain



def fix_origin_list(source_elems, meta = None):
	fixed_list = []
	for elem in source_elems:
		source_url = elem['href']
		if meta is not None:
			meta_date = meta.split(",")[-2][1:-2]
			source_text = elem.text
			if meta_date not in source_text:
				continue
		if (source_url is not None) and (source_url[-4:] != ".asp"):
			source_domain = get_url_domain(source_url)
			if sum([1 for e in fc_agencies if e in source_domain]) > 0:
				continue
			elif sum([1 for e in bad_domains if e in source_domain]) > 0:
				continue
			elif ("facebook.com" in source_domain):
				if ("/videos/" in source_url) or ("/photos/" in source_url):
					continue
			elif ("archive" in source_domain):
				fixed_list.append(source_url.replace("/image",""))
			else:
				fixed_list.append(source_url)
	return list(set(fixed_list))


def fix_source(source_elems, meta = None):
	for elem in source_elems:
		source_url = elem['href']
		if meta is not None:
			meta_date = meta.split(",")[-2][1:-2]
			source_text = elem.text
			if meta_date not in source_text:
				continue
		if (source_url is not None) and (source_url[-4:] != ".asp"):
			parsed_url = urlparse(source_url)
			source_domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_url)
			if sum([1 for e in fc_agencies if e in source_domain]) > 0:
				continue
			elif sum([1 for e in bad_domains if e in source_domain]) > 0:
				continue
			elif ("facebook.com" in source_domain):
				if ("/videos/" in source_url) or ("/photos/" in source_url):
					continue
			elif ("archive" in source_domain):
				return (source_url.replace("/image",""),source_domain)
			else:
				return (source_url,source_domain)
	return (None, None)

def update_last_saved_page(page_num,agency):
	with open(infofile, "r+") as f:
		lines = f.readlines()
		for idx,line in enumerate(lines):
			if agency+": " in line:
				lines[idx] = agency+": "+str(page_num)+"\n" 
				
	a = "".join(lines)
	# SAVE PROGRESS PAGE
	with open(infofile, "w+") as f:
		f.write(a)


def get_last_saved_page(agency):
	with open(infofile, "r+") as f:
		lines = f.readlines()
		for line in lines:
			if agency+": " in line:
				return(int(line.split(" ")[1]))	


def get_num_of_pages(agency, name_or_url=True):
	if name_or_url:
		base_url = base_urls[agency]
	else:
		base_url = agency
	req = requests.get(base_url)
	soup = BeautifulSoup(req.text,"html.parser")
	if agency == "snopes":
		pages = soup.find("title").text.split(" ")[-3]
	elif agency == "factcheck":
		pagination = soup.find("ul",{"class":"pagination"})
		last_child = pagination.find_all(recursive=False)[-1]
		pages = last_child.a['href'].split("/")[-2]
	elif agency == "politifact":
		pages = soup.find("span",{"class":"step-links__current"}).text.split()[-1]
	elif agency in ["https://www.truthorfiction.com/category/fact-checks","https://www.truthorfiction.com"]:
		pages = soup.findAll("a", {"class":"page-numbers"})[-2].text
		
	return int(pages)			

def getVerdict(text):
	answer = ''.join(text.split("A:")[1:]).strip(" ")
	verdict = answer.split(".")[0][:3]
	print(answer)
	if "No" in verdict:
		return "false" 
	elif "Yes" in verdict:
		return "true" 
	else:
		return "unverified"

#given an bs.html tag, returns a list of all <a> elements on it
def getSources(content):
	sources = []
	f_source = 0
	p_list = (i for i in content.contents[1:-1] if isinstance(i,Tag))
	
	for p in p_list:
		text = getOnlyText(p)
		if (f_source == 1):
			source_elem = p.find("a")
			if source_elem != None: 
				sources.append(source_elem)
		if "sources" == text.lower():
			f_source = 1
	return sources


def contentLogError(url, error, source):
	print("error:"+str(error)+str(source))
	with open(cwd+"/eatiht/logfiles/log_"+source+"_content.txt","r+") as log:
		lines = log.readlines()
		print(lines)
	for line in lines:
		if url not in line:
			with open(cwd+"/eatiht/logfiles/log_"+source+"_content.txt","a+") as log:
				log.write(error+url+"\n")


def tryContent(data):
	soup = BeautifulSoup(data,"lxml")
	try0 = soup.find("div",{"itemprop":"articleBody"})
	try1 = soup.find("div",{"class":"entry-content article-text"})
	try2 = soup.find("div",{"class":"article-text"})
	try3 = soup.find("div",{"class":"entry-content"})
	catch = next((item for item in [try0,try1,try2,try3] if item is not None),soup.new_tag('div'))
	while catch.find(["applet","code","embed","head","object","script","server"]):
		catch.find(["applet","code","embed","head","object","script","server"]).decompose()

	manual = unicodedata.normalize('NFKD', catch.text.replace("\n","")).encode('ascii','ignore')

	if isinstance(manual, bytes):
		manual = manual.decode("ascii")

	return manual

#returns the domain of given url
def getDomain(url):
	domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(url))
	domain = ''.join(domain.split())
	domain = domain.replace("https://www.","")
	domain = domain.replace("https://","")
	domain = domain.replace("http://www.","")
	domain = domain.replace("http://","")
	return domain

#this tries to get the content of a given website by navigating on html tabs with BeautifulSoup
def getManual(url,source="mixed"):
	#chrome_options = Options()
	#chrome_options.add_argument("--headless")
	#chrome_options.add_argument("--dns-prefetch-disable")	
	#chrome_options.add_argument("--window-size=1920x1080")
	#chrome_driver = os.getcwd() +"/chromedriver"
	
	browserManual= webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
	error = False
	req = None

	t=eventlet.Timeout(15)
	try:
		req = requests.get(url)
		if req == "<Response [404]>":
			contentLogError(url, "404\n",source)
			browserManual.quit()
			return(False,"404")
	except:
		error = True
	finally:
            t.cancel()

	with eventlet.Timeout(10):
		try:
			browserManual.get(url)
			source_body = browser.page_source
			current_url = browser.current_url
		except:
			if error == True:
				contentLogError(url,"ERROR (selenium+requests)\n",source)
				browserManual.quit()
				return(False,"domain")
			else:
				source_body = req.text
				current_url = req.url

	actual_domain = getDomain(current_url)
	claim_source_domain = getDomain(url)

	if  actual_domain != claim_source_domain: #check if it's not redirected"
		print(actual_domain,claim_source_domain)
		browserManual.quit()
		return (False, "redirect")

	if len(source_body) == 0:
		browserManual.quit()
		return (False, "no content")

	if isinstance(source_body, bytes):
		source_body = source_body.decode("ascii")

	manual = tryContent(source_body)

	browserManual.quit()
	return (True,manual)

#gets the carbon date(first date of indexing) of a page
def getDate(url):
	try:
		with eventlet.Timeout(30):
			carbon_date = requests.get("http://cd.cs.odu.edu/cd/"+url)
			data = json.loads(carbon_date.text)
			if data['estimated-creation-date'] is not '':
				date = parse(data['estimated-creation-date']).strftime('%Y/%m/%d')
				return date
	except:
		pass

	return 'N/A'

#gets the 'body' of an url, also checks if domain is a webarchive to proceed accordingly
#this method makes use of getManual/getPipe/getEathit and selects the larger of them
def getContent(url,source="mixed",fromArchive=False):
	if fromArchive:
		print("[utils.py] Getting content from archive: http://archive.fo/"+url)
	else:
		print("[utils.py] Getting content: "+url)

	#browser.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
	if fromArchive:
		#try with archive:
		url = "http://archive.fo/"+url
		row = None
		with eventlet.Timeout(15):
			try:
				browser.get(url)
				soup = BeautifulSoup(browser.page_source,"lxml")
				row = soup.find("div",{"id":"row0"})
			except:
				pass
		if row is None:
			browser.quit()
			return ("","no log in archive.is")
		else:
			text = row.find("div",{"class":"TEXT-BLOCK"})
			url = text.a['href']
			
	eat = ''
	pipe = ''
	manual = ''

	if (url[-4:] in [".jpg",".pdf",".mp3",".mp4"]) or ("/video/" in url) or ("/image/" in url):
		contentLogError(url,"FORMAT\n",source)
		browser.quit()
		return ("","format")
	try:
		with eventlet.Timeout(15):
			eat = eatiht.extract(url).replace("\n","")
			print("ACK eat",len(eat))
	except:
		pass
	try:
		with eventlet.Timeout(15):
			pipe = Extractor(extractor='ArticleExtractor', url=url).getText().replace("\n","")
			print("ACK pipe",len(pipe))
	except:
		pass

	browser.quit()
	manual = getManual(url,source)
	if manual[0] == False:
		if manual[1] == 'redirect':
			contentLogError(url,"REDIRECT\n",source)
			return("","redirect")
		manual = ''
	else:
		manual = manual[1]
		print("ACK manual",len(manual))

	selected = max([(eat,"eat"),(pipe,"pipe"),(manual,"manual")], key=lambda x: len(x[0]))

	if len(selected) > 0:
		lang = detect(str(selected))
		if "en" not in lang:
			contentLogError(url,"LANGUAGE\n",source)
			return("","language")
	else:
		contentLogError(url,"NO CONTENT\n",source)

	return (selected[0],selected[1])
