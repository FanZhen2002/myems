FROM python:slim
WORKDIR /code

# todo: share upload folder with admin container on Docker
RUN mkdir -p /var/www/html/admin/upload

COPY . /code
RUN pip install -r requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
EXPOSE 8000
CMD ["gunicorn", "app:api", "-b", "0.0.0.0:8000", "--timeout", "600", "--workers=4"]