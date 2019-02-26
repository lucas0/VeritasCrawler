# encoding: utf-8
import pandas as pd
import math
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import utils

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")
chrome_driver = os.path.abspath(os.path.dirname(sys.argv[0]))+"/chromedriver"

browser = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)

cwd = os.path.abspath(os.path.dirname(sys.argv[0]))

datasets_path = os.path.abspath(cwd+'/..')+"/eatiht/datasets/"
stance_path = os.path.abspath(cwd+'/..')+"/eatiht/stance_class/"
datasets = ['emergent', 'factcheck', 'politifact', 'snopes', 'tof']
datasets = ['factcheck']
#datasets = ['test']

content_header = ["page","claim","claim_label","tags","claim_source_domain","claim_source_url","date_check","source_body","date_fake"]
#factcheck = pd.read_csv(cwd+"/datasets/factcheck.csv", "r+")
#politifact = pd.read_csv(cwd+"/datasets/politifact.csv", "r+")
#snopes = pd.read_csv(cwd+"/datasets/snopes.csv", "r+")

def cleanText(text):
	if text[0] == text[-1] == "\n":
		text = text[1:-1]
	elif text[0] == text[-2] == "\n":
		text = text[1:-2]+text[-1]
	return text

#should be read only once
stance = pd.read_csv(cwd+"/results/result_stance.csv", sep=',')
bodies = pd.read_csv(stance_path+"pred_bodies.csv", sep='\t')

for dataset_name in datasets:

	if dataset_name == 'emergent':
		dataset = pd.read_csv(datasets_path+dataset_name+".csv", sep='\t')
		saved = pd.read_csv(datasets_path+dataset_name+"_content.csv", sep='\t')

		for idx,e in enumerate(dataset.values):
			claim = e[1]
			print(claim)

			if claim not in saved.claim.unique():
				body,error = utils.getContent(e[6], dataset_name)
				print(error)
				if body is not "":
					body = re.sub('\s+', " ",body).strip()
					date = utils.getDate(e[6])
					saved.loc[saved.shape[0]] = [e[0],claim,e[2],e[3],e[5],e[6],e[7],body,date]
					print("> Body retrieved < | > Date: "+date)
				elif error == "eat":
					print(">>Trying with archive")
				#try with archive:
					url = "http://archive.fo/"+e[6]
					row = None
					try:
						with eventlet.Timeout(25):
							browser.get(url)
							soup = BeautifulSoup(browser.page_source,"lxml")
							row = soup.find("div",{"id":"row0"})
					except:
						pass
					if row is None:
						print("> No log in archive.is")
					else:
						text = row.find("div",{"class":"TEXT-BLOCK"})
						a_link = text.a['href']
						body,error = utils.getContent(a_link,dataset_name)
						print(">>2 "+error+" 2<<")
						if body is not "":
							body = re.sub('\s+', " ",body).strip()
							date = utils.getDate(e[6])
							saved.loc[saved.shape[0]] = [e[0],claim,e[2],e[3],e[5],e[6],e[7],body,date]
							print("> Body retrieved < | > Date: "+date)
	
				if (idx % 10 == 0):
					print("Saving to file...")			
					saved.to_csv(datasets_path+dataset_name+"_content.csv", sep='\t', header=content_header, index=False)
		
			else:
				print("Claim Already Saved")
	
		print("Saving to file...")			
		saved.to_csv(datasets_path+dataset_name+"_content.csv", sep='\t', header=content_header, index=False)
	else:
		dataset = pd.read_csv(datasets_path+dataset_name+".csv", sep='\t')
		#print(dataset.shape)
		print("Starting dataset:", datasets_path+dataset_name+"_content.csv")
		dataset = dataset.dropna(subset=['claim'])
		#print(dataset.shape)
		#sys.exit(1)
		saved = pd.read_csv(datasets_path+dataset_name+"_content.csv", sep='\t')
		for (idx,claim) in enumerate(dataset.claim.unique()):
			if claim not in saved.claim.unique():
				s_claim = stance['Headline']
				d_claim = cleanText(claim.encode('utf-8').strip()).decode('utf-8')
				print(">>>>",d_claim,"<<<<>>>>")
				anySource = stance.loc[(s_claim == d_claim)]
				print(anySource)
				scoredSources = stance.loc[(s_claim == d_claim) & (stance['Stance'] == 'agree')]
				if len(scoredSources) == 0:
					print("erro1")
					continue
				maxAgreedIdx = scoredSources['Agree'].idxmax()
				if math.isnan(maxAgreedIdx):
					print("erro2")
					continue
				maxAgreed = scoredSources.loc[maxAgreedIdx]
				maxAgreedBodyID = maxAgreed['Body ID']
				bodyRow = bodies.loc[bodies['Body ID'] == int(maxAgreedBodyID)]	
				body = bodyRow['articleBody'].item()
				source_url = bodyRow['bodyURL'].item()
				source_domain = utils.get_url_domain(source_url)
				e = dataset.loc[dataset['claim'] == claim].values[0]
				date = bodyRow['BodyDate'].item()
				saved.loc[saved.shape[0]] = [e[0],claim,e[2],e[3],source_domain,source_url,e[7],body,date]
				
				if (idx % 10 == 0):
					print(dataset_name+" idx "+str(idx)+". Saving to file...")			
					saved.to_csv(datasets_path+dataset_name+"_content.csv", sep='\t', header=content_header, index=False)
		
			else:
				print("Claim Already Saved")
	
		print("Saving to file...")			
		saved.to_csv(datasets_path+dataset_name+"_content.csv", sep='\t', header=content_header, index=False)
