from newspaper import Article
from bs4 import BeautifulSoup, Tag
import json
import time
import re
import random
from boilerpipe.extract import Extractor
import ssl
from selenium.common.exceptions import TimeoutException
try:
    import urllib.request
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
    import urllib2
from langdetect import detect
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from dateutil.parser import parse
import unicodedata
import pandas as pd
import numpy as np
import urllib.request
import os
import eventlet
import requests
import sys
sys.setrecursionlimit(10000)

cwd = os.path.dirname(os.path.abspath(__file__))
bad_domains = ["youtube.com", ":///", "vimeo.com", "reddit.com", "twitter.com", "youtu.be", "linkedin.com", "whatsapp", "books.google", "spreadsheets.google"]
fc_agencies = ["snopes.com", "emergent.info", "politifact.com", "factcheck.org", "truthorfiction.com"]
base_urls = {"factcheck":"https://www.factcheck.org/fake-news/","snopes":"https://www.snopes.com/fact-check/page/2/", "politifact":"http://www.politifact.com/truth-o-meter/statements/", "tof":"https://www.truthorfiction.com/category/fact-checks/"}
infofile = cwd+"/input/infofile.txt"

chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("---disable-setuid-sandbox")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--dns-prefetch-disable")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--single-proces')

chrome_driver = os.path.abspath(cwd+"/chromedriver")

def removeFile(filename):
        try:
                os.remove(filename)
                print('File Removed: '+filename)
        except OSError:
                pass

################# methods handling error logs ########################
def contentLogError(url, error, origin):
        print("error:"+str(error)+str(origin))
        with open(cwd+"/eatiht/logfiles/log_"+origin+"_content.txt","r+") as log:
                lines = log.readlines()
                print(lines)
        for line in lines:
                if url not in line:
                        with open(cwd+"/eatiht/logfiles/log_"+origin+"_content.txt","a+") as log:
                                log.write(error+url+"\n")

def inputLogError(url, pagenum, error, dataset):
    print("ERROR:",error)
    with open(cwd+"/input/"+dataset+"/logfile.txt","r+") as log:
        lines = log.readlines()
        for line in lines:
            if url in line:
                return
            #with open(cwd+"/"+dataset+"/logfile.txt","a+") as log:
        log.write(error+"|P>"+str(pagenum)+" "+url+"\n")

################# methods handling page numbers ########################
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
        print(base_url)
        req = requests.get(base_url)
        print(req)
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

################# methods dealing with origin(s) #######################
#remove unwanted origin candidates from the list
def cleanOrigins(origins, meta = None):
        fixed_list = []
        for elem in origins:
            t = eventlet.Timeout(50)
            try:
                browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
                origin_url = elem['href']
                if meta is not None:
                        meta_date = meta.split(",")[-2][1:-2]
                        origin_text = elem.text
                        if meta_date not in origin_text:
                                continue
                if (origin_url is not None) and (origin_url[-4:] not in [".pdf",".asp"]):
                        origin_domain = getDomain(origin_url)
                        if sum([1 for e in fc_agencies if e in origin_domain]) > 0:
                                continue
                        elif sum([1 for e in bad_domains if e in origin_domain]) > 0:
                                continue
                        elif ("facebook.com" in origin_domain):
                                if ("/videos/" in origin_url) or ("/photos/" in origin_url):
                                        continue
                        browser.get(origin_url)
                        code = [req.response.status_code for req in browser.requests if req.response]
                        if any(x in [301, 404] for x in code):
                            continue
                        elif ("archive" in origin_domain):
                                fixed_list.append(origin_url.replace("/image",""))
                        else:
                                fixed_list.append(origin_url)
            except Exception as e:
                input("ERROR ON CLEANING ORIGIN:"+str(e))
                pass
            finally:
                browser.quit()
                t.cancel()
        return list(set(fixed_list))

################# methods that capture webpage content #######################
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


#returns the domain of given url
def getDomain(url):
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(url))
        domain = ''.join(domain.split())
        domain = domain.replace("https://www.","")
        domain = domain.replace("https://","")
        domain = domain.replace("http://www.","")
        domain = domain.replace("http://","")
        return domain

