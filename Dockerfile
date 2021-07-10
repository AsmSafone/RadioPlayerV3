FROM debian:latest

RUN apt update && apt upgrade -y
RUN apt install git curl python3-pip ffmpeg -y
RUN pip3 install -U pip
RUN cd /
RUN git clone -b V3.0 https://github.com/AsmSafone/RadioPlayer
RUN cd RadioPlayer
WORKDIR /RadioPlayer
RUN pip3 install -U -r requirements.txt
CMD python3 main.py
