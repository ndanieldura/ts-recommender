FROM python:3

RUN pip install --upgrade pip 

RUN mkdir /app

WORKDIR /app  

ADD . . 

RUN pip install -r requirements.txt 

CMD ["python3", "app.py"]