import os
import subprocess
from urllib.request import urlopen, Request

import discord
import openshiftbot.helptext as helptext

client = discord.Client()
oc_config_folder = "/data/kubeconfigs/"
oc_temp_folder = "/tmp/oc"
oc_config_arg = "--config " + oc_config_folder
try:
    discord_api_token = os.environ['DISCORD_API_TOKEN']
except KeyError as err:
    print("ERROR: API token required for Discord API via env var: DISCORD_API_TOKEN \n Details: \n", err)

try:
    oc_server_fqdn = os.environ['OPENSHIFT_API_FQDN']
except KeyError as err:
    print("ERROR: No OpenShift API server defined via environment variable: OPENSHIFT_API_FQDN \n Details: \n", err)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
async def on_message(message):
    args = message.content.split()
    print(message.content)
    if len(args) > 0 and args[0] == "!oc":
        if args[1] == "login":
            if isinstance(message.channel, discord.PrivateChannel):
                if len(args) == 3:
                    if args[2] == "download":
                        # send kubeconfig file to channel
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
                    await client.send_message(message.channel, "```" + execute("oc " + oc_config_arg + message.author.id + " login --token " + octoken + " " + ocurl) + "```")
                else:
                    await client.send_message(message.channel, helptext.render(helptext.LOGIN))
            else:
                await client.send_message(message.author, "You cannot login to OpenShift tools using a public channel. Send me a private message with ``!oc login <token>`` instead.")
                await client.send_message(message.author, helptext.render(helptext.LOGIN))
                await client.delete_message(message)
        elif args[1] == "create" or args[1] == "apply":
            output = ""
            tmp = await client.send_message(message.channel, "Creating Resources..." if isinstance(message.channel, discord.PrivateChannel) else message.author.mention + "Creating Resources...")
            if len(message.attachments) > 0:
                for attachment in message.attachments:
                    if attachment['filename'].find('.yaml') >= 0 or attachment['filename'].find('.json') >= 0:
                        file_ext = ".yaml" if attachment['filename'].find('.yaml') else ".json"
                        filepath = oc_temp_folder + "/" + message.author.id + "/" + attachment['id'] + file_ext
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        with open(filepath, 'ab') as f:
                            req = Request(attachment['url'], headers={'User-Agent': 'Mozilla/5.0'})
                            with urlopen(req) as url:
                                f.write(url.read())
                        if message.content.find('-n') >= 0:
                            output += execute("oc " + oc_config_arg + message.author.id + " " + args[1] + " -f " + filepath + " -n " + args[args.index("-n")+1])
                        else:
                            output += execute("oc " + oc_config_arg + message.author.id + " " + args[1] + " -f " + filepath)
            urls = [x for x in args if args[args.index(x)-1] == "-f"]
            for url in urls:
                if message.content.find('-n') >= 0:
                    output += execute("oc " + oc_config_arg + message.author.id + " " + args[1] + " -f " + url + " -n " + args[args.index("-n")+1])
                else:
                    output += execute("oc " + oc_config_arg + message.author.id + " " + args[1] + " -f " + url)
            if len(message.attachments) > 0 or len(urls) > 0:
                await client.edit_message(tmp, "```" + output + "```" if isinstance(message.channel, discord.PrivateChannel) else message.author.mention + "```" + output + "```")
            else:
                await client.delete_message(tmp)
                await client.send_message(message.author, "ERROR: Could not understand input. \n\n" + helptext.render(
                    helptext.FILES))
        elif args[1] == "get" and message.content.find('-o') >= 0: 
            filename = ""
            rtype = args[2]
            rname = args[3]
            filetype = ""
            if args[args.index('-o')+1] == "yaml":
                filetype = ".yaml"
            elif args[args.index('-o')+1] == "json":
                filetype = ".json"
            else:
                await std_send(message, execute("oc " + oc_config_arg + message.author.id + " " + " ".join(args[1:])))
                return
            filename = rname + "-" + rtype + filetype
            exportfilepath = os.path.join(oc_temp_folder, message.author.id + filename)
            os.makedirs(os.path.dirname(exportfilepath), exist_ok=True)
            execute("oc " + oc_config_arg + message.author.id + " " + " ".join(args[1:]) + " > " + exportfilepath)
            with open(exportfilepath, 'r') as f:
                await client.send_file(message.channel, f, filename=filename, content="Here are your exported resources!")
        elif args[1] == "export" and len(args) > 2:
            filename = ""
            if message.content.find('-l') >= 0:
                labels = [{x.split('=')[0]:x.split('=')[1]} for x in args if args[args.index(x)-1] == "-l"]
                for label in labels:
                    filename += list(label.keys())[0] + "-" + label[list(label.keys())[0]] + "_"
            if message.content.find('--as-template') >= 0:
                template_name = [x for x in args if args[args.index(x)].find('--as-template') >= 0]
                filename += template_name[0].split('=')[1] + "-template"
            filename += ".yaml"
            #send send exported .yaml file to channel
            exportfilepath = os.path.join(oc_temp_folder, message.author.id + filename + ".yaml")
            os.makedirs(os.path.dirname(exportfilepath), exist_ok=True)
            execute("oc " + oc_config_arg + message.author.id + " " + args[1] + " " + " ".join(args[2:]) + " > " + exportfilepath)
            with open(exportfilepath, 'r') as f:
                await client.send_file(message.channel, f, filename=filename, content="Here are your exported resources!")
        else:
            await std_send(message, execute("oc " + oc_config_arg + message.author.id + " " + " ".join(args[1:])))
    elif isinstance(message.channel, discord.PrivateChannel) and message.author != client.user:
        if len(args) > 0 and args[0] == "!help":
            await client.send_message(message.channel, helptext.render(args[1]))
        else:
            await client.send_message(message.channel, helptext.render())

async def std_send(message, output):
    if len(output) > 1000:
        n = 1000  # send 1900 characters at a time
        [await client.send_message(message.author, "```" + "".join(output[i:i+n]) + "```") for i in range(0, len(output), n)]
    else:
        await client.send_message(message.channel, "```" + output + "```" if isinstance(message.channel, discord.PrivateChannel) else message.author.mention + "```" + output + "```")


def execute(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, err = p.communicate()
    return output.decode('utf-8')


def main():
    client.run(discord_api_token)