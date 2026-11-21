FROM python:3.12-slim

WORKDIR /app

# Cài đặt curl, nodejs, npm để Reflex biên dịch frontend
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Khởi tạo web assets
RUN reflex init

EXPOSE 3000 8001

CMD ["reflex", "run", "--env", "prod", "--frontend-port", "3000", "--backend-port", "8001"]
