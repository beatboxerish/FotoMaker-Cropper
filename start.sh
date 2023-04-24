#!/bin/bash
echo "Container Started"

# Below is to ensure the stdout and stderr streams are sent straight to terminal (e.g. your container log)
# without being first buffered and that you can see the output of your application in real time.
export PYTHONUNBUFFERED=1

echo "starting api"
# nohup python app.py & python -u handler.py
python -u handler.py

