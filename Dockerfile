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

# Create a new stage for the runtime environment
FROM ubuntu:24.04

ENV LANG en_US.utf8
ENV LANGUAGE=en_US

WORKDIR /home/ubuntu/ballistica

ARG BOMBSQUAD_VERSION=N/A
LABEL bombsquad_version=${BOMBSQUAD_VERSION}

# Copy apt cache from builder to avoid redownloading 
COPY --from=builder /var/cache/apt/ /var/cache/apt/
COPY --from=builder /var/lib/apt/lists/ /var/lib/apt/lists/

# Install runtime dependencies
RUN DEBIAN_FRONTEND=noninteractive \
    apt-get install -y  \
        python3.12-venv \
        python3-pip \
        libsdl2-dev \
        libvorbisfile3 \
        freeglut3-dev \
        libopenal1 \
        curl

# Copy the compiled application from the builder stage
COPY --from=builder /home/ubuntu/ballistica/build/cmake/server-debug/staged/ /home/ubuntu/ballistica
COPY --from=builder /home/ubuntu/ballistica/build/cmake/server-debug/ballisticakit_headless /home/ubuntu/ballistica/dist

# Expose the necessary port
EXPOSE 43210/udp

# Set the default command to run the application
CMD [ "./ballisticakit_server" ]
