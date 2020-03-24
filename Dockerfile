FROM nvidia/cuda:10.2-cudnn7-devel

LABEL Author="Transport for Cairo"
ARG MODEL
# Install Python
RUN apt-get -y update &&\
    apt-get install -y software-properties-common && \
    add-apt-repository universe && \
    apt-get install -y git unzip python3.7 python3-pip wget pkg-config \
    libsm6 libxext6 libxrender-dev


RUN mkdir /code
WORKDIR /code
# Copy code 
COPY . .
RUN mkdir videos
# Install required libraries for Ivy
RUN pip3 install --upgrade pip && pip install -r requirements.txt && \
    pip install opencv-python opencv-contrib-python && \
    GPU=1 pip install yolo34py yolo34py-gpu
# Fetch YOLOv3 weights
# RUN wget --load-cookies /tmp/cookies.txt \
#     "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1DHWungo4hzQkYpM2-_5rpzDgy4zHzH7G' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1DHWungo4hzQkYpM2-_5rpzDgy4zHzH7G" \
#     -O weights.zip && rm -rf /tmp/cookies.txt && \
#     unzip weights.zip -d ./data  && \

# Copy base env
RUN mv .env.base .env
# Copy models data
COPY ${MODEL} ./detectors
ENTRYPOINT ["python3", "-m", "start"]