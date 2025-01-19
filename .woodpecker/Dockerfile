FROM python:3.12
RUN apt update && apt -y upgrade && apt -y --no-install-recommends install libopenal-dev libsdl2-dev libvorbis-dev cmake clang-format rsync zip
RUN pip install --upgrade pip
COPY config/requirements.txt ballistica_requirements.txt
RUN pip install -r ballistica_requirements.txt
