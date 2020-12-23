FROM python:3.7-slim as base
RUN apt-get update && apt-get install -y gcc build-essential libssl-dev libffi-dev python-dev
WORKDIR app
RUN python -m venv ./venv
ENV PATH="/app/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.7-slim as app
COPY --from=base /app/venv /app/venv
WORKDIR app
COPY main.py devices.py ./
ENV PATH="/app/venv/bin:$PATH"
CMD [ "python", "-u", "main.py"]

