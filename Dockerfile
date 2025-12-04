FROM python:3.11.14-slim

USER root

RUN apt-get update && \
    apt-get install -y build-essential 

COPY requirements.txt /tmp/requirements.txt

RUN pip install -r /tmp/requirements.txt
RUN rm -r /tmp

RUN groupadd -r appgroup && useradd --no-log-init -r -m -g appgroup appuser

WORKDIR /opt/app

COPY ./app .

RUN chown -R appuser:appgroup /opt/app

USER appuser

EXPOSE 8501

CMD ["streamlit", "run", "st_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]