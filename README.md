## Repo containing the code used to crawl news agencies for the [Veritas Dataset](https://github.com/lucas0/VeritasCorpus)

### 1)install dependencies:

    python3 -m pip install -r requirements.txt
    python2 -m pip install -r requirements_python2.txt

### 2)install [boilerpipe](https://github.com/misja/python-boilerpipe):

    python /eathit/python-boilerpipe/setup.py install
    
The crawler for each agency is under `/input/<agency_name>`

## If you use this code, please cite the [following publication](https://www.aclweb.org/anthology/D19-6614/):

    @inproceedings{azevedo2019veritas,
      title={Veritas annotator: Discovering the origin of a rumour},
      author={Azevedo, Lucas and Moustafa, Mohamed},
      booktitle={Proceedings of the Second Workshop on Fact Extraction and VERification (FEVER)},
      year={2019},
      organization={Association for Computational Linguistics (ACL)}
    }
