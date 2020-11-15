Build the image with:

	docker build -t mediamirror .

A quick sanity check:

	docker run --rm mediamirror

Then one of:

docker run -it --volume /share/Public/music:/var/opt/source --volume /share/Public/music.mp3s/mp3s/from_flac:/var/opt/dest mediamirror 
docker run --name mediamirror --rm -it --volume /share/Public/music:/var/opt/source --volume /share/Public/music.mp3s/mp3s/from_flac:/var/opt/dest mediamirror 

docker run -it --volume //W/music:/var/opt/source --volume //W/music.mp3s/mp3s/from_flac:/var/opt/dest mediamirror 
docker run --name mediamirror --rm -it --volume //W/music:/var/opt/source --volume //W/music.mp3s/mp3s/from_flac:/var/opt/dest mediamirror

Delete the instance with: docker rm mediamirror
Delete the image with: docker rmi mediamirror

scripts are in /var/opt/scripts but also on the path, so python -tt /var/opt/scripts/mediamirror.py -s /var/opt/source/ -d /var/opt/dest/ --prune -n


#docker build -t mediamirror .
#docker run -d --name container_name image_name


Run a shell to debug:

	docker run -it --rm --entrypoint /bin/ash mediamirror
