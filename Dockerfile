FROM nvidia/cuda:10.2-cudnn7-runtime

LABEL Author="Transport for Cairo"

# Install Python
RUN apt-get -y update &&\
    apt-get install -y software-properties-common && \
    add-apt-repository universe && \
    apt-get install -y git unzip python3.7 python3-pip wget pkg-config 

RUN pip3 install --upgrade pip
RUN mkdir /code
WORKDIR /code

RUN git clone --branch docker-prep https://github.com/transportforcairo/ivy.git ivy
WORKDIR /code/ivy
# numpy needs to be installed for yolo34-gpu
RUN pip install numpy
# Install required libraries for Ivy
RUN pip install -r requirements.txt
RUN pip install opencv-python==3.4.0.14 opencv-contrib-python==4.1.2.30
RUN GPU=1 pip install yolo34py
RUN apt-get install -y libsm6 libxext6 libxrender-dev

# Fetch YOLOv3 weights
RUN wget --load-cookies /tmp/cookies.txt \
    "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1DHWungo4hzQkYpM2-_5rpzDgy4zHzH7G' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1DHWungo4hzQkYpM2-_5rpzDgy4zHzH7G" \
    -O weights.zip && rm -rf /tmp/cookies.txt && \
    unzip weights.zip -d ./data  && \
    mv .env.tfc .env

ENTRYPOINT ["python3", "-m", "start"]