FROM python:3
RUN pip install selenium webdriver_manager prometheus_client pyyaml

ARG CHROME_VERSION="100.0.4896.60-1"

# Install ${CHROME_VERSION} stable release
RUN wget -O /tmp/chrome.deb https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_${CHROME_VERSION}_amd64.deb
RUN apt update
RUN apt install -y /tmp/chrome.deb
RUN rm /tmp/chrome.deb >/dev/null

ADD src/axa.py /usr/local/bin/axa

EXPOSE 8000/tcp