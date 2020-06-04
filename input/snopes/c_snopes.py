# -*- coding: utf-8 -*-
from newspaper import Article
import psutil
import subprocess
import eventlet
import re
from dateutil.parser import parse
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys, os, requests
import pandas as pd
sys.path.insert(1, os.path.join(sys.path[0], '../..'))
import utils

cwd = os.path.abspath(__file__+'/..')
parent_path = os.path.abspath(__file__+'/../..')
infofile = parent_path+"/infofile.txt"

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")
chrome_driver = parent_path+"/chromedriver"

header = ["page", "claim", "verdict", "tags", "date", "author", "source_list"]
possible_verdicts = ('true', 'false','false', 'true', 'mixture', 'legend', 'unproven', 'mostly true', 'miscaptioned', 'scam', 'mostly false', 'misattributed', 'outdated', 'correct attribution', 'new-type', 'research in progress')
footer_strings = ["Contact us", "Latest Fact Checks"]
baseurl = "https://www.snopes.com/fact-check/page/"
dataset = pd.read_csv(cwd+'/snopes.csv', sep='\t')

last_saved_page = utils.get_last_saved_page("snopes")
num_pages = utils.get_num_of_pages("snopes")
jumped = 0
def get_date_snopes(soup, page):
        date = ""
        try:
                date = soup.find("meta",{"property":"DC.date.issued"})['content']
                date = parse(date).strftime('%Y/%m/%d')
        except TypeError:
                try:
                        date = soup.find("span",{"class":"date-published"}).text
                        date = parse(date).strftime('%Y/%m/%d')
                except AttributeError:
                        pass

        if date is "":
            a = Article(page)
            a.download()
            a.parse()
            a.nlp()
            date = a.publish_date
            if date is not None:
                date = strftime('%Y/%m/%d')
            else:
                date = ""

        return date

def get_content_snopes(soup):
        content = soup.find("div",{"class":"entry-content article-text"})
        if content is not None:
            if (content.find("div", {"class":"claim"}) is not None):
                return content,3
            else:
                return content,1

        content = soup.find("div",{"class":"post-body-card"})
        if content is not None:
            content = content.find('div', {"class": "card-body"})
            ret = content,2

        content = soup.find("div", {"class":"content"})
        rating = soup.find("div",{"class":"rating-wrapper"})
        table = content.find("table")
        if rating is not None:
            return content, 4
        elif table is not None:
            return content, 5
        else:
            return content, 6

        return "error",0

def get_verdict_snopes(content, soup, content_type):
        try:
           article = soup.find("article")
           rating = article.find("div",{"class":"media rating"})
           for c in rating.find("div", {"class":"media-body"}).findChildren():
                text = c.text.lower().strip()
                if text.startswith(possible_verdicts):
                    verdict = text
                    return verdict
        except Exception as e:
            print(e)
            pass
        if content_type == 1:
                if soup.find("title").text.lower().startswith("false"):
                        verdict = "false"
                elif soup.find("title").text.lower().startswith("true"):
                        verdict = "true"
                elif content.find("div", {"class":"claim-old"}) is not None:
                        verdict = content.find("div", {"class":"claim-old"}).text
                elif content.find("a", {"class":"claim"}) is not None:
                        verdict = content.find("a", {"class":"claim"}).text
                else:
                        verdict = 'error'

        if content_type in [2]:
                verdict = content.findAll("p")[1].text
                verdict = ''.join(c for c in verdict if c.isprintable())
                verdict = re.sub("[^a-z0-9]+","", verdict, flags=re.IGNORECASE)
                verdict = verdict[6:].lower()

        if content_type == 3:
                verdict = content.find("div", {"class":"claim"})['class'][1]

        if content_type == 4:
                try:
                    article = soup.find("article")
                    rating = article.find("div",{"class":"rating-wrapper"})
                    for c in rating.find("div", {"class":"media-body"}).findChildren():
                        text = c.text.lower().strip()
                        if text.startswith(possible_verdicts):
                            verdict = text
                            return verdict
                except:
                    pass

        if content_type == 5:
            table = content.find("table")
            text = table.text.lower().strip()
            verdict = re.sub('<.*>','',text)
            if verdict.startswith(possible_verdicts):
                return verdict
            else:
                return 'error'

        if content_type == 6:
                [s.extract() for s in content('noscript')]
                content_p = content.findAll("p")

                for e in content_p:
                    text = e.text.lower().strip()
                    if text.startswith('status:'):
                        verdict = text.lstrip('status:').strip()
                        if verdict.startswith('multiple'):
                            continue
                        return verdict

                for e in content_p:
                    text = e.text.lower().strip()
                    if text.startswith(possible_verdicts):
                        verdict = text
                        return verdict

        verdict = 'error'
        return verdict

