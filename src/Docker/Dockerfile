FROM python:2.7-alpine3.7

RUN apk add --update curl gcc g++ && rm -rf /var/cache/apk/*
RUN apk --no-cache --update-cache add gcc gfortran python-dev build-base wget freetype-dev libpng-dev openblas-dev
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h
CMD tail -f /dev/null


RUN pip install -U pip
RUN pip install numpy==1.14.3
RUN pip install hyperopt
RUN pip install twython
RUN pip install pandas
RUN pip install scikit-learn
RUN pip install scipy
RUN pip install nltk
RUN pip install --upgrade gensim


#CMD python usr/src/docker_setup.py; python usr/src/fnc-1/tree_model/generateFeatures.py
