Build the image with:

cd C:\Users\Steven\Documents\docker\mediamirror
docker build -t mediamirror .

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