#gets the 'body' of an url, also checks if domain is a webarchive to proceed accordingly
#update: now, this method makes use of only one third party lib: newspaper 3k, seems to work really well.
#this method makes use of getManual/getPipe/getEathit and selects the larger of them
def getContent(url,source="mixed",fromArchive=False):
        oDomain = getDomain(url)
        if sum([1 for e in bad_domains if e in oDomain]) > 0:
                return (None, "bad domain")

        if (url[-4:] in [".jpg",".pdf",".mp3",".mp4"]) or ("/video/" in url) or ("/image/" in url):
                contentLogError(url,"FORMAT\n",source)
                return (None, "format")

        if "http://archive." in url:
                fromArchive = True

        if not fromArchive:
                print("[utils.py] Getting content: "+url)
                try:
                        a = Article(url)
                        a.download()
                        a.parse()
                        a.nlp()
                        date = a.publish_date.strftime('%Y/%m/%d')
                        if len(a.text) > 50:
                            return ((a.text, a.title, a.authors, a.summary, date, a.keywords), "newspaper")
                        raise
                except:
                        return(None,"eat")

        #try with archive:
        else:
                print("[utils.py] Getting content from archive: http://archive.fo/"+url)

                browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
                url = "http://archive.fo/"+url
                row = None
                t=eventlet.Timeout(20)
                try:
                        browser.get(url)
                        soup = BeautifulSoup(browser.page_source,"lxml")
                        row = soup.find("div",{"id":"row0"})
                except:
                        pass
                finally:
                        t.cancel()
                        browser.quit()

                if row is None:
                        return(None,"no log in archive.is")
                else:
                        text = row.find("div",{"class":"TEXT-BLOCK"})
                        url = text.a['href']

                try:
                        a = Article(url)
                        a.download()
                        a.parse()
                        a.nlp()
                        date = a.publish_date.strftime('%Y/%m/%d')
                        return ((a.text, a.title, a.authors, a.summary, date, a.keywords), "newspaper")
                except:
                        return(None,"no log in archive.is")


#########################################################
################# old code below ########################
#########################################################

