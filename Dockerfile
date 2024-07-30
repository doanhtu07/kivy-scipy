FROM ubuntu:22.04

# === Start working at /root ===

WORKDIR /root

# Install sudo

RUN apt update -y
RUN apt install -y sudo

# Target Android on Ubuntu 22.04

RUN sudo apt update -y
RUN sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

RUN sudo apt update -y
RUN sudo apt install -y autopoint
RUN pip3 install pipenv 

RUN echo 'export PATH="$PATH:~/.local/bin/"' >> ~/.bashrc

## Clone project

RUN mkdir BufferCapacity4
RUN git clone -b tudo --single-branch https://github.com/tonnuhongan999/BufferCapacity4.git ./BufferCapacity4

## Setup pyenv

RUN sudo apt update -y
RUN sudo apt install -y curl
RUN curl https://pyenv.run | bash

RUN echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
RUN echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
RUN echo 'eval "$(pyenv init -)"' >> ~/.bashrc

RUN echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
RUN echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile
RUN echo 'eval "$(pyenv init -)"' >> ~/.profile

## Setup locales for pipenv

RUN sudo apt update -y
RUN sudo apt install -y locales
RUN sudo locale-gen en_US.UTF-8
RUN echo 'export LANG="en_US.UTF-8"' >> ~/.profile
RUN echo 'export LC_ALL="en_US.UTF-8"' >> ~/.profile
RUN echo 'export LC_CTYPE="en_US.UTF-8"' >> ~/.profile

# Source

# https://stackoverflow.com/questions/55206227/why-bashrc-is-not-executed-when-run-docker-container
SHELL ["/bin/bash", "-l", "-c"]

# === Go to project ===

WORKDIR /root/BufferCapacity4

RUN git checkout tudo

RUN sudo apt update -y
RUN sudo apt install -y libbz2-dev libreadline-dev libsqlite3-dev liblzma-dev
RUN pyenv install 3.12
RUN pyenv global 3.12

RUN pipenv install
RUN pipenv install -d

RUN echo 'export ANDROID_HOME="$HOME/.android"' >> ~/.bashrc
RUN echo 'export LEGACY_NDK="$ANDROID_HOME/android-ndk-legacy"' >> ~/.bashrc

#RUN ["/bin/bash", "-c", "source $(pipenv --venv)/bin/activate && make"]
