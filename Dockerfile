# use official Python image with size around 200 MB
FROM python:3.11-slim

# set working directory inside container
WORKDIR /app

COPY requirements.txt ./

# install dependencies with size around 1.2 GB
RUN pip install --no-cache-dir -r requirements.txt

# copy all files to container
COPY . .

CMD ["python", "-m", "ground_station.frontend.main_window"]
