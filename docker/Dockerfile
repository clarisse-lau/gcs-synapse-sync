FROM ubuntu:20.04

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    python3.8 \
    python3-pip \
    openslide-tools \
    python3-openslide \
    curl

# Download and install gcloud package.
RUN curl https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz > /tmp/google-cloud-sdk.tar.gz
RUN mkdir -p /usr/local/gcloud \
  && tar -C /usr/local/gcloud -xvf /tmp/google-cloud-sdk.tar.gz \
  && /usr/local/gcloud/google-cloud-sdk/install.sh
ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin

COPY minerva_story.sh /usr/local/bin/minerva_story.sh
COPY save_exhibit_pyramid.py /usr/local/bin/save_exhibit_pyramid.py
COPY index.html /usr/local/bin/index.html

WORKDIR /tmp
COPY requirements.txt /tmp
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
RUN pip3 install --upgrade setuptools && pip3 install -r /tmp/requirements.txt

USER root
RUN /bin/bash -c 'chmod +x /usr/local/bin/minerva_story.sh'
CMD [ "/bin/sh", "/usr/local/bin/minerva_story.sh" ]
