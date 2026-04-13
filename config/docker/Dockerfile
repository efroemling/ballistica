# syntax=docker/dockerfile:1

# if provided it will make debug build
ARG cmake_build_type=Release
# whether to make GUI or headless build (defaults to headless)
ARG headless_build=1
# system to start with the build with
# currently will break for other images
ARG base_image=ubuntu:latest

#-------------------------------BUILDER--------------------------------
# Start with the base image
FROM ${base_image} AS builder

# Renew the args
ARG headless_build
ARG cmake_build_type

# Environment settings
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
ENV CMAKE_BUILD_TYPE=${cmake_build_type}
ENV HEADLESS_BUILD=${headless_build}

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/venv \
    apt-get update && \
    apt-get install -y software-properties-common &&\
    add-apt-repository ppa:deadsnakes/ppa &&\
    apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        clang \
        clang-format \
        cmake \
        curl \
        libglut-dev \
        libopenal-dev \
        libsdl2-dev \
        libvorbis-dev \
        make \
        python3-pip \
        python3.13-dev \
        python3.13-venv \
        rsync \
        zstd

# Copy source code
COPY ./ /ballistica

# Set the working directory
WORKDIR /ballistica

# Compile the application
RUN mkdir /ballistica_cmake && \
    if [ "$HEADLESS_BUILD" != "0" ]; then \
        make cmake-server-build && \
        mv build/cmake/*/ballisticakit_headless build/cmake/*/staged/dist; \
    else \
        make cmake-build && \
        mv build/cmake/*/ballisticakit build/cmake/*/staged/; \
    fi && \
    mv build/cmake/*/staged/* /ballistica_cmake

#-------------------------------RUNNER--------------------------------
# Create a new stage for the runtime environment
FROM ${base_image} AS runner

# Environment settings
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

# Renew the args
ARG headless_build
ENV HEADLESS_BUILD=${headless_build}
ARG cmake_build_type
LABEL BOMBSQUAD_BUILD_TYPE=${cmake_build_type}

# Install runtime dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y software-properties-common &&\
    add-apt-repository ppa:deadsnakes/ppa &&\
    apt-get update && \
    apt-get install -y \
        python3.13-dev && \
    if [ "$HEADLESS_BUILD" = "0" ]; then \
        apt-get install -y \
            libsdl2-dev \
            libvorbis-dev \
            libglut-dev \
            pulseaudio-utils \
            libopenal-dev; \
    fi && \
    apt-get clean && \
    python3.13 -c "import uuid; print(uuid.uuid4())" > /etc/machine-id

# Copy the compiled application from the builder stage
COPY --from=builder /ballistica_cmake \
                    /home/ubuntu/ballistica

# Set the working directory
WORKDIR /home/ubuntu/ballistica

RUN ln -s ballisticakit* run

# Expose the necessary port
EXPOSE 43210/udp

# Set the default command to run the application
CMD [ "./run" ]
