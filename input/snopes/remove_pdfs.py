import ast
import pandas as pd
import sys,os

cwd = os.path.abspath(__file__+"/..")


df = pd.read_csv(cwd+"/snopes.csv", sep="\t")
counter = 0
print(len(df))
for index, row in df.iterrows():
        x = ast.literal_eval(row['source_list'])
        x2 = [e for e in x if not e.lower().endswith(".pdf")]
        if len(x2) == 0:
            counter += 1
            df = df.drop([index])
print(len(df))
print(counter)
df.to_csv(cwd+"/snopes.csv", index=False, sep="\t")
