FROM python:latest

ENV VIRTUAL_ENV "/venv"
RUN python -m venv $VIRTUAL_ENV
ENV PATH "$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y ffmpeg opus-tools bpm-tools
RUN python -m pip install --upgrade pip
RUN python -m pip install wheel Pyrogram TgCrypto psutil
RUN python -m pip install pytgcalls ffmpeg-python requests
RUN python -m pip install wget youtube-dl youtube_search youtube_search_python

RUN wget -q https://github.com/AsmSafone/RadioPlayer/archive/V3.0.tar.gz && tar xf V3.0.tar.gz && rm V3.0.tar.gz

WORKDIR /RadioPlayer-V3.0
CMD python3 main.py
