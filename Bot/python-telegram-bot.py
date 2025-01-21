import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from fuzzywuzzy import fuzz
from transformers import pipeline
import random

# Initialize DeepAI API (replace YOUR_DEEPAI_KEY with your DeepAI key)
DEEPAI_API_KEY = '7b1dbef4-1eda-44bf-aded-9492cb1f9fd0'
TOKEN = '7704374911:AAH2eNfHu9fzYmIeHVIjr11dDjS9ucIFiKM'

# Quiz question categories
CATEGORIES = {
    "math": "Math Quiz",
    "science": "Science Quiz",
    "history": "History Quiz",
    "programming": "Programming Quiz",
    "cybersecurity": "Cybersecurity Quiz",
    "python": "Python Quiz",
}

# State tracking
user_state = {}
user_performance = {}
sentiment_analysis = pipeline("sentiment-analysis")  # Sentiment analysis pipeline for user motivation

# Sample programming and cybersecurity facts
FACTS = [
    "Did you know? Python was named after the British comedy group Monty Python!",
    "Cybersecurity is the practice of protecting systems, networks, and programs from digital attacks.",
    "The first computer programmer is considered to be Ada Lovelace, who wrote an algorithm for Charles Babbage's early mechanical general-purpose computer.",
    "In 1995, the first version of Java was released, designed to have the look and feel of the C++ programming language.",
    "A common programming practice is to comment code, which helps others (and yourself) understand what your code does.",
    "The term 'phishing' refers to the fraudulent attempt to obtain sensitive information by disguising as a trustworthy entity."
]

def start(update: Update, context: CallbackContext):
    """Start command to initiate the bot."""
    welcome_msg = "Welcome to the Smart Quiz Bot! Please select a topic:\n" + "\n".join([f"- {cat}" for cat in CATEGORIES.keys()])
    update.message.reply_text(welcome_msg)

def get_questions(topic, difficulty="easy"):
    """Fetch quiz questions based on the topic and difficulty using DeepAI."""
    try:
        response = requests.post(
            "https://api.deepai.org/api/text-generator",
            data={
                'text': f"Generate a {difficulty} multiple-choice question on {topic}. Provide four answer options with the correct one indicated.",
            },
            headers={'api-key': DEEPAI_API_KEY}
        )
        question_data = response.json()
        question = question_data['output']
        return question
    except Exception as e:
        return "Could not fetch questions."

def analyze_sentiment(user_input):
    """Analyze the sentiment of user input to provide motivational feedback."""
    result = sentiment_analysis(user_input)
    sentiment = result[0]["label"]
    if sentiment == "NEGATIVE":
        return "It seems like you're finding this tough. Don't worry; you can do it!"
    elif sentiment == "POSITIVE":
        return "Great job! You're on fire! Keep going!"
    else:
        return "Keep it up!"

def check_answer(user_answer, correct_answer):
    """Check if the user's answer is semantically similar to the correct answer."""
    similarity_score = fuzz.ratio(user_answer.lower(), correct_answer.lower())
    # Semantic comparison using NLP
    # Using transformers for semantic similarity (you can use cosine similarity or another metric)
    if similarity_score > 75:  # Fuzzy matching threshold
        return True
    return False

def adjust_difficulty(user_id, correct):
    """Adjust question difficulty based on the user's performance."""
    if user_id not in user_performance:
        user_performance[user_id] = {"score": 0, "difficulty": "easy"}
    if correct:
        user_performance[user_id]["score"] += 1
        if user_performance[user_id]["score"] > 5:
            user_performance[user_id]["difficulty"] = "medium"
        if user_performance[user_id]["score"] > 10:
            user_performance[user_id]["difficulty"] = "hard"
    else:
        user_performance[user_id]["score"] -= 1
        if user_performance[user_id]["score"] < 3:
            user_performance[user_id]["difficulty"] = "easy"
    return user_performance[user_id]["difficulty"]

def ask_question(update: Update, context: CallbackContext):
    """Ask a quiz question based on the user-selected topic and difficulty."""
    topic = update.message.text.lower()
    if topic not in CATEGORIES:
        update.message.reply_text("Please choose a valid topic.")
        return

    difficulty = user_performance.get(update.effective_user.id, {}).get("difficulty", "easy")
    question = get_questions(topic, difficulty)
    # Placeholder for correct answer extraction; you need to implement this
    correct_answer = "your_correct_answer"  # Replace with actual logic to extract the correct answer
    user_state[update.effective_user.id] = {'topic': topic, 'question': question, 'difficulty': difficulty, 'correct_answer': correct_answer}
    
    update.message.reply_text(f"Here's your {difficulty} question on {CATEGORIES[topic]}:\n\n{question}")

    # Share a random fact after asking a question
    fact = random.choice(FACTS)
    update.message.reply_text(f"Fun Fact: {fact}")

def answer(update: Update, context: CallbackContext):
    """Check the answer and give feedback with motivational sentiment analysis."""
    user_id = update.effective_user.id
    if user_id not in user_state:
        update.message.reply_text("Please select a topic first by typing the topic name.")
        return

    user_answer = update.message.text
    correct_answer = user_state[user_id]['correct_answer']  # Replace with actual logic

    if check_answer(user_answer, correct_answer):
        next_difficulty = adjust_difficulty(user_id, True)
        update.message.reply_text(f"Correct! Well done 🎉. Next question will be {next_difficulty} difficulty.")
    else:
        update.message.reply_text("Not quite right. Try again or type 'submit' to end.")

    sentiment_response = analyze_sentiment(user_answer)
    update.message.reply_text(sentiment_response)

def submit(update: Update, context: CallbackContext):
    """End the quiz session, summarize, and reset the state."""
    user_id = update.effective_user.id
    summary = generate_summary_and_recommendations(user_id)
    update.message.reply_text(summary)
    if user_id in user_state:
        del user_state[user_id]

def generate_summary_and_recommendations(user_id):
    """Summarize the session and provide recommendations."""
    score = user_performance.get(user_id, {}).get("score", 0)
    if score < 5:
        return "Good effort! It looks like you could use more practice with the basics. Try reviewing [topic]."
    elif score < 10:
        return "Nice work! You’re getting the hang of it. Consider exploring intermediate topics."
    else:
        return "Excellent! You’ve mastered this topic. How about trying a related topic to broaden your knowledge?"

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, ask_question))
    dp.add_handler(MessageHandler(Filters.regex('^(submit)$'), submit))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()


