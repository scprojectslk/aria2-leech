#!/bin/bash
apt-get update -y
apt-get install aria2 -y

python3 bot.py
