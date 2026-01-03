import discord
import os
import asyncio
import requests
import html
import random
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    print("DISCORD_TOKEN environment variable not found.")
    exit(1)

# Discord client setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Trivia categories
trivia_categories = [
    "General Knowledge",
    "Science",
    "History",
    "Geography",
    "Entertainment: Books",
    "Sports",
    "Anime and Manga",
    "Animals",
    "Science: Computers",
    "Science: Gadgets",
    "Cartoons and Animations",
    "Vehicles",
]

# Mapping category names to API category IDs
category_ids = {
    "General Knowledge": 9,
    "Science": 17,
    "History": 23,
    "Geography": 22,
    "Entertainment: Books": 10,
    "Sports": 21,
    "Anime and Manga": 31,
    "Animals": 27,
    "Science: Computers": 18,
    "Science: Gadgets": 30,
    "Cartoons and Animations": 32,
    "Vehicles": 28,
}

# Global game state
user_scores = {}
game_in_progress = False
game_starter = None
players = []

trivia_active = False
category_selected = False
current_question = None
current_answer = None
awaiting_answer = False
difficulty = 30

timer_expired = False
timer_task = None
all_answers = []


async def show_trivia_categories(channel):
    """Sends a numbered list of trivia categories to the channel."""
    category_list = "\n".join([f"{i+1}. {category}" for i, category in enumerate(trivia_categories)])
    await channel.send(f"Choose a trivia category by typing the corresponding number:\n{category_list}")


def update_score(user):
    """Increment the user's score by 1."""
    if user not in user_scores:
        user_scores[user] = 0
    user_scores[user] += 1


def get_score(user):
    """Return the user's current score."""
    return user_scores.get(user, 0)


def help_messages():
    """Return help text describing available bot commands."""
    return (
        "!help = Shows all commands\n"
        "!trivia = Start a new trivia game\n"
        "!score = Show your current score\n"
        "!join = Join an in-progress trivia game\n"
        "!category = Show trivia categories if no question is active"
    )


def fetch_trivia_question(category):
    """Fetch a single trivia question from Open Trivia Database API."""
    category_id = category_ids.get(category)
    if category_id:
        url = f"https://opentdb.com/api.php?amount=1&category={category_id}&type=multiple"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data["response_code"] == 0:
                return data["results"][0]
    return None


def set_difficulty(timer):
    """Adjust the difficulty by changing the time allowed to answer."""
    global difficulty
    difficulty = timer


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


def reset_game_state():
    """Reset all variables to prepare for a new trivia round."""
    global trivia_active, category_selected, current_question, current_answer
    global awaiting_answer, timer_task, game_in_progress

    trivia_active = False
    category_selected = False
    current_question = None
    current_answer = None
    awaiting_answer = False
    game_in_progress = False
    set_difficulty(30)


async def timer(duration, channel):
    """Countdown timer for answering a trivia question."""
    global timer_expired, awaiting_answer, current_answer
    timer_expired = False

    try:
        message = await channel.send(f"You have {duration} seconds to answer starting now!")
        for remaining_time in range(duration, 0, -1):
            if remaining_time == 10:
                await channel.send("Hurry up! Only 10 seconds left!", delete_after=5)
            await message.edit(content=f"You have {remaining_time} seconds left")
            await asyncio.sleep(1)

        if awaiting_answer:
            await channel.send(f"Time's up! The correct answer was: {current_answer}")
            reset_game_state()

        timer_expired = True
        await message.edit(content="Time's up! You can no longer submit answers.")
        await message.delete()

    except asyncio.CancelledError:
        await message.edit(content="The timer has been stopped.")
        await message.delete()
    except Exception as e:
        print(f"An error occurred: {e}")