def get_claim_snopes(content, soup, content_type):
        if content_type == 1:
                if (content.p is not None):
                        claim = content.p.text.lower().lstrip("Claim: ")

        if content_type == 2:
                claim = content.findAll("p")[0].text
                claim  = ''.join(c for c in claim if c.isprintable())
                claim = claim[5:].lower()
                claim = re.sub("[^a-z0-9\s]+","", claim, flags=re.IGNORECASE).strip()

        if (content_type == 3):
                if content.find("p", {"itemprop":"claimReviewed"}) is not None:
                        claim = content.find("p", {"itemprop":"claimReviewed"}).text.strip()
                else:
                        claim = content.p.text.strip()

        if (content_type in [4,5,6]):
                claim = soup.find("div",{"class":"claim-wrapper"})
                if claim is not None:
                    claim = claim.find("div", {"class","claim"}).text.lower().strip()
                else:
                    content_p = content.findAll("p")
                    for e in content_p:
                        text = e.text.lower().strip()
                        if text.startswith(("claim:","legend:")):
                            claim = text.lstrip('claim:').lstrip('legend:')
                            claim = re.sub("[^\?!,\.a-z0-9\s]+","", claim, flags=re.IGNORECASE).strip()
                            break

        if claim is None:
            return "error"

        claim = ' '.join(claim.split())
        return claim.lower().split('see example')[0]

def get_html_snopes(content, soup, content_type):
        if content_type in [1,3]:
                html = soup.new_tag('div')
                article_text = soup.find("div",{"class":"article-text-inner"})
                for idx,elem in enumerate(article_text):
                        text = elem.text.lower()
                        if "origin" == text:
                                for e in article_text.contents[idx:]:
                                        if "Contact us" in e.text:
                                                break
                                        else:
                                                html.append(e)
        if content_type in [2,4,5,6]:
                html = soup.new_tag('div')
                if content_type == 2:
                    article_text = content.find("div",{"class":"card-body"}).findAll("p")[4:]
                    article_contents = article_text.contents
                else:
                    article_text = soup.findAll(["p","div", "font"])
                    article_contents = article_text

                for idx,elem in enumerate(article_text):
                    text = elem.text.lower().strip()
                    if text.startswith(("summary","origin")):
                        for e in article_contents[idx:]:
                            if any(x in e.text for x in footer_strings):
                                break
                            else:
                                html.append(e)
                if len(html) == 0:
                    article_text = soup.findAll(["p"])
                    article_contents = article_text[4:]
                    for idx,e in enumerate(article_text):
                        text = e.text.lower().strip()
                        if any(x in e.text for x in footer_strings):
                            break
                        else:
                            html.append(e)

        return html

def get_tags_snopes(soup):
    tags = soup.findAll("meta",{"property":"article:tag"})
    if tags is None:
        tags = soup.find("meta",{"name":"news_keywords"})['content']
    else:
        tags = ','.join([e['content'] for e in tags])
    tags = tags.split(",")

    if 'ASP Article' in tags: tags.remove('ASP Article')

    return tags

def get_author_snopes(soup):
    author = soup.find("div",{"class":"authors"}).text.strip()
    return author

def get_soup(url):
        print("getting soup for: ",url)
        t_s=eventlet.Timeout(20)
        try:
            browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
            browser.get(url)
            soup = bs(browser.page_source,"html.parser")
            if "Page not found" in browser.title:
                utils.inputLogError(page,pagenumber, "REQUEST:","snopes")
                return None
            return soup
        except:
            pass
        finally:
            browser.quit()
            t_s.cancel()

