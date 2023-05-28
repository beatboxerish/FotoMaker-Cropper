from python:3.10.0-buster

WORKDIR /

# This is done when you want to change the default shell in your image (and during build)
SHELL ["/bin/bash", "-c"]

COPY requirements.txt  ./
RUN pip install pip --upgrade && pip install -r requirements.txt

# Copy function code
ADD app.py ./
ADD initial_run.py ./
ADD handler.py ./
ADD s3_utils.py ./
ADD utils.py ./

# RUN python initial_run.py
ADD isnet-general-use.onnx /root/.u2net/

ADD start.sh .
RUN chmod +x ./start.sh

CMD [ "./start.sh" ]