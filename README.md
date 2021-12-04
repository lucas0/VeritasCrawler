## Repo containing the code used to crawl news agencies for the Veritas Dataset

### 1)install dependencies:

    python3 -m pip install -r requirements.txt
    python2 -m pip install -r requirements_python2.txt

### 2)install [boilerpipe](https://github.com/misja/python-boilerpipe):

    python /eathit/python-boilerpipe/setup.py install
    
The crawler for each agency is under `/input/<agency_name>`

---

Please cite the published articles related to this work:

Azevedo, Lucas, et al. "LUX (Linguistic aspects Under eXamination): Discourse Analysis for Automatic Fake News Classification." Findings of the Association for Computational Linguistics: ACL-IJCNLP 2021. 2021.

    @inproceedings{azevedo2021lux,
      title={LUX (Linguistic aspects Under eXamination): Discourse Analysis for Automatic Fake News Classification},
      author={Azevedo, Lucas and d’Aquin, Mathieu and Davis, Brian and Zarrouk, Manel},
      booktitle={Findings of the Association for Computational Linguistics: ACL-IJCNLP 2021},
      pages={41--56},
      year={2021}
    }

Azevedo, Lucas, and Mohamed Moustafa. "Veritas annotator: Discovering the origin of a rumour." Proceedings of the Second Workshop on Fact Extraction and VERification (FEVER). 2019.

    @inproceedings{azevedo2019veritas,
      title={Veritas annotator: Discovering the origin of a rumour},
      author={Azevedo, Lucas and Moustafa, Mohamed},
      booktitle={Proceedings of the Second Workshop on Fact Extraction and VERification (FEVER)},
      pages={90--98},
      year={2019}
    }

Azevedo, Lucas. "Truth or lie: Automatically fact checking news." Companion Proceedings of the The Web Conference 2018. 2018.

    @inproceedings{azevedo2018truth,
      title={Truth or lie: Automatically fact checking news},
      author={Azevedo, Lucas},
      booktitle={Companion Proceedings of the The Web Conference 2018},
      pages={807--811},
      year={2018}
    }
