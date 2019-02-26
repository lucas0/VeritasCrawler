import os,sys
cwd = os.path.abspath(os.path.dirname(sys.argv[0]))

def swapComment():
	with open(cwd+"/fnc-1/tree_model/TfidfFeatureGenerator.py", "r+") as f:
		lines = f.readlines()
		line1 = lines[122]
		line2 = lines[123]

	if line1[8] == "#":
		line1 = line1[0:8]+line1[9:]
		line2 = line2[0:8]+"#"+line2[8:]

	lines[122] = line1
	lines[123] = line2

	with open(cwd+"/fnc-1/tree_model/TfidfFeatureGenerator.py", "w+") as f:
		for line in lines:
			f.write(line)

swapComment()

