#!/bin/bash
cd /home/youngleba/beautybot
git pull origin main
source venv/bin/activate
pm2 restart beautybot

