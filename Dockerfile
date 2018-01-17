FROM python:3.6.4

WORKDIR /app
ADD . /app


ARG TOKEN
ARG MONGO_USER
ARG MONGO_PASS
ARG GROUPME_TOKEN
ARG SLACK_BOT_TOKEN
ARG GROUPME_BOT_ID

RUN pip install -r requirements.txt

# docker build --build-arg TOKEN=$TOKEN
ENV TOKEN=$TOKEN
ENV MONGO_USER=$MONGO_USER
ENV MONGO_PASS=$MONGO_PASS
ENV GROUPME_TOKEN=$GROUPME_TOKEN
ENV SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN
ENV GROUPME_BOT_ID=$GROUPME_BOT_ID

CMD [ "python", "./myDiscordBot.py" ]
