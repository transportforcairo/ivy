FROM nvidia/cuda:10.2-cudnn7-devel

LABEL Author="Transport for Cairo"
ARG MODEL
# Install Python
RUN apt-get -y update &&\
    apt-get install -y software-properties-common && \
    add-apt-repository universe && \
    apt-get install -y git unzip python3.7 python3-pip wget pkg-config h264enc \
    libsm6 libxext6 libxrender-dev


RUN mkdir /code
WORKDIR /code
# Copy code 
COPY . .
RUN mkdir -p videos
RUN mkdir -p data/detectors
# Install required libraries for Ivy
RUN pip3 install --upgrade pip && pip install -r requirements.txt && \
    pip install opencv-python opencv-contrib-python && \
    GPU=1 pip install yolo34py yolo34py-gpu
# Copy base env
RUN mv .env.base .env
# Copy models data
RUN cp -r ${MODEL}/* data/detectors/ && rm -rf models/
ENTRYPOINT ["python3", "-m", "start"]