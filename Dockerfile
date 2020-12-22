FROM python:3.7-slim

COPY Pipfile Pipfile.lock ./
RUN pip install pipenv

ADD main.py devices.py
CMD [ "python", "-u", "main.py"]

