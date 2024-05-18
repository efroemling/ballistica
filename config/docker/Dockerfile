# if provided it will make debug build
ARG cmake_build_type=Release

# system to start with  the build with
# currently will break for non ubuntu system
ARG base_image=ubuntu:24.04

#-------------------------------BUILDER--------------------------------
# Start with the base image
FROM ${base_image} AS builder

# Renew the arg
ARG cmake_build_type

ENV LANG en_US.utf8
ENV LANGUAGE=en_US
ENV DEBIAN_FRONTEND=noninteractive
ENV CMAKE_BUILD_TYPE=${cmake_build_type}

# Install build dependencies
RUN apt-get update -y && \
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
RUN make cmake-server-build
RUN mkdir ./../ballistica_cmake_server
RUN mv build/cmake/* ./../ballistica_cmake_server

#-------------------------------RUNNER--------------------------------
# Create a new stage for the runtime environment
FROM ${base_image}

ENV LANG en_US.utf8
ENV LANGUAGE=en_US
ENV DEBIAN_FRONTEND=noninteractive

# Renew the arg
ARG cmake_build_type
LABEL BUILD_TYPE=${cmake_build_type}

ARG bombsquad_build=N/A
LABEL BOMBSQUAD_BUILD=${bombsquad_build}

ARG bombsquad_version=N/A
LABEL BOMBSQUAD_VERSION=${bombsquad_version}

# Install runtime dependencies
RUN apt-get update -y && \
    apt-get install -y  \
        python3.12-venv \
        python3-pip \
        libsdl2-dev \
        libvorbisfile3 \
        freeglut3-dev \
        libopenal1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the compiled application from the builder stage
COPY --from=builder /home/ubuntu/ballistica_cmake_server/*/staged \
                    /home/ubuntu/ballistica
# ballisticakit_headless in staged is a symlink
COPY --from=builder /home/ubuntu/ballistica_cmake_server/*/ballisticakit_headless \
                    /home/ubuntu/ballistica/dist

WORKDIR /home/ubuntu/ballistica

# Expose the necessary port
EXPOSE 43210/udp
EXPOSE 43210/tcp

# Set the default command to run the application
CMD [ "./ballisticakit_server" ]
