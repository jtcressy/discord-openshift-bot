build:
	sudo docker build -t docker-registry-default.cloud.jtcressy.net/jtcressy-net/discord-openshift-bot .

push:
	sudo docker push docker-registry-default.cloud.jtcressy.net/jtcressy-net/discord-openshift-bot
