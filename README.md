## Repo containing the code used to crawl news agencies for the [Veritas Dataset](https://github.com/lucas0/VeritasCorpus)

### 1)install dependencies:

    python3 -m pip install -r requirements.txt
    python2 -m pip install -r requirements_python2.txt

### 2)install [boilerpipe](https://github.com/misja/python-boilerpipe):

    python /eathit/python-boilerpipe/setup.py install
    
The crawler for each agency is under `/input/<agency_name>`

Please cite the following article if you use **VeritasCrawler**

    Azevedo, Lucas, and Mohamed Moustafa. "Veritas annotator: Discovering the origin of a rumour." 
    Proceedings of the Second Workshop on Fact Extraction and VERification (FEVER). 
    Association for Computational Linguistics (ACL), 2019.
