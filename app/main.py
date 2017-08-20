import discord
from discord.ext import commands
import asyncio
import os
import subprocess

client = discord.Client()
oc_config_folder = "/data/kubeconfigs/"
oc_config_arg = "--config " + oc_config_folder
try:
    discord_api_token = os.environ['DISCORD_API_TOKEN']
except KeyError as err:
    print("ERROR: API token required for Discord API via env var: DISCORD_API_TOKEN \n Details: \n")
    print(err)

try:
    oc_server_fqdn = os.environ['OPENSHIFT_API_FQDN']
except KeyError as err:
    print("ERROR: No OpenShift API server defined via environment variable: OPENSHIFT_API_FQDN \n Details: \n")
    print(err)

try: 
    oc_server_port = os.environ['OPENSHIFT_API_PORT']
except KeyError as err:
    print("WARN: OPENSHIFT_API_PORT not defined. Details: \n")
    print(err)
    pass


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    args = message.content.split()
    if args[0] == "!oc":
        if args[1] == "login":
            if isinstance(message.channel, discord.PrivateChannel):
                if len(args) == 3:
                    octoken = args[2]
                    await client.send_message(message.channel, "```" + execute("oc " + oc_config_arg + message.author.id + " login --token " + octoken + " " + oc_server_fqdn) + "```")
                elif len(args) > 3:
                    octoken = args[2]
                    ocurl = args[3]
                    await client.send_message(message.channel, "```" + execute("oc " + oc_config_args + message.author.id + " login --token " + octoken + " " + ocurl) + "```")
                else:
                    await client.send_message(message.channel, "You need to supply a token with ``!oc login <token>`` by requesting one from https://" + oc_server_fqdn + "/oauth/token/request")
            else:
                await client.send_message(message.author, "You cannot login to OpenShift tools using a public channel. Send me a private message with ``!oc login <token>`` instead.")
                await client.send_message(message.author, "You need to supply a token with ``!oc login <token>`` by requesting one from https://" + oc_server_fqdn + ":" + oc_server_port + "/oauth/token/request")
                await client.delete_message(message)
        else:
            output = execute("oc " + oc_config_arg + message.author.id + " " + " ".join(args[1:]))
            if len(output) > 1000:
                n = 1000 #send 1900 characters at a time
                [await client.send_message(message.author, "```" + "".join(output[i:i+n])  + "```") for i in range(0, len(output), n)]
            else:
                await client.send_message(message.channel, "```" + output + "```" if isinstance(message.channel, discord.PrivateChannel) else message.author.mention + "```" + output + "```")

def execute(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, err = p.communicate()
    return output.decode('utf-8')

client.run(discord_api_token)