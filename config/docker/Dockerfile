# if provided it will make debug build
ARG cmake_build_type=Release
# wether to make gui or headless build(defaults to headless)
ARG headless_build=1
# system to start with  the build with
# currently will break for other images
ARG base_image=ubuntu:24.04

#-------------------------------BUILDER--------------------------------
# Start with the base image
FROM ${base_image} AS builder

# Renew the arg
ARG headless_build
ARG cmake_build_type

ENV LANG en_US.utf8
ENV LANGUAGE=en_US
ENV DEBIAN_FRONTEND=noninteractive
ENV CMAKE_BUILD_TYPE=${cmake_build_type}
ENV HEADLESS_BUILD=${headless_build}

# Install build dependencies
RUN apt-get update -y && \
    apt-get install -y \
        python3.12-dev \
        python3.12-venv \
        python3-pip \
        libsdl2-dev \
        # libvorbisfile3 \
        libglut-dev \
        libopenal-dev \
        libvorbis-dev \
        make \
        curl \
        rsync \
        clang-format \
        cmake 
# Copy source code
COPY ./ /ballistica

WORKDIR /ballistica

# Compile the application
RUN mkdir /ballistica_cmake \
# ballisticakit_headless & ballisticakit in staged is a symlink
    && if [$HEADLESS_BUILD!=0]; then \
        make cmake-server-build \
        && mv build/cmake/*/ballisticakit_headless build/cmake/*/staged/dist ;\
    else \
        make cmake-build \
        && mv build/cmake/*/ballisticakit build/cmake/*/staged/ ;\
    fi \
    && mv build/cmake/*/staged/* /ballistica_cmake

#-------------------------------RUNNER--------------------------------
# Create a new stage for the runtime environment
FROM ${base_image}

ENV LANG en_US.utf8
ENV LANGUAGE=en_US
ENV DEBIAN_FRONTEND=noninteractive

# Renew the arg
ARG headless_build
ENV HEADLESS_BUILD=${headless_build}
ENV HEADLESS_BUILD=${headless_build}
ARG cmake_build_type

LABEL BOMBSQUAD_BUILD_TYPE=${cmake_build_type}

# Install runtime dependencies
RUN apt-get update -y && \
    apt-get install -y  \
        python3.12-dev \
    && if [$HEADLESS_BUILD!=0]; then \
        apt-get install -y \
            libsdl2-dev \
            libvorbis-dev \
            libglut-dev ;\
    fi \
    && rm -rf /var/lib/apt/lists/* \
    && python3.12 -c "import uuid;print(uuid.uuid4())">/etc/machine-id

# Copy the compiled application from the builder stage
COPY --from=builder /ballistica_cmake \
                    /home/ubuntu/ballistica

WORKDIR /home/ubuntu/ballistica

# Expose the necessary port
EXPOSE 43210/udp

# Set the default command to run the application
CMD [ "./ballisticakit_server" ]