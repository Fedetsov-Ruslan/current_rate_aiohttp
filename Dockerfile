FROM python:3.12.2-slim-bullseye
WORKDIR /
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080

CMD ["python", "pars_valute.py"]