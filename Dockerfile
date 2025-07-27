# use official Python image with size around 200 MB
FROM python:3.11-slim

# set python env path
ENV PYTHONPATH=/app

# set working directory inside container
WORKDIR /app

# copy all files to container
COPY . /app

# install dependencies with size around 1.2 GB
RUN pip install --upgrade pip && \
    pip install -r requirements.txt


# EXPOSE 5000
CMD ["python", "./ground_station/frontend/main_window.py"]  # create bash script to initiate the application

# convert current pipeline to multistage to reduce the image size
