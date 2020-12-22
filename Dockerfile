FROM python:3.7

COPY main.py devices.py requirements.txt ./
RUN pip install -r requirements.txt
CMD [ "python", "-u", "main.py"]

