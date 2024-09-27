# Released under the MIT License. See LICENSE for details.
#
"""General functionality related to docker builds."""

import subprocess


def _docker_build(
    image_name: str,
    dockerfile_dir: str,
    *,
    cmake_build_type: str | None = None,
    labels: dict[str, str] | None = None,
    platform: str | None = None,
    headless_build: bool | str | None = None,
) -> None:

    build_cmd = [
        'docker',
        'buildx',
        'build',
        '--tag',
        image_name,
        '--file',
        dockerfile_dir,
        '--load',
        '.',
    ]

    if cmake_build_type is not None:
        build_cmd = build_cmd + [
            '--build-arg',
            f'cmake_build_type={cmake_build_type}',
        ]
    if headless_build is not None:
        if headless_build:
            headless_build = '1'
        else:
            headless_build = '0'
        build_cmd = build_cmd + [
            '--build-arg',
            f'headless_build={headless_build}',
        ]
    if platform is not None:
        build_cmd = build_cmd + [
            '--platform',
            platform,
        ]
    if labels is not None:
        build_cmd = build_cmd + [
            f'--label={i}={labels[i]}' for i in labels.keys()
        ]
    subprocess.run(build_cmd, check=True)


def docker_build(
    platform: str | None = 'linux/amd64',
    headless_build: bool | str | None = None,
    build_type: str | None = None,
) -> None:
    """Build docker image.
    platform == 'linux/arm64' or platform == 'linux/amd64'"""
    from batools import version

    version_num, build_num = version.get_current_version()
    if headless_build is None:
        headless_build = True
    if build_type is None:
        build_type = 'Release'

    image_name = get_docker_image_name(
        headless_build=headless_build, build_type=build_type
    )

    config_file = 'config/docker/Dockerfile'

    print(
        f'Building docker image {image_name} '
        + f'version {version_num}:{build_num}'
    )

    _docker_build(
        image_name,
        config_file,
        labels={
            'bombsquad_version': version_num,
            'bombsquad_build': str(build_num),
        },
        platform=platform,
        headless_build=headless_build,
        cmake_build_type=build_type,
    )


def get_docker_image_name(headless_build: bool | str, build_type: str) -> str:
    """Get name of docker images in predefined format."""
    name = 'bombsquad'
    if headless_build:
        name += '_server'
    else:
        name += '_gui'
    if 'release' in build_type.lower():
        name += '_release'
    else:
        name += '_debug'
    return name


def docker_save_images() -> None:
    """Saves bombsquad images loaded into docker."""
    output = subprocess.run(
        ['docker', 'images'], capture_output=True, text=True, check=True
    )
    save_cmd = ['docker', 'save', '-o']
    # we expect this directory is already present from Makefile
    build_save_dir = 'build/docker/'

    img_name = get_docker_image_name(headless_build=True, build_type='Release')
    if img_name in output.stdout:
        subprocess.run(
            save_cmd + [build_save_dir + img_name + '_docker.tar', img_name],
            check=True,
        )

    img_name = get_docker_image_name(headless_build=True, build_type='Debug')
    if img_name in output.stdout:
        subprocess.run(
            save_cmd + [build_save_dir + img_name + '_docker.tar', img_name],
            check=True,
        )

    img_name = get_docker_image_name(headless_build=False, build_type='Release')
    if img_name in output.stdout:
        subprocess.run(
            save_cmd + [build_save_dir + img_name + '_docker.tar', img_name],
            check=True,
        )

    img_name = get_docker_image_name(headless_build=False, build_type='Debug')
    if img_name in output.stdout:
        subprocess.run(
            save_cmd + [build_save_dir + img_name + '_docker.tar', img_name],
            check=True,
        )


def docker_remove_images() -> None:
    """Remove the bombsquad images loaded in docker."""
    output = subprocess.run(
        ['docker', 'images'], capture_output=True, text=True, check=True
    )
    remove_cmd = [
        'docker',
        'rmi',
    ]

    img_name = get_docker_image_name(headless_build=True, build_type='Release')
    if img_name in output.stdout:
        subprocess.run(remove_cmd + [img_name], check=True)

    img_name = get_docker_image_name(headless_build=True, build_type='Debug')
    if img_name in output.stdout:
        subprocess.run(remove_cmd + [img_name], check=True)

    img_name = get_docker_image_name(headless_build=False, build_type='Release')
    if img_name in output.stdout:
        subprocess.run(remove_cmd + [img_name], check=True)

    img_name = get_docker_image_name(headless_build=False, build_type='Debug')
    if img_name in output.stdout:
        subprocess.run(remove_cmd + [img_name], check=True)