@client.event
async def on_message(message):
    """Main message handler for bot commands and game flow."""
    global trivia_active, category_selected, current_question, current_answer
    global awaiting_answer, timer_expired, timer_task, game_starter, game_in_progress, all_answers

    if message.author == client.user:
        return

    content = message.content.strip()

    # Start a trivia game
    if content.startswith("!trivia"):
        if trivia_active or awaiting_answer:
            await message.channel.send("A trivia game is already in progress. Please wait until it finishes.")
        else:
            trivia_active = True
            game_in_progress = True
            category_selected = False
            game_starter = message.author.id
            await show_trivia_categories(message.channel)

    # Show current standings
    elif content.startswith("!standings"):
        if game_in_progress and user_scores:
            sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
            rankings = "\n".join([f"{i+1}. {user}: {score} points" for i, (user, score) in enumerate(sorted_scores)])
            await message.channel.send(f"Current standings:\n{rankings}")
        elif game_in_progress:
            await message.channel.send("No scores to display yet. Start answering questions to earn points!")
        else:
            await message.channel.send("No game is currently in progress. Start a new game with !trivia.")

    # End the current game
    elif content.startswith("!endgame"):
        if game_in_progress and message.author.id == game_starter:
            await message.channel.send("The game has been ended by the game starter.")
            if timer_task:
                timer_task.cancel()
                timer_task = None

            if user_scores:
                sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
                rankings = "\n".join([f"{i+1}. {user}: {score} points" for i, (user, score) in enumerate(sorted_scores)])
                await message.channel.send(f"The game has ended! Final rankings:\n{rankings}")
            else:
                await message.channel.send("The game has ended! No scores to display.")

            reset_game_state()
            players.clear()
            user_scores.clear()
            game_starter = None
        elif game_in_progress:
            await message.channel.send("Only the game starter can end the game.")
        else:
            await message.channel.send("No game is currently in progress to end.")

    # Show help
    elif content.startswith("!help"):
        await message.channel.send(help_messages())

    # Difficulty settings
    elif content.startswith("!hard"):
        set_difficulty(15)
        await message.channel.send("You have chosen Hard mode. You have 15 seconds per question!")
    elif content.startswith("!medium"):
        set_difficulty(30)
        await message.channel.send("You have chosen Medium mode. You have 30 seconds per question!")
    elif content.startswith("!easy"):
        set_difficulty(45)
        await message.channel.send("You have chosen Easy mode. You have 45 seconds per question!")

    # Join an active game
    elif content.startswith("!join"):
        if game_in_progress:
            if message.author.name not in players:
                players.append(message.author.name)
                await message.channel.send(f"{message.author.name} has joined the game!")
            else:
                await message.channel.send(f"{message.author.name}, you are already in the game!")
        else:
            await message.channel.send("No game is currently in progress. Start a new game with !trivia.")

    # Category selection
    elif content.isdigit() and trivia_active and not category_selected:
        category_index = int(content) - 1
        if 0 <= category_index < len(trivia_categories):
            selected_category = trivia_categories[category_index]
            await message.channel.send(f"You selected: {selected_category}")
            category_selected = True

            question_data = fetch_trivia_question(selected_category)
            if question_data:
                current_question = html.unescape(question_data["question"])
                current_answer = html.unescape(question_data["correct_answer"])
                incorrect_answers = [html.unescape(ans) for ans in question_data["incorrect_answers"]]
                all_answers = incorrect_answers + [current_answer]
                random.shuffle(all_answers)

                options = "\n".join([f"{i+1}. {answer}" for i, answer in enumerate(all_answers)])
                await message.channel.send(f"Question: {current_question}\nOptions:\n{options}")
                awaiting_answer = True
                timer_task = asyncio.create_task(timer(difficulty, message.channel))
            else:
                await message.channel.send("Failed to fetch a trivia question. Please try again.")
                reset_game_state()
        else:
            await message.channel.send("Invalid selection. Please choose a valid number from the list.")

    # Answer handling
    elif trivia_active and category_selected and current_question:
        if timer_expired:
            await message.channel.send("Sorry, the time is up. You can no longer answer.")
            return

        if content.isdigit():
            option_index = int(content) - 1
            if 0 <= option_index < len(all_answers):
                selected_answer = all_answers[option_index]
                if selected_answer.lower() == current_answer.lower():
                    await message.channel.send("Correct answer! You earned 1 point.")
                    update_score(message.author.name)
                else:
                    await message.channel.send(f"Wrong answer! The correct answer was: {current_answer}")

                if timer_task:
                    timer_task.cancel()
                    timer_task = None
                reset_game_state()
            else:
                await message.channel.send("Invalid option number. Please select a valid option.")
        else:
            await message.channel.send("Please respond with the number corresponding to your answer choice.")

    # Show user score
    elif content.startswith("!score"):
        score = get_score(message.author.name)
        await message.channel.send(f"{message.author.name}, your current score is: {score}")


client.run(TOKEN)
