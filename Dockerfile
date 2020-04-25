FROM python:3.7 as app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY Pipfile Pipfile.lock /code/

RUN pip install pipenv && pipenv install --system
RUN apt-get update && apt-get install -y netcat



RUN addgroup --system app && adduser --system --ingroup app app

COPY ./docker-entrypoint.sh /code/docker-entrypoint.sh

COPY . /code/

#RUN chown -R app:app .
#
#USER app

#ENTRYPOINT ["sh", "./docker-entrypoint.sh"]