import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import utils
import math
import pandas as pd

cwd = os.path.abspath(__file__+"/..")
datasets_dir = cwd+"/../eatiht/datasets"
tree_dir = cwd+"/fnc-1/tree_model"
stance_dir = cwd+"/../eatiht/stance_class"
results_dir = cwd+"/results"

pred_bodies = pd.read_csv(stance_dir+'/pred_bodies.csv', sep='\t')
pred_stance = pd.read_csv(stance_dir+'/pred_stances.csv', sep='\t')
result_stances = pd.read_csv(results_dir+'/result_stance.csv', sep=',')

#depending on the size of dataset returns the amount of samples needed for
#significant statistical representation, keeping 95% confidence and 5%error margin
def getSampleSize(dataset):
	l = len(dataset)
	x = (math.pow(1.96,2)*(0.7)*(0.3))/math.pow(0.05,2)
	sample_size = (l*x)/(x + l + 1)
	return math.floor(sample_size)

samples_header = ['page','claim','claim_label','tags','claim_source_domain','claim_source_url','date_check','source_body','date_fake','dataset']
samples = pd.DataFrame()
datasets = ['snopes', 'politifact', 'factcheck', 'emergent']

for datasetname in datasets:
	dataset = pd.read_csv(datasets_dir+"/"+datasetname+"_content.csv", sep="\t").sample(frac=1, random_state=123)
	datasetfile = cwd+"/samples/sample_"+datasetname+".csv"
	sampleSize = getSampleSize(dataset)
	#dataset_sample = dataset.head(sampleSize)
	dataset_sample = dataset.head(25)
	dataset_sample.insert(len(dataset_sample.columns), 'dataset', datasetname)

	utils.removeFile(datasetfile)
	dataset_sample.to_csv(datasetfile, sep='\t', header=samples_header, index=False)

	samples = pd.concat([samples, dataset_sample], ignore_index=True)

samplesFile = cwd+"/samples/samples.csv"
utils.removeFile(samplesFile)
samples.to_csv(samplesFile, sep='\t', header=samples_header, index=False)