for pagenumber in reversed(range(1,num_pages-last_saved_page)):
        browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        url = baseurl+str(pagenumber)+"/"
        browser.get(url)
        data = browser.page_source
        print(url)
        soup = bs(data,"html.parser")
        lwrapper = soup.find("div", {"class":"media-list"})
        articlelist = lwrapper.findAll("article")
        ignore_list = open(cwd+"/ignored_claims.txt", "r+").readlines()
        saved_list = dataset.page.unique().tolist()
        browser.quit()
        for article in articlelist:
                page = article.find("a")['href']
                print("\nP> {} T> {}".format(pagenumber,page))

                # ALREADY SAVED
                if page in (saved_list + ignore_list):
                    jumped+=1; print("Already saved article: ",page)
                    continue

                soup = get_soup(page)
                if soup is None:
                    continue

                #################### CONTENT ####################
                content, content_type = get_content_snopes(soup)
                if content is "error":
                    continue

                if "has been moved here:" in content.text:
                    page = baseurl[:-1]+content.find("a")['href']

                    # ALREADY SAVED
                    if page in (saved_list + ignore_list):
                        jumped+=1; print("Already saved article: ",page)
                        continue

                    soup = get_soup(page)
                    if soup is None:
                        continue

                content, content_type = get_content_snopes(soup)
                print("content type: ",content_type)
                if content is "error":
                    continue

                print("content lenght: ", len(content.text))
                if len(content.text) < 1000:
                    jumped+=1
                    utils.inputLogError(page, pagenumber, "NO CONTENT:","snopes")
                    continue

                #################### CLAIM ####################
                claim = get_claim_snopes(content, soup, content_type)
                print("claim: ",claim)
                if claim == 'error':
                        jumped+=1
                        utils.inputLogError(page,pagenumber, "NO CLAIM:","snopes")
                        continue

                elif any(x in claim for x in ['video','photo']):
                        jumped+=1
                        utils.inputLogError(page,pagenumber, "PHOTO/VIDEO:","snopes")
                        continue

                #################### VERDICT ####################
                verdict = str(get_verdict_snopes(content, soup, content_type).encode(), "ascii", "ignore")
                print("verdict: ",verdict)
                if verdict == 'error':
                        jumped+=1
                        utils.inputLogError(page,pagenumber,  "NO VERDICT (content type "+str(content_type)+") :","snopes")
                        continue

                # get the whole rest of the html:
                #################### HTML ####################
                html = get_html_snopes(content,soup,content_type)

                assert claim is not None, "Claim is None"
                assert len(html) != 0, "HTML is None"

                claim = " ".join(claim.split())
                verdict = " ".join(verdict.split())

                #################### TAGS ####################
                tags = get_tags_snopes(soup)
                print("tags: ["+', '.join([str(tag.encode(),"ascii","ignore") for tag in tags])+"]")

                #################### DATE ####################
                date = get_date_snopes(soup,page)
                print("date: ",date)

                #################### AUTHOR ####################
                author = get_author_snopes(soup)
                print("author: ",author)

                #################### SOURCES ####################
                source_elems = [e for e in html.findAll('a') if e.has_attr("href")]
                source_print = "<< | >>".join([e['href'] for e in source_elems])
                print("#sources_elems: ",len(source_elems), source_print)
                source_list = utils.cleanOrigins(source_elems)
                print("#sources: ",len(source_list))
                print("sources: ",source_list)

                if len(source_list)>0 and page not in dataset.page.unique():
                        # CREATE ENTRY
                        with open(cwd+"/pos_log.txt", "a") as f:
                            f.write(page+str(content_type))
                        entry = [page, claim, verdict, tags, date, author, source_list]
                        dataset.loc[page] = entry
                else:
                    jumped+=1
                    utils.inputLogError(page,pagenumber,  "NOT ENOUGH SOURCES (content type "+str(content_type)+") :","snopes")
                    continue

        # SAVE DATASET
        print("salvou")
        dataset.to_csv(cwd+"/snopes.csv", sep='\t', header=header, index=False)

        utils.update_last_saved_page(num_pages-pagenumber,"snopes")

        #KILLS EVERY CHROME PROCESS (Selenium was not handling browsers effectivelly)
        PROCNAME = "chrome"
        for proc in psutil.process_iter():
                # check whether the process name matches
                    if proc.name() == PROCNAME:
                                proc.kill()
