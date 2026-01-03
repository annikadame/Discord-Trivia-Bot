# Discord-Trivia-Bot

A Discord bot that runs multiplayer trivia games using the Open Trivia Database API. Players can join games, select a trivia category, and compete to answer questions correctly to earn points. The bot supports different difficulty levels, keeps track of scores, and displays rankings at the end of each game. It includes commands for starting a game, joining, selecting categories, checking scores, and ending the game. This bot was developed as part of a group project. This repository is a showcase of the bot’s functionality and is meant to highlight its functionality and structure for portfolio purposes.

## Features

- Multiplayer trivia in Discord
- Categories:
  - General Knowledge
  - Science
  - History
  - Geography
  - Entertainment: Books
  - Sports
  - Anime & Manga
  - Animals
  - Computers
  - Gadgets
  - Cartoons
  - Vehicles
- Difficulty levels: Easy, Medium, Hard
- Score tracking and rankings
- Commands: !trivia, !join, !category, !score, !standings, !endgame, !help

## Getting Started

1. Clone the repo:
```bash
git clone https://github.com/annikadame/Discord-Trivia-Bot.git
cd Discord-Trivia-Bot

2. Install Dependencies:
pip install -r requirements.txt

3. Create a .env with your Discord bot token
Important: To run the bot, you will need your own Discord bot token in a `.env` file. The `.env` file containing my token is not included for security reasons.
DISCORD_TOKEN=your_token_here

4. Run the bot
python bot.py
