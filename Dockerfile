FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e ".[web]"
EXPOSE 8000
CMD ["uvicorn", "autocad_batch_commander.web.api:app", "--host", "0.0.0.0", "--port", "8000"]
