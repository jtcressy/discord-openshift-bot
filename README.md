# discord-openshift-bot

This is a discord bot designed for interacting with an openshift (soon: vanilla kubernetes) cluster and performing commands on-par with the ``oc`` command from the openshift client tools.

With the exception of ``!oc login``, the ``!oc`` base command can be appended with anything the commandline version of ``oc`` supports. (you can also type ``!oc --help`` in the chat and get a full help readout directly from the cli)

### Current working features:
- Bot forces login interactions through private messages (no tokens in public chats!)
- Bot saves a personal kubeconfig file for every unique user ID that uses the ``!oc login`` command (works regardless of nicknames)
- Breaks up messages if longer than 1000 chars and sends output via private message to user (e.g. ``!oc describe pod <pod>`` will pm you with the deets)
- Takes API token and default API URL via environment variable (roadmap: commandline options)

### Docker Container features:
- Bot optionally saves kubeconfigs in a persistent volume (kubeconfigs are destroyed on container restart otherwise)

### Untested:
- Unknown how well custom API servers are working. Intended use is ``!oc login <token> <fqdn/ip:port>``
- Plus many commands (assumed most to work)

### Environment Variables:
- ``DISCORD_API_TOKEN``
    - Token from the "App Bot User" section in the [Developer Applications](https://discordapp.com/developers/applications/me) section of discord's website
- ``OPENSHIFT_API_FQDN``
    - The FQDN (DNS name) or IP addres and port (``ip:port`` or ``fqdn:port``) that points to your cluster's API.
    
### Possible Improvements / Roadmap:
- Support for a vanilla kubernetes cluster
    - Upload a premade kubeconfig file to use
- Commandline options for api token/kubeconfig/API address
- Upload .yaml file when creating/applying resources

### Disclaimer
This was a fun side-project that I initially whipped up in one night, feel free to add to it via PR's or just yell at me for coding mistakes. It's going to have bugs and not always work correctly.
