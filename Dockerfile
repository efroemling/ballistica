FROM ubuntu:24.04

ENV LANG en_US.utf8

ENV LANGUAGE=en_US

RUN DEBIAN_FRONTEND=noninteractive \
    apt-get update -y && \
    apt-get install -y \
        python3.12-dev \
        python3.12-venv \
        libsdl2-dev \
        libvorbisfile3 \
        freeglut3-dev \
        libopenal-dev \
        make

ARG BOMBSQUAD_VERSION=N/A

# WORKDIR /home/ubuntu/

COPY ./ ./ballistica

WORKDIR /ballistica

LABEL bombsquad_version=${BOMBSQUAD_VERSION}

CMD [ "./do_stuff" ]

# ENTRYPOINT ["./do_stuff"]

# CMD [ "make" ]

# this does not port forward locally
# its just a hint for user which port to forward
EXPOSE 43210/udp

# Clean up
# RUN apt-get clean && \
#     rm -rf /var/lib/apt/lists/* /tmp/*