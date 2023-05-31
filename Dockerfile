from python:3.10.0-buster

WORKDIR /

# This is done when you want to change the default shell in your image (and during build)
SHELL ["/bin/bash", "-c"]

COPY requirements.txt  ./
RUN pip install pip --upgrade && pip install -r requirements.txt

# Copy function code and change dir
ADD app ./app

WORKDIR app

# RUN python initial_run.py
ADD isnet-general-use.onnx /root/.u2net/

ADD start.sh .
RUN chmod +x ./start.sh

CMD [ "./start.sh" ]