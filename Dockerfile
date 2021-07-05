FROM python:latest

ENV VIRTUAL_ENV "/venv"
RUN python -m venv $VIRTUAL_ENV
ENV PATH "$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y ffmpeg opus-tools bpm-tools
RUN python -m pip install --upgrade pip
RUN python -m pip install wheel pyrogram tgCrypto
RUN python -m pip install pytgcalls ffmpeg-python psutil
RUN python -m pip install tgintegration youtube-dl youtube_search requests

RUN wget -q https://github.com/AsmSafone/RadioPlayer/archive/V2.0.tar.gz && tar xf V2.0.tar.gz && rm V2.0.tar.gz

WORKDIR /RadioPlayer-V2.0
CMD python3 main.py

# docker build -t tgcalls .
# docker run -it --rm --env-file ./envfile --name tgvc-userbot tgcalls
