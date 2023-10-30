name: my-telegram-bot
version: 1.0.0
build:
  steps:
    - run: pip install -r requirements.txt
run:
  service: python3 bot.py
  ports:
    - 80:8080
