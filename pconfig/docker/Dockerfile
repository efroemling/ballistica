# syntax=docker/dockerfile:1

# if provided it will make debug build
ARG cmake_build_type=Release
# whether to make GUI or headless build (defaults to headless)
ARG headless_build=1
# system to start with the build with
# currently will break for other images
# (pinned to 26.04, the first LTS shipping python3.14, which the build
# requires exactly; see ballisticakit-cmake/CMakeLists.txt)
ARG base_image=ubuntu:26.04
# image the builder stage starts from: either the build-env stage
# below or a prebuilt copy of it (see batools.docker and
# .github/workflows/docker_build_env.yml, which publishes one to ghcr.io)
ARG build_env_image=build-env

#------------------------------BUILD-ENV-------------------------------
# Toolchain and libraries only; nothing here may depend on the source
# tree or on build args, so the result can be published and reused.
# The published image doubles as the dev container (.devcontainer/), so
# the few dev-only extras (git, pkg-config) live here too.
FROM ${base_image} AS build-env

# Environment settings
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
# (each stage gets its own apt cache id; a shared locked cache made the
# builder and runner apt steps wait on each other)
RUN --mount=type=cache,id=apt-builder,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=aptlib-builder,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        clang \
        clang-format \
        cmake \
        curl \
        git \
        libglut-dev \
        libopenal-dev \
        libpango1.0-dev \
        libsdl3-dev \
        libvorbis-dev \
        libzstd-dev \
        make \
        pkg-config \
        python3-pip \
        python3.14-dev \
        python3.14-venv \
        rsync \
        zstd

# Install uv (used by make env / make cmake-build for venv setup).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

#-------------------------------BUILDER--------------------------------
FROM ${build_env_image} AS builder

# Renew the args
ARG headless_build
ARG cmake_build_type

ENV CMAKE_BUILD_TYPE=${cmake_build_type}
ENV HEADLESS_BUILD=${headless_build}

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
RUN --mount=type=cache,id=apt-runner,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=aptlib-runner,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y \
        python3.14-dev && \
    if [ "$HEADLESS_BUILD" = "0" ]; then \
        apt-get install -y \
            libsdl3-dev \
            libvorbis-dev \
            libglut-dev \
            libpango1.0-dev \
            pulseaudio-utils \
            libopenal-dev; \
    fi && \
    apt-get clean && \
    python3.14 -c "import uuid; print(uuid.uuid4())" > /etc/machine-id

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
