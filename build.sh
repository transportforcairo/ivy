#!/bin/bash
echo "Pulling model from s3"
tag=$3
model=$2/$tag
mkdir -p $model
aws s3 cp s3://project-sea-cv-models/$model models/$model --recursive
echo "Build docker image"
nvidia-docker build -t --build-args MODEL=models/$model vc:$tag
echo "Happy counting 🚗"