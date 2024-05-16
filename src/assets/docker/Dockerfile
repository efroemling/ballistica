FROM ubuntu:24.04

ENV LANG en_US.utf8
ENV LANGUAGE=en_US
ARG BOMBSQUAD_VERSION=N/A

ARG SOURCE_DIR=.

RUN DEBIAN_FRONTEND=noninteractive \
    apt-get update -y && \
    apt-get install -y \
        python3.12-dev \
        libsdl2-dev \
        libvorbisfile3 \
        freeglut3-dev \
        libopenal-dev

# Clean up
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/*

WORKDIR ${SOURCE_DIR}

COPY ${SOURCE_DIR} ./

LABEL bombsquad_version=$BOMBSQUAD_VERSION

CMD [ "./ballisticakit_server" ]

# this does not port forward locally
# its just a hint for user which port to forward
EXPOSE 43210/udp
