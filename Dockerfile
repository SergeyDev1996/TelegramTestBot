FROM python:3.9-slim-bullseye
ENV PYTHONPATH "${PYTHONPATH}:/app"
EXPOSE 80
WORKDIR /app
COPY . .
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt