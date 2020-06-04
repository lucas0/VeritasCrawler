import pandas as pd
import os
import sys
 
filepath = sys.argv[0]
cwd = os.path.dirname(os.path.realpath(filepath))
crawling_path = os.path.abspath(cwd+'../../..')
e_path = crawling_path+"/eatiht/datasets/tof_e_content.csv"

tof_e = pd.read_csv(e_path, sep="\t")
tof = pd.read_csv(cwd+"/tof.csv", sep="\t")

print("tof_e_content.csv len:", len(tof_e),"\ntof.csv len:",len(tof),"\nsum of both:",len(tof_e)+len(tof))

