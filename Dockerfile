FROM python:3.7-alpine

RUN apk add gcc libc-dev make git libffi-dev openssl-dev python3-dev libxml2-dev libxslt-dev

ADD main.py devices.py requirements.txt ./
RUN pip install -r requirements.txt
CMD [ "python", "-u", "main.py"]

