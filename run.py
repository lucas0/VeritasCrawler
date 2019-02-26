import time
import os
import subprocess
import pandas as pd
import argparse
import optparse
import utils
parser = optparse.OptionParser()

parser.add_option('-s', '--splits', action="store", dest="splits", help="number of splits on input data", default=10)
parser.add_option('-r', '--recrawl', action="store", dest="recrawl", help="boolena for recrawling", default=False)

options, args = parser.parse_args()

parser = argparse.ArgumentParser()
print(options.splits)
print(options.recrawl)

pwd = os.getcwd()

import sys

datasources = ['emergent','snopes','factcheck','politifact']
# fill up [datasource].csv files
if options.recrawl: 
	for datasource in datasources:
		reset = input("["+datasource+"]Do you want to recrawl: (1)All the pages (2)Not crawled pages (3) Nothing:\n")
		if reset == '1':
			utils.update_last_saved_page(0,datasource)	
		if reset == '3':
			continue
		subprocess.call(["python3",pwd+"/input/"+datasource+"/c_"+datasource+".py"])
		# copy [datasource].csv to /eathit/datasets
		subprocess.call(["cp",pwd+"/input/"+datasource+"/"+datasource+".csv",pwd+"/eatiht/datasets/"+datasource+".csv"])
		print("done with "+datasource)

	# call generate stance CSV to retrieve the bodies of every source link and create pred_bodies and pred_stances
	subprocess.call(["python3",pwd+"/eatiht/generateStanceCSVs.py"])

#reset the result_stance.csv
res_tot = pd.read_csv(pwd+"/src/results/result_stance.csv", sep=",")
res_tot = res_tot.iloc[0:0]
res_tot.to_csv(pwd+"/src/results/result_stance.csv", index=False)

#the dataset had to be split, therefore this loop:
for i in range(int(options.splits)):

	# organize files for stance_class
	subprocess.call("python3 "+pwd+"/src/stance_structure.py "+str(i)+" "+str(options.splits), shell=True)
	print("Split "+str(i)+": files ready for stance classification")
	
	# call clf.py
	subprocess.call(["python",pwd+"/src/fnc-1/deep_learning_model/clf.py"])
	print("Split "+str(i)+": done with clf.py")
	
	#paste deep results to tree 
	subprocess.call("cp "+pwd+"/src/fnc-1/deep_learning_model/deepoutput.csv "+pwd+"/src/fnc-1/tree_model/dosiblOutputFinal.csv", shell=True)
	print("Split "+str(i)+": deep results pasted to tree model.")
	
	# swap commented lines as instructed in fnc-1 README.md
	subprocess.call(["python3", pwd+"/src/comment2.py"])
	print("Split "+str(i)+": line 122 commented")
	
	# call generateFeatures.py
	subprocess.call(["python", pwd+"/src/fnc-1/tree_model/generateFeatures.py"])
	print("Split "+str(i)+": features generated")
	
	# swap commented lines as instructed in fnc-1 README.md
	subprocess.call(["python3", pwd+"/src/comment1.py"])
	print("Split "+str(i)+": line 121 commented")
	
	# call xgb_train_cvBOdyID.py
	subprocess.call(["python", pwd+"/src/fnc-1/tree_model/xgb_train_cvBodyId.py"])
	print("Split "+str(i)+": done with xgb.py")
	
	# call average.py
	subprocess.call(["python", pwd+"/src/fnc-1/tree_model/average.py"])
	print("Split "+str(i)+": done with average.py")
	
	#append results
	res = pd.read_csv(pwd+"/src/fnc-1/tree_model/averaged_2models_cor4.csv", sep=",")
	res_tot = pd.read_csv(pwd+"/src/results/result_stance.csv", sep=",")
	res_tot = pd.concat([res_tot, res], ignore_index=True)
	res.to_csv(pwd+"/src/results/result"+str(i)+".csv", index=False)
	res_tot.to_csv(pwd+"/src/results/result_stance.csv", index=False)
	
	# fill up [dataset]_content.csv files
	subprocess.call(["python3",pwd+"/src/populate_content_csvs.py"])
	print("Split "+str(i)+" done.")

# sample and analyze how good the source text is

# train and evaluate baseline models saving their results

# train and evaluate Lux saving their results

# display both results (hoping for an enhancement with Lux)

time.sleep(30)
