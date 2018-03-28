FROM python:3.6

COPY . /app

RUN pip install -r /app/requirements.txt

WORKDIR /app
# ENTRYPOINT ['/app/awsiamreport.py']
