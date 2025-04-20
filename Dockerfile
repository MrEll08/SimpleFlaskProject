FROM python:3.11-slim
LABEL authors="max"

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

ENTRYPOINT ["sh", "-c", "python create_database.py && python app.py"]
