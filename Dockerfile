FROM python:3.13
WORKDIR /home/app
ADD . .
RUN pip install -r requirements.txt
CMD uvicorn main:app --reload
