## myems-aggregation

Data Aggregation Service 

数据汇总服务

## Introduction

This service is a component of MyEMS. It aggregates normalized data up to multiple dimensions.

## Prerequisites

mysql-connector-python

python-decouple


## Quick Run for Development

```bash
cd myems/myems-aggregation
pip install -r requirements.txt
cp example.env .env
chmod +x run.sh
./run.sh
```

## Installation

### Option 1: Install myems-aggregation on Docker

In this section, you will install myems-aggregation on Docker.

* Copy source code to root directory

On Windows:
```bash
cp -r myems/myems-aggregation c:\
cd c:\myems-aggregation
```

On Linux:
```bash
cp -r myems/myems-aggregation /
cd /myems/myems-aggregation
```

* Duplicate example.env file as .env file and modify the .env file
Replace ~~127.0.0.1~~ with real **HOST** IP address.
```bash
cp example.env .env
```

* Build a Docker image
```bash
docker build -t myems/myems-aggregation .
```
* Run a Docker container
On Windows host, bind-mount the .env to the container: 
```bash
docker run -d -v c:\myems-aggregation\.env:/code/.env --restart always --name myems-aggregation myems/myems-aggregation
```
On Linux host, bind-mount the .env to the container:
```bash
docker run -d -p 8000:8000 -v /myems-aggregation/.env:/.env --restart always --name myems-aggregation myems/myems-aggregation
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
docker save --output myems-aggregation.tar myems/myems-aggregation
```
* Copy the tarball file to another computer, and then load image from tarball file
```bash
docker load --input .\myems-aggregation.tar
```

### Option 2: Online install myems-aggregation on Ubuntu Server with internet access

In this section, you will install myems-aggregation on Ubuntu Server with internet access.

```bash
cd ~
git clone https://github.com/MyEMS/myems.git
cd myems
git checkout master (or the latest release tag)
cd myems-aggregation
pip install -r requirements.txt
cp -r ~/myems/myems-aggregation /myems-aggregation
```
Copy exmaple.env file to .env and modify the .env file:
```bash
cp /myems-aggregation/example.env /myems-aggregation/.env
nano /myems-aggregation/.env
```
Setup systemd service:
```bash
cp myems-aggregation.service /lib/systemd/system/
```
Enable the service:
```bash
systemctl enable myems-aggregation.service
```
Start the service:
```bash
systemctl start myems-aggregation.service
```
Monitor the service:
```bash
systemctl status myems-aggregation.service
```
View the log:
```bash
cat /myems-aggregation.log
```

### Option 3: Offline install myems-aggregation on Ubuntu Server without internet access

In this section, you will install myems-aggregation on Ubuntu Server without internet access.

Download on any server with internet access:
```bash
cd ~/tools
wget https://cdn.mysql.com/archives/mysql-connector-python-8.0/mysql-connector-python-8.0.23.tar.gz
git clone https://github.com/henriquebastos/python-decouple.git
cd ~
git clone https://github.com/MyEMS/myems.git
```

Copy files to the server without internet access and install prerequisites:
```bash
cd ~/tools
tar xzf mysql-connector-python-8.0.23.tar.gz
cd ~/tools/mysql-connector-python-8.0.23
python3 setup.py install
cd ~/tools/python-decouple
python3 setup.py  install
```

Install myems-aggregation service:
```bash
cd ~/myems
git checkout master (or the latest release tag)
cp -r ~/myems/myems-aggregation /myems-aggregation
```
Copy exmaple.env file to .env and modify the .env file:
```bash
cp /myems-aggregation/example.env /myems-aggregation/.env
nano /myems-aggregation/.env
```
Setup systemd service:
```bash
cp myems-aggregation.service /lib/systemd/system/
```
Enable the service:
```bash
systemctl enable myems-aggregation.service
```
Start the service:
```bash
systemctl start myems-aggregation.service
```
Monitor the service:
```bash
systemctl status myems-aggregation.service
```
View the log:
```bash
cat /myems-aggregation.log
```

### References

[1]. https://myems.io

[2]. https://dev.mysql.com/doc/connector-python/en/

[3]. https://github.com/henriquebastos/python-decouple/
