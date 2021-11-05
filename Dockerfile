FROM python:3.7

RUN mkdir /ecommerce-app

COPY requierments.txt /ecommerce-app/

WORKDIR /ecommerce-app

RUN pip install -r requierments.txt

COPY . /ecommerce-appg/