#def tryContent(data):
#       soup = BeautifulSoup(data,"lxml")
#       try0 = soup.find("div",{"itemprop":"articleBody"})
#       try1 = soup.find("div",{"class":"entry-content article-text"})
#       try2 = soup.find("div",{"class":"article-text"})
#       try3 = soup.find("div",{"class":"entry-content"})
#       catch = next((item for item in [try0,try1,try2,try3] if item is not None),soup.new_tag('div'))
#       while catch.find(["applet","code","embed","head","object","script","server"]):
#               catch.find(["applet","code","embed","head","object","script","server"]).decompose()
#
#       #manual = unicodedata.normalize('NFKD', catch.text.replace("\n","")).encode('ascii','ignore')
#       manual = unicodedata.normalize('NFKD', catch.text).encode('ascii','ignore')
#
#       if isinstance(manual, bytes):
#               manual = manual.decode("ascii")
#
#       return manual
##this tries to get the content of a given website by navigating on html tabs with BeautifulSoup
#def getManual(url,source="mixed"):
#       #chrome_options = Options()
#       #chrome_options.add_argument("--headless")
#       #chrome_options.add_argument("--dns-prefetch-disable")
#       #chrome_options.add_argument("--window-size=1920x1080")
#       #chrome_driver = os.getcwd() +"/chromedriver"
#
#       browserManual = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
#       error = False
#       req = None
#
#       #selenium browser requests do not return the HTML response code, so I use requests.get to check if the page is 404
#       t=eventlet.Timeout(15)
#       try:
#               req = requests.get(url)
#               if req == "<Response [404]>":
#                       contentLogError(url, "404\n",source)
#                       browserManual.quit()
#                       return(False,"404")
#       except:
#               error = True
#       finally:
#            t.cancel()
#
#       t = eventlet.Timeout(10)
#       try:
#               browserManual.get(url)
#               source_body = browserManual.page_source
#               current_url = browserManual.current_url
#       except:
#               if error == True:
#                       contentLogError(url,"ERROR (selenium+requests)\n",source)
#                       return(False,"domain")
#               else:
#                       source_body = req.text
#                       current_url = req.url
#       finally:
#               t.cancel()
#               browserManual.quit()
#
#       try:
#               actual_domain = getDomain(current_url)
#               claim_source_domain = getDomain(url)
#
#               if  actual_domain != claim_source_domain: #check if it's not redirected"
#                       print(actual_domain,claim_source_domain)
#                       browserManual.quit()
#                       return (False, "redirect")
#
#               if len(source_body) == 0:
#                       browserManual.quit()
#                       return (False, "no content")
#
#               if isinstance(source_body, bytes):
#                       source_body = source_body.decode("ascii")
#
#               manual = tryContent(source_body)
#       except Exception as e:
#               print(e)
#       finally:
#               browserManual.quit()
#
#       return (True,manual)
#
##gets the carbon date(first date of indexing) of a page
#def getDate(url):
#       try:
#               with eventlet.Timeout(30):
#                       carbon_date = requests.get("http://cd.cs.odu.edu/cd/"+url)
#                       data = json.loads(carbon_date.text)
#                       if data['estimated-creation-date'] is not '':
#                               date = parse(data['estimated-creation-date']).strftime('%Y/%m/%d')
#                               return date
#       except:
#               pass
#
#       return 'N/A'
#
##gets the 'body' of an url, also checks if domain is a webarchive to proceed accordingly
##this method makes use of getManual/getPipe/getEathit and selects the larger of them
#def getContent(url,source="mixed",fromArchive=False):
#       a = Article(url)
#       a.download()
#       a.parse()
#       a.nlp()
#       date = a.publish_date.strftime('%Y/%m/%d')
#       return (a.text, a.title, a.authors, a.summary, date, a.keywords, "newspaper")
#       if fromArchive:
#               print("[utils.py] Getting content from archive: http://archive.fo/"+url)
#       else:
#               print("[utils.py] Getting content: "+url)
#
#       print("check-1")
#       browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
#       print("check-2")
#       if fromArchive:
#               #try with archive:
#               url = "http://archive.fo/"+url
#               row = None
#               t=eventlet.Timeout(15)
#               try:
#                       browser.get(url)
#                       soup = BeautifulSoup(browser.page_source,"lxml")
#                       row = soup.find("div",{"id":"row0"})
#               except:
#                       pass
#               finally:
#                       t.cancel()
#                       browser.quit()
#               if row is None:
#                       return ("","no log in archive.is")
#               else:
#                       text = row.find("div",{"class":"TEXT-BLOCK"})
#                       url = text.a['href']
#
#       print("check-3")
#       eat = ''
#       pipe = ''
#       manual = ''
#
#       if (url[-4:] in [".jpg",".pdf",".mp3",".mp4"]) or ("/video/" in url) or ("/image/" in url):
#               contentLogError(url,"FORMAT\n",source)
#               return ("","format")
#       print("check-4")
#       t=eventlet.Timeout(15)
#       try:
#               #eat = eatiht.extract(url).replace("\n","")
#
#               print("check-5")
#               eat = eatiht.extract(url)
#               print("ACK eat",len(eat))
#       except:
#               print("NACK eat")
#               pass
#       finally:
#               t.cancel()
#
#       t=eventlet.Timeout(15)
#       try:
#               #pipe = Extractor(extractor='ArticleExtractor', url=url).getText().replace("\n","")
#               pipe = Extractor(extractor='ArticleExtractor', url=url).getText()
#               print("ACK pipe",len(pipe))
#       except:
#               print("NACK pipe")
#               pass
#       finally:
#               print("check-6")
#               t.cancel()
#
#       print("check-7")
#       manual = getManual(url,source)
#       if manual[0] == False:
#               if manual[1] == 'redirect':
#                       contentLogError(url,"REDIRECT\n",source)
#                       return("","redirect")
#               manual = ''
#       else:
#               manual = manual[1]
#               print("ACK manual",len(manual))
#
#       selected = max([(eat,"eat"),(pipe,"pipe"),(manual,"manual")], key=lambda x: len(x[0]))
#
#       if len(selected) > 0:
#               lang = detect(str(selected))
#               if "en" not in lang:
#                       contentLogError(url,"LANGUAGE\n",source)
#                       return("","language")
#       else:
#               contentLogError(url,"NO CONTENT\n",source)
#
#       return (selected[0],selected[1])
