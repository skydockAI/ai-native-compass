FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app:create_app()
ENV PYTHONPATH=/app/src

RUN chmod +x entrypoint.sh

EXPOSE 5005

CMD ["./entrypoint.sh"]
