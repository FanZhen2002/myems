# myems-cleaning
MyEMS Cleaning Service 

MyEMS 数据清洗服务

## Introduction

This service is a component of MyEMS. It cleans the historical data. 

## Prerequisites

mysql-connector-python

schedule

python-decouple

## Quick Run for Development
```bash
cd myems/myems-cleaning
pip install -r requirements.txt
cp example.env .env
chmod +x run.sh
./run.sh
```

## Installation

### Option 1: Install myems-cleaning on Docker

In this section, you will install myems-cleaning on Docker.

* Copy source code to root directory

On Windows:
```bash
cp -r myems/myems-cleaning c:\
cd c:\myems-cleaning
```

On Linux:
```bash
cp -r myems/myems-cleaning /
cd /myems-cleaning
```

* Duplicate example.env file as .env file and modify the .env file
Replace ~~127.0.0.1~~ with real **HOST** IP address.
```bash
cp example.env .env
```

* Build a Docker image
```bash
docker build -t myems/myems-cleaning .
```
* Run a Docker container
On Windows host, bind-mount the .env to the container:
```bash
docker run -d -v c:\myems-cleaning\.env:/code/.env --restart always --name myems-cleaning myems/myems-cleaning
```
On Linux host, bind-mount the .env to the container:
```bash
docker run -d -p 8000:8000 -v /myems-cleaning/.env:/.env --restart always --name myems-cleaning myems/myems-cleaning
```
* -d Run container in background and print container ID

* -v If you use -v or --volume to bind-mount a file or directory that does not yet exist on the Docker host, -v creates the endpoint for you. It is always created as a directory.

* --restart Restart policy to apply when a container exits

* --name Assign a name to the container

The absolute path before colon is for path on host  and that may vary on your system.
The absolute path after colon is for path on container and that CANNOT be changed.
By passing .env as bind-mount parameter, you can change the configuration values later.
If you changed .env file, restart the container to make the change effective.

If you want to immigrate the image to another computer,
* Export image to tarball file
```bash
docker save --output myems-cleaning.tar myems/myems-cleaning
```
* Copy the tarball file to another computer, and then load image from tarball file
```bash
docker load --input .\myems-cleaning.tar
```

### Option 2: Install myems-cleaning on Ubuntu Server (bare-metal or virtual machine)

In this section, you will install myems-cleaning on Ubuntu Server.

Download and install MySQL Connector:
```bash
cd ~/tools
wget https://cdn.mysql.com/archives/mysql-connector-python-8.0/mysql-connector-python-8.0.23.tar.gz
tar xzf mysql-connector-python-8.0.23.tar.gz
cd ~/tools/mysql-connector-python-8.0.23
python3 setup.py install
```

Download and install Schedule
```bash
cd ~/tools
git clone https://github.com/dbader/schedule.git
cd ~/tools/schedule
python3 setup.py install
```

Download and install Python Decouple
```bash
cd ~/tools
git clone https://github.com/henriquebastos/python-decouple.git
cd ~/tools/python-decouple
python3 setup.py  install
```

Install myems-cleaning service
```bash
cp -R myems/myems-cleaning /myems-cleaning
```
Copy file example.env to .env and edit the .env file:
```bash
cp /myems-cleaning/example.env /myems-cleaning/.env
nano /myems-cleaning/.env
```
Setup systemd service:
```bash
cp myems-cleaning.service /lib/systemd/system/
```
Enable the service:
```bash
systemctl enable myems-cleaning.service
```
Start the service:
```bash
systemctl start myems-cleaning.service
```
Monitor the service:
```bash
systemctl status myems-cleaning.service
```
View the log:
```bash
cat /myems-cleaning.log
```

### References

1.  https://myems.io
2.  https://dev.mysql.com/doc/connector-python/en/