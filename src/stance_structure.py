# encoding: utf-8
import pandas as pd
import os,sys
import math

stances_header = ["Headline","Body ID"]
body_header = ["Body ID","articleBody"]

cwd = os.path.abspath(os.path.dirname(sys.argv[0]))
parent_dir = '/'.join(cwd.split("/")[:-1])
stance_dir = parent_dir+"/eatiht/stance_class/"
tree_dir = cwd+"/fnc-1/tree_model"
tree_dir = cwd+"/teste"
dl_dir = cwd+"/fnc-1/deep_learning_model"

stance = pd.read_csv(stance_dir+"pred_stances.csv", sep='\t')
body = pd.read_csv(stance_dir+"pred_bodies.csv", sep='\t')

total = pd.concat([stance,body], axis=1, ignore_index=True) 
total = total.drop_duplicates()

print(len(stance))
print(len(body))
print(len(total))
stance = []
body = []

print(sys.argv[1])
for idx,elem in total.iterrows():
	stance.append([elem[0],elem[1]])
	body.append([elem[1],elem[3]])

print(len(stance))
print(len(body))
stance = pd.DataFrame(stance, columns=stances_header)
body = pd.DataFrame(body, columns=body_header)

#print(stance.head(2))
#print(body.head(2))

split = int(sys.argv[1])
n_splits = int(sys.argv[2])
bucket_sz = math.floor(len(stance)/n_splits)
print("stance splitting",split,n_splits,len(stance),bucket_sz)
end = (split+1)*bucket_sz if n_splits - split > 1 else len(stance)
stance = stance.iloc[split*bucket_sz:end]
body = body.iloc[split*bucket_sz:end]

#body.to_csv(tree_dir+"/test_bodies.csv", sep=',', header=body_header, index=False, encoding="utf-8")
#stance.to_csv(tree_dir+"/test_stances_unlabeled.csv", sep=',', header=stances_header, index=False, encoding="utf-8")

#body.to_csv(dl_dir+"/test_bodies.csv", sep=',', header=body_header, index=False, encoding="utf-8")
#stance.to_csv(dl_dir+"/test_stances_unlabeled.csv", sep=',', header=stances_header, index=False, encoding="utf-8")
