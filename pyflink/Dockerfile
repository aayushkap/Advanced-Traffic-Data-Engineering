FROM flink:1.18.0

# Install Python
RUN apt-get update -y && \
apt-get install -y python3 python3-pip python3-dev && \
rm -rf /var/lib/apt/lists/*

# Ensure python command points to python3
RUN ln -s /usr/bin/python3 /usr/bin/python

# Optional: Install any additional Python packages you need
# RUN pip3 install <additional-packages>

# In case that packages are downloaded manually
# COPY apache-flink*.tar.gz /
# RUN pip3 install /apache-flink-libraries*.tar.gz && pip3 install /apache-flink*.tar.gz

# install Java & updates
RUN apt-get update && \
    apt-get install -y openjdk-8-jdk && \
    apt-get install -y ant && \
    apt-get clean;

ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64

WORKDIR /opt/flink
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY download_libs.sh .
RUN chmod +x ./download_libs.sh && ./download_libs.sh

RUN rm -f /opt/flink/lib/flink-doris-connector-1.17-24.0.0.jar

# Remove if no automation
RUN apt-get update && apt-get install -y jq

RUN apt-get update && apt-get install -y openssh-server && \
    mkdir /var/run/sshd && \
    echo 'root:root' | chpasswd && \
    sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PermitEmptyPasswords no/PermitEmptyPasswords yes/' /etc/ssh/sshd_config && \
    echo "export VISIBLE=now" >> /etc/profile

# Expose SSH port
EXPOSE 22

COPY ./usr_jobs/ ./usr_jobs