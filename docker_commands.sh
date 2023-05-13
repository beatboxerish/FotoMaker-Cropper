#!/bin/sh
docker buildx build --platform=linux/amd64 -t ishannangia/cropper .
imageId=$(docker images | awk '{print $3}' | awk NR==2)
docker tag $imageId ishannangia/cropper:latest
docker push ishannangia/cropper:latest

