FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    unzip \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1) \
    && wget -q -O - "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}" | { read VERSION; wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${VERSION}/chromedriver_linux64.zip"; } \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip

RUN pip3 install selenium
# COPY auto_accept_rides_prod.py /app/
# CMD ["python3", "auto_accept_rides_prod.py"]
COPY sandboxed_testing.py /app/
CMD ["python3", "sandboxed_testing.py"]