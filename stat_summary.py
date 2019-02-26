import sys, os
import pandas as pd

#set paths
cwd = os.path.abspath(os.path.dirname(sys.argv[0]))
datasets_path = os.path.abspath(cwd)+"/eatiht/datasets/"
stance_path = os.path.abspath(cwd)+"/eatiht/stance_class/"
path = cwd+"/src/fnc-1/deep_learning_model/"

#four initial datasets, with list of sources
emergent = pd.read_csv(datasets_path+"emergent.csv", sep="\t")
factcheck = pd.read_csv(datasets_path+"factcheck.csv", sep="\t")
politifact = pd.read_csv(datasets_path+"politifact.csv", sep="\t")
snopes = pd.read_csv(datasets_path+"snopes.csv", sep="\t")
print("Initial datasets sizes:\n")
print("Emergent: ",emergent.shape)
print("Factcheck: ",factcheck.shape)
print("Politifact: ",politifact.shape)
print("Snopes: ",snopes.shape)
#print("\nChecking for null entries:") 
#print(emergent.isnull().any())
#print(factcheck.isnull().any())
#print(politifact.isnull().any())
#print(snopes.isnull().any())

#generate file for stance classification (acquire the body of each link in the list)

db = pd.read_csv(stance_path+"pred_bodies.csv", sep="\t")
df = pd.read_csv(stance_path+"pred_stances.csv", sep="\t")
print("\nAfter acquiring bodies and concatenating:") 
print(len(df))
print(len(db))
#print("\nChecking for null entries:") 
#print(df.isnull().any())
#print(db.isnull().any())

#post stance classification
stance = pd.read_csv(cwd+"/src/results/result_stance.csv", sep=',')
print("\nResults size:")
print(stance.shape)
print("\nNot null results size:")
print(stance[stance.Agree.notnull()].shape)
print(stance['Body ID'].unique().shape)


print("\nUnique results size:")
print(stance['Headline'].unique().shape)

#final documents "*_content.c"
e = pd.read_csv(datasets_path+"emergent_content.csv", sep="\t")
f = pd.read_csv(datasets_path+"factcheck_content.csv", sep="\t")
p = pd.read_csv(datasets_path+"politifact_content.csv", sep="\t")
s = pd.read_csv(datasets_path+"snopes_content.csv", sep="\t")

print("\nFinal datasets sizes:")
print("Emergent: ",e.shape)
print("Factcheck: ",f.shape)
print("Politifact: ",p.shape)
print("Snopes: ",s.shape)
