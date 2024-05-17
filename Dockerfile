# Start with the base image
FROM ubuntu:24.04 AS builder

ENV LANG en_US.utf8
ENV LANGUAGE=en_US

# Install build dependencies
RUN DEBIAN_FRONTEND=noninteractive \
    apt-get update -y && \
    apt-get install -y \
        python3.12-dev \
        python3.12-venv \
        python3-pip \
        libsdl2-dev \
        libvorbisfile3 \
        freeglut3-dev \
        libopenal-dev \
        make \
        curl \
        rsync \
        clang-format \
        cmake \
        libvorbis-dev

# Copy source code
COPY ./ /home/ubuntu/ballistica

WORKDIR /home/ubuntu/ballistica

# Compile the application
RUN ./do_stuff 

# Optionally, clean up the build dependencies and any temporary files to reduce image size
# This step depends on how './do_stuff compile' works and if it generates any temporary files
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/*

# Create a new stage for the runtime environment
FROM ubuntu:24.04

ENV LANG en_US.utf8
ENV LANGUAGE=en_US

WORKDIR /home/ubuntu/ballistica

# Install runtime dependencies
RUN DEBIAN_FRONTEND=noninteractive \
    apt-get update -y && \
    apt-get install -y \
        python3.12-venv \
        python3-pip \
        libsdl2-dev \
        libvorbisfile3 \
        freeglut3-dev \
        libopenal1 \
        curl

# Copy the compiled application from the builder stage
COPY --from=builder /home/ubuntu/ballistica/build/cmake/server-debug/staged/ /home/ubuntu/ballistica

ARG BOMBSQUAD_VERSION=N/A
LABEL bombsquad_version=${BOMBSQUAD_VERSION}

# Expose the necessary port
EXPOSE 43210/udp

# Set the default command to run the application
CMD [ "./ballisticakit_server" ]
