#!/bin/bash
echo "Pulling model from s3"
bucket=$1
tag=$2
model=$tag
repo_url=$3
mkdir -p models/$model
aws s3 cp s3://$bucket/$model models/$model --recursive
echo "Build docker image"
nvidia-docker build --no-cache -t vc:$tag --build-arg MODEL=models/$model .
echo "Happy counting 🚗"
echo "Pushing model to ECR"
docker tag vc:$tag $repo_url:$tag
docker push $repo_url:$tag