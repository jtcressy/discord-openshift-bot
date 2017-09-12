FROM python:3
RUN python3 -m pip install -U discord.py
RUN export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)"
RUN echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
RUN apt-get update -y && apt-get install google-cloud-sdk -y
RUN wget https://github.com/openshift/origin/releases/download/v3.6.0/openshift-origin-client-tools-v3.6.0-c4dd4cf-linux-64bit.tar.gz -O oc.tar.gz && tar -xzf oc.tar.gz --wildcards '*oc' --strip-components=1 && mv oc /usr/bin/oc && rm oc.tar.gz
WORKDIR /usr/src/app
VOLUME /data
COPY ./app /usr/src/app
CMD [ "python", "/usr/src/app/main.py"]
