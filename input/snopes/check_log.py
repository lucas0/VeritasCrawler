from itertools import groupby
import ast
import pandas as pd
import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '../..'))
import utils

filename = sys.argv[0]
cwd = os.path.abspath(filename+"/..")

log_path = cwd+"/logfile.txt"

with open(log_path, "r+") as f:
    lines = f.readlines()

for line in lines:
    if "NOT ENOUGH SOURCES (content type 6)" in line:
        print(line)

errors = [line.split(":")[0] for line in lines]
urls = [line.split(":")[-1] for line in lines]

results = {value: len(list(freq)) for value, freq in groupby(sorted(errors))}

no_verdict = [line for line in lines if line.startswith('NO VERDICT')]
sorted_results = sorted(results.items(), key=lambda kv: kv[1])
print(sorted_results)

print("Repeated URLS in log:",len(urls)-(len(set(urls))))

df = pd.read_csv(cwd+"/snopes.csv", sep='\t')
df_unique = pd.read_csv(cwd+"/snopes.csv", sep='\t').page.unique()
df = df.drop_duplicates(subset=['page'], keep='last')
df.to_csv(cwd+"/snopes.csv", sep='\t', index=False)

estimated_num_claims = utils.get_last_saved_page("snopes")*12

print("#errors in Log: ",len(lines))
print("#entries in snopes.csv: ",len(df))
print("#unique entries in snopes.csv: ",len(df_unique))
print("#estimated checked claims: ",estimated_num_claims)
