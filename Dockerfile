FROM hse_cunning_fox_bot_base:latest

WORKDIR /app

# Copy application requirements
COPY requirements.txt .

# Install application dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Run the bot
CMD ["./start_bot.sh"]
