import pandas as pd
import os

cwd = os.getcwd()

data_e = pd.read_csv(cwd+'/datasets/emergent_content.csv', sep='\t')
data_s = pd.read_csv(cwd+'/datasets/snopes_content.csv', sep='\t')
data_f = pd.read_csv(cwd+'/datasets/factcheck_content.csv', sep='\t')
data_p = pd.read_csv(cwd+'/datasets/politifact_content.csv', sep='\t')

data_crawled = pd.concat([data_e,data_s,data_f,data_p])


print("emergent: ",data_e.shape)
print("snopes: ",data_s.shape)
print("factcheck: ",data_f.shape)
print("politifact: ",data_p.shape)
print(data_crawled.shape)