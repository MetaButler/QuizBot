FROM python:3.12.6-slim

RUN useradd -m botuser
USER botuser

WORKDIR /app/

COPY requirements.txt /app/

RUN pip install --user --no-cache-dir --upgrade wheel pip

RUN pip install --user --no-cache-dir --upgrade -r requirements.txt

COPY . /app/

CMD ["python", "-m", "bot"]