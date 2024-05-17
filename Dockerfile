ARG cmake_build_type=Release
ARG base_image=ubuntu:24.04

# Start with the base image
FROM ${base_image} AS builder

ENV LANG en_US.utf8
ENV LANGUAGE=en_US

# Renew the arg
ARG cmake_build_type

ENV CMAKE_BUILD_TYPE=${cmake_build_type}

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
RUN rm -rf .venv tools/pcommand
RUN make cmake-server-build

# Create a new stage for the runtime environment
FROM ${base_image}

# Renew the arg
ARG cmake_build_type

ENV LANG en_US.utf8
ENV LANGUAGE=en_US

WORKDIR /home/ubuntu/ballistica

ARG bombsquad_version=N/A
LABEL BOMBSQUAD_VERSION=${bombsquad_version}

# Install runtime dependencies
RUN DEBIAN_FRONTEND=noninteractive \
    apt-get update -y && \
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
