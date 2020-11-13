#Create a mirroring script
#Installed mutagen python library so that mediamirror.py / flac2mp3.py can be used. Needed to install pip first:
#	$ sudo easy_install pip
#	$ sudu pip install mutagen

#Dry-run it (after adding Volume_1 to the auto-mounts):
#	python -tt /Music/mediamirror.py -s /Music/ -d /mnt/Volume_1/music/mp3s/from_flac/ --prune -n
#The -n option shows what would happen. Run again without it to perform the mirror. Periodically run:
#/usr/bin/python -tt /var/opt/scripts/mediamirror.py -s /var/opt/source/ -d /var/opt/dest --prune | tee -a /var/opt/source//mediamirror.log

FROM alpine:latest

ADD *.py /var/opt/scripts/

RUN apk add --no-cache bash python py-mutagen flac lame && \
    rm -fr /var/cache/apk/*

ENV PATH=${PATH}:/var/opt/scripts/

WORKDIR /var/opt/source

VOLUME [ "/var/opt/source", "/var/opt/dest"  ]

#use ENTRYPOINT instead?
#CMD [ "/usr/bin/python", "-tt", "/var/opt/scripts/mediamirror.py", "-s", "/var/opt/source/", "-d", "/var/opt/dest", "--prune", "-n" ]
ENTRYPOINT [ "/usr/bin/python", "-tt", "/var/opt/scripts/mediamirror.py", "-s", "/var/opt/source/", "-d", "/var/opt/dest", "--prune" ]
