# discord-openshift-bot

This is a discord bot designed for interacting with an openshift (soon: vanilla kubernetes) cluster and performing commands on-par with the ``oc`` command from the openshift client tools.

This bot supports most functions of the ``oc`` command except for:
- ``!oc login``
    - Custom login options, can be viewed by typing ``!help login`` in a private message to the bot
- ``!oc create/apply``
    - Custom resource handling, you can provide URL's to .yaml/.json files or attach .yaml/.json files to a the command. More help via ``!help files``
- ``!oc attach``
    - Due to the limitations of Discord, you cannot currently attach to a container with an interactive console. 
 (you can also type ``!oc --help`` or ``!help`` in the chat and get a full help readout directly from the cli)

### Current working features:
- Bot forces login interactions through private messages (no tokens in public chats!)
- Bot saves a personal kubeconfig file for every unique user ID that uses the ``!oc login`` command (works regardless of nicknames)
- Upload your own kubeconfig file by attaching it to the ``!oc login`` command
    - This is how you connect to vanilla kubernetes clusters, which the ``oc`` command fully supports.
- Breaks up messages if longer than 1000 chars and sends output via private message to user (e.g. ``!oc describe pod <pod>`` will pm you with the deets)
- Takes API token and default API URL via environment variable (roadmap: commandline options)
- Upload a number of .yaml/.json files describing new resources and apply them by attaching the files to the ``!oc create`` or ``!oc apply`` commands
    - You can also specify a web address for the resources in the same command (e.g. ``!oc create -f http://path/to/resource.yaml``)
    - Specify a namespace/project by adding ``-n <namespace>`` to the end of your command.
- Download .yaml/.json files created with ``!oc export`` and ``!oc get <resource> <name> -o yaml|json``
    - The bot will generate a file and attach it to a response message for you to download through discord.

### Docker Container features:
- Bot optionally saves kubeconfigs in a persistent volume (default is /data/kubeconfigs) (kubeconfigs are destroyed on container restart otherwise)

### Untested:
- Unknown how well custom API servers are working. Intended use is ``!oc login <token> <fqdn/ip:port>``
- Plus many commands (assumed most to work)

### Environment Variables:
- ``DISCORD_API_TOKEN``
    - Token from the "App Bot User" section in the [Developer Applications](https://discordapp.com/developers/applications/me) section of discord's website
- ``OPENSHIFT_API_FQDN``
    - The FQDN (DNS name) or IP addres and port (``ip:port`` or ``fqdn:port``) that points to your cluster's API.
    
### Using this bot

You can run this locally using docker, or as an openshift deployment.

Docker example: ``docker run -e DISCORD_API_TOKEN=<your api token> -e OPENSHIFT_API_FQDN=<api server address and port> -v $(pwd):/data quay.io/jtcressy/discord-openshift-bot``

### Possible Improvements / Roadmap:
- Commandline options for api token/kubeconfig/API address

### Disclaimer
This was a fun side-project that I initially whipped up in one night, feel free to add to it via PR's or just yell at me for coding mistakes. It's going to have bugs and not always work correctly.
