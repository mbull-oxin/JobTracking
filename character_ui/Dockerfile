FROM python:3.11
COPY ./code/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt && rm -f /requirements.txt
WORKDIR /app
ADD ./code /app/
