FROM python:3.11-slim
WORKDIR /app
COPY . .
EXPOSE 8888
CMD ["python", "dashboard.py"]
