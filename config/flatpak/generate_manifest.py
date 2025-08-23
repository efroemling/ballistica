import hashlib


template = '''app-id: #{APP_ID}#
runtime: org.freedesktop.Platform
runtime-version: '24.08'
sdk: org.freedesktop.Sdk
command: bombsquad.sh
finish-args:
  - --share=network
  - --share=ipc
  - --socket=x11
  - --socket=pulseaudio
  - --device=dri
  - --filesystem=host

modules:
  - name: SDL2
    buildsystem: cmake
    builddir: true
    cleanup:
      - /bin
      - /include
      - /lib/pkgconfig
      - /lib/cmake
      - /share
      - '*.a'
    sources:
      - type: git
        url: https://github.com/libsdl-org/SDL
        tag: release-2.0.20

  - name: Python
    sources:
      - type: archive
        url: https://www.python.org/ftp/python/3.13.3/Python-3.13.3.tar.xz
        sha256: 40f868bcbdeb8149a3149580bb9bfd407b3321cd48f0be631af955ac92c0e041
    config-opts:
      - --prefix=${FLATPAK_DEST}
      - --enable-shared
      - --enable-optimizations
      - --with-computed-gotos
      - --with-lto
      - --enable-ipv6
      - --with-system-expat
      - --with-system-ffi
      - --with-system-libmpdec
      - --enable-loadable-sqlite-extensions
      - --without-ensurepip
    cleanup:
      - /bin
      - /include
      - /lib/pkgconfig
      - /share

  - name: BombSquad
    buildsystem: simple
    build-commands:
    - mkdir -p ${FLATPAK_DEST}/bin/BombSquad
    - tar --no-same-owner axf BombSquad.tar.gz
    - mv BombSquad_*/* ${FLATPAK_DEST}/bin/BombSquad
    - install -Dm755 bombsquad.sh ${FLATPAK_DEST}/bin/bombsquad.sh
    - install -Dm644 -t ${FLATPAK_DEST}/share/applications/ ${FLATPAK_ID}.desktop
    - install -Dm644 ${FLATPAK_ID}.png ${FLATPAK_DEST}/share/icons/hicolor/512x512/apps/${FLATPAK_ID}.png
    - install -Dm644 net.froemling.BombSquad.appdata.xml /app/share/metainfo/net.froemling.BombSquad.metainfo.xml

    sources:

    - type: file
      dest-filename: BombSquad.tar.gz
      url: https://files.ballistica.net/bombsquad/builds/BombSquad_Linux_x86_64_#{BOMBSQUAD_VERSION}#.tar.gz
      sha256: #{BOMBSQUAD_SHA256}#

    - type: file
      dest-filename: #{APP_ID}#.png
      url: https://files.ballistica.net/bombsquad/promo/BombSquadIcon512.png
      sha256: c950d1b62da2714b1ed1afc42244f7e192be23172c89b6fa3e6eaaca8e45a89a

    - type: file
      path: #{APP_ID}#.desktop

    - type: file
      path: #{APP_ID}#.appdata.xml

    - type: script
      dest-filename: bombsquad.sh
      commands:
        - cd /app/bin/BombSquad
        - exec ./bombsquad
'''

def generate():
    with open('BombSquad_Linux_x86_64_1.7.48.tar.gz', 'rb') as tarball:
        data = tarball.read()

    manifest = (template
               .replace('#{APP_ID}#', 'net.froemling.BombSquad')
               .replace('#{BOMBSQUAD_VERSION}#', '1.7.48')
               .replace('#{BOMBSQUAD_SIZE}#', str(len(data)))
               .replace('#{BOMBSQUAD_SHA256}#', hashlib.sha256(data).hexdigest())
              )

    with open('net.froemling.BombSquad.yml', 'w') as manifestfile:
        manifestfile.write(manifest)


if __name__ == '__main__':
    generate()
