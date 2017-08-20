import sys, os, subprocess, asyncio, discord
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from discord.ext import commands

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
    if len(args) > 0 and args[0] == "!oc":
        if args[1] == "login":
            if isinstance(message.channel, discord.PrivateChannel):
                if len(args) == 3:
                    if args[2] == "download":
                        #send kubeconfig file to channel
                        kubeconfigpath = os.path.join(oc_config_folder, message.author.id)
                        try:
                            file = open(kubeconfigpath, "rb")
                            await client.send_file(message.channel, file, filename="kubeconfig", content="Here is your kubeconfig file!")
                            file.close()
                            return
                        except FileNotFoundError as err:
                            await client.send_message(message.channel, "Your kubeconfig file was not found or does not exist. Details: " + str(err))
                            return
                    if args[2] == "upload" and len(message.attachments) == 1:
                        if message.attachments[0]['filename'] == "kubeconfig":
                            # save file in oc_config_folder + message.author.id
                            kubeconfigpath = os.path.join(oc_config_folder, message.author.id)
                            os.makedirs(os.path.dirname(kubeconfigpath), exist_ok=True)
                            with open(kubeconfigpath, 'ab') as f:
                                req = Request(message.attachments[0]['url'], headers={'User-Agent': 'Mozilla/5.0'})
                                with urlopen(req) as url:
                                    f.write(url.read())
                        else:
                            await client.send_message(message.channel, "To use a custom kubeconfig file, attach your kubeconfig with the exact file name of ``kubeconfig`` with the message ``!oc login upload``")
                    else:
                        octoken = args[2]
                        await client.send_message(message.channel, "```" + execute("oc " + oc_config_arg + message.author.id + " login --token " + octoken + " " + oc_server_fqdn) + "```")
                elif len(args) > 3:
                    octoken = args[2]
                    ocurl = args[3]
                    await client.send_message(message.channel, "```" + execute("oc " + oc_config_args + message.author.id + " login --token " + octoken + " " + ocurl) + "```")
                else:
                    await client.send_message(message.channel, "You need to supply a token with ``!oc login <token>`` by requesting one from https://" + oc_server_fqdn + "/oauth/token/request")
                    await client.send_message(message.channel, "To use a custom kubeconfig file, attach your kubeconfig with the exact file name of ``kubeconfig`` with the message ``!oc login upload``")
                    await client.send_message(message.channel, "You can also download your current kubeconfig with ``!oc login download``")
            else:
                await client.send_message(message.author, "You cannot login to OpenShift tools using a public channel. Send me a private message with ``!oc login <token>`` instead.")
                await client.send_message(message.author, "You need to supply a token with ``!oc login <token>`` by requesting one from https://" + oc_server_fqdn + "/oauth/token/request")
                await client.delete_message(message)
        else:
            output = execute("oc " + oc_config_arg + message.author.id + " " + " ".join(args[1:]))
            if len(output) > 1000:
                n = 1000 #send 1900 characters at a time
                [await client.send_message(message.author, "```" + "".join(output[i:i+n])  + "```") for i in range(0, len(output), n)]
            else:
                await client.send_message(message.channel, "```" + output + "```" if isinstance(message.channel, discord.PrivateChannel) else message.author.mention + "```" + output + "```")
    elif isinstance(message.channel, discord.PrivateChannel) and message.author != client.user:
        await client.send_message(message.channel, renderhelp("general"))
def execute(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, err = p.communicate()
    return output.decode('utf-8')

def renderhelp(key):
    return "help not yet implemented"

client.run(discord_api_token)