#!/bin/bash
now=$(date +%s)

sed -i "/## INJECT_PATCH_INSTRUCTION ##/c\RUN echo ${now}" tmos_image_patcher/Dockerfile
docker build -t tmos_image_patcher:latest tmos_image_patcher
git checkout tmos_image_patcher/Dockerfile

sed -i "/## INJECT_PATCH_INSTRUCTION ##/c\RUN echo ${now}" tmos_configdrive_builder/Dockerfile
docker build -t tmos_configdrive_builder:latest tmos_configdrive_builder
git checkout tmos_configdrive_builder/Dockerfile
