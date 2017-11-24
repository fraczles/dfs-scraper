FROM python:3.6

MAINTAINER Alex Fraczak <fraczakalex@gmail.com>

RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code/

CMD python /code/scraper.py
