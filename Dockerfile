FROM python:3.7

RUN mkdir /ecommerce-app

COPY requierments.txt /app/

WORKDIR /app

RUN pip install -r requierments.txt

COPY . /app/

EXPOSE 8000

# runs the production server
ENTRYPOINT ["python", "smart-pad/manage.py"]

CMD ["runserver", "0.0.0.0:8000"]