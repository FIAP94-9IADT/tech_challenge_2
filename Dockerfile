FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml requirements.txt README.md ./
COPY src ./src
COPY data ./data
RUN pip install --no-cache-dir .
ENTRYPOINT ["python", "-m", "hospital_routes.cli"]
CMD ["--input", "data/deliveries.json", "--output", "outputs"]
