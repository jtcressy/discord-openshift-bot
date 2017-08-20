FROM python:3
RUN python3 -m pip install -U discord.py
RUN wget https://github.com/openshift/origin/releases/download/v3.6.0/openshift-origin-client-tools-v3.6.0-c4dd4cf-linux-64bit.tar.gz -O oc.tar.gz && tar -xzf oc.tar.gz --wildcards '*oc' --strip-components=1 && mv oc /usr/bin/oc && rm oc.tar.gz
WORKDIR /usr/src/app
VOLUME /data
COPY ./app /usr/src/app
CMD [ "python", "/usr/src/app/main.py"]