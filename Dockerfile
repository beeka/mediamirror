FROM alpine:latest

ADD *.py /var/opt/scripts/

RUN apk add --no-cache bash python3 py-mutagen flac lame && \
    rm -fr /var/cache/apk/*

ENV PATH=${PATH}:/var/opt/scripts/

WORKDIR /var/opt/source

VOLUME [ "/var/opt/source", "/var/opt/dest"  ]

ENTRYPOINT [ "/usr/bin/python3", "-tt", "/var/opt/scripts/mediamirror.py", "-s", "/var/opt/source/", "-d", "/var/opt/dest/" ]

# Default to pruning dead directories after the mirror
CMD [ "--prune" ]
