import os
GENERAL = "general"
LOGIN = "login"
FILES = "files"
def render(key=GENERAL):
    if key == GENERAL:
            return """
    General Help

    You can send commands to me starting with !oc, which are similar to the commands in the OpenShift Client Tools.
    Type ``!oc --help`` to see what commands are available.

    One difference is the ``!oc login`` command, which you can find out more about by typing ``!help login``

    File handling is enabled! Type ``!help files`` for more information.
            """
    elif key == LOGIN:
            return """
    Login Help

    You can supply a token with ``!oc login <token>`` by requesting one from https://""" + os.environ['OPENSHIFT_API_FQDN'] + """/oauth/token/request
    Specify a custom server with your token by typing ``!oc login <token> <server>`` 

    To use a custom kubeconfig file, attach your kubeconfig with the exact file name of ``kubeconfig`` with the message ``!oc login upload``
    NOTE: Your current kubeconfig will be replaced with your newly uploaded kubeconfig.
    You can also download your current kubeconfig with ``!oc login download``

            """
    elif key == FILES:
            return """
File Handling Help

File handling is enabled for ``!oc apply`` and ``!oc create``. All you have to do is attach your .yaml or .json files to the message. 
You can use URLs in addition to file attachments by using the ``-f`` flag like so:
```
!oc create -f http://path/to/some/resource -f http://path/to/another/resource
```
AND you *can* attach files to that same message. Attachments get processed before URLs.

Optionally define a namespace to create these resources in:
```
!oc create -f http://path/to/some/resource -n namespace1
```
Includes attachments.


Also, when you ``describe`` or ``get`` a resource with the flag ``-o yaml`` a .yaml file with the output will be attached to the reply.
"""
    