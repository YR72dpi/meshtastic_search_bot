FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY bot.py .

COPY prompt/ ./prompt
COPY tool/ ./tool
COPY emergency/ ./emergency

RUN python ./emergency/download_aid.py \
    && python -c "from tool.Emergency import _build_index; _build_index()"

CMD ["python", "-u", "main.py"]
