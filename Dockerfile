# پایه: تصویر رسمی پایتون 3.11
FROM python:3.11-slim

# تنظیم دایرکتوری کاری داخل کانتینر
WORKDIR /app

# کپی فایل‌های وابستگی
COPY requirements.txt .

# نصب وابستگی‌ها
RUN pip install --no-cache-dir -r requirements.txt

# کپی کل کد پروژه به داخل کانتینر
COPY . .

# پورت مورد نظر (مثلاً 10000 یا پورتی که خودت استفاده می‌کنی)
EXPOSE 10000

# فرمان اجرای برنامه
CMD ["python", "main.py"]
