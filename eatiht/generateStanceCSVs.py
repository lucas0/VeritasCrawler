# encoding: utf-8
from threading import Timer
import time
import math
import ast
import json
import re
import random
import ssl
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import eventlet
eventlet.monkey_patch()
try:
    import urllib.request
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
    import urllib2
from langdetect import detect
from dateutil.parser import parse
import unicodedata
import pandas as pd
import numpy as np
import requests
import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import utils

cwd = os.path.abspath(os.path.dirname(sys.argv[0]))+"/stance_class"
dsd = os.path.abspath(os.path.dirname(sys.argv[0]))+"/datasets"

# emergent = pd.read_csv(cwd+'/emergent.csv', sep='\t')
datasets = ["snopes", "politifact", "factcheck", "tof"]
#datasets = ["test"]
snopes = pd.read_csv(dsd+'/snopes.csv', sep='\t')
# dataset = pd.read_csv(cwd+'/emergent.csv', sep='\t')

import csv
csv.field_size_limit(sys.maxsize)
with open(cwd+'/pred_bodies.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    linenumber = 1
    try:
        for row in reader:
            linenumber += 1
    except Exception as e:
        print (("Error line %d: %s | %s" % (linenumber, str(type(e)), e)))

pred_stances = pd.read_csv(cwd+'/pred_stances.csv', sep='\t')
pred_bodies = pd.read_csv(cwd+'/pred_bodies.csv', sep='\t')
stances_header = ["Headline","Body ID"]
body_header = ["Body ID", "articleBody", "oUrl", "oTitle", "oAuthor", "oSummary", "oKeywords", "oDate", "dataset"]

def isBodySaved(body_url):
        return (pred_bodies['oUrl'] == body_url).any()

def saveRow(claim, oUrl, oBody, oTitle, oAuthor, oSummary, oDate, oKeywords, dataset_name):
    print(oBody)
    size = pred_stances.shape[0]
    pred_stances.loc[size] = [claim.decode("utf-8") ,size]
    pred_bodies.loc[size] = [size, oBody.strip(), oUrl, oTitle, oAuthor, oSummary, oKeywords, oDate, dataset_name]

for dataset_name in datasets:
    dataset = pd.read_csv(dsd+'/'+dataset_name+'.csv', sep='\t')
    for (idx_c,e) in list(enumerate(dataset.values)):
        #print(">> Claim "+str(idx_c+1)+"/"+str(len(dataset))+ " being processed")
        #empty values are read as NaN, thus, floats.
        if isinstance(e[1], float):
            print("ERROR: No 'claim' value")
            continue
        claim = e[1].encode('utf-8').strip()
        source_list = ast.literal_eval(e[4])
        num_sources = len(source_list)
        num_done = len(pred_stances.loc[pred_stances['Headline'] == claim])
        if num_sources >= num_done:
            for (s_idx,oUrl) in enumerate(source_list):

                claim_bar ="["+str(idx_c+1)+"/"+str(len(dataset))+"] "
                source_bar = "["+str(s_idx+1)+"/"+str(len(source_list))+"] "
                print("\n> Claim "+claim_bar+"Source "+source_bar)

                if isBodySaved(oUrl):
                    print("source already saved")
                    continue

                content, error = utils.getContent(oUrl,dataset_name)

                if content is not None:
                    oBody, oTitle, oAuthor, oSummary, oDate, oKeywords = content
                    oBody = oBody.strip()

                    if oDate is None:
                        oDate = utils.getDate(oUrl)

                    print("> Body retrieved "+str(s_idx+1)+"/"+str(len(source_list))+" Date: "+str(oDate))
                    saveRow(claim, oUrl, oBody, oTitle, oAuthor, oSummary, oDate, oKeywords, dataset_name)

                elif error == "eat":
                    content, error = utils.getContent(oUrl,dataset_name, True)

                    if content is not None:
                        oBody, oTitle, oAuthor, oSummary, oDate, oKeywords = content
                        oBody = oBody.strip()

                        if oDate is None:
                            oDate = utils.getDate(oUrl)

                        print("> Body retrieved "+str(s_idx+1)+"/"+str(len(source_list))+" Date: "+str(oDate))
                        saveRow(claim, oUrl, oBody, oTitle, oAuthor, oSummary, oDate, oKeywords, dataset_name)

                # time.sleep(10)

        else:
            print("Claim Already Saved")

        if (idx_c % 10 == 0):
            print("Saving to file...")
            pred_stances.to_csv(cwd+"/pred_stances.csv", sep='\t', header=stances_header, index=False)
            pred_bodies.to_csv(cwd+"/pred_bodies.csv", sep='\t', header=body_header, index=False)

pred_stances.to_csv(cwd+"/pred_stances.csv", sep='\t', header=stances_header, index=False)
pred_bodies.to_csv(cwd+"/pred_bodies.csv", sep='\t', header=body_header, index=False)
