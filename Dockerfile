# Use the official Python 3 image as the base image
FROM python:3

# Set the working directory inside the container
WORKDIR /app

# Copy your bot script and requirements file into the container
COPY bot.py .
COPY requirements.txt .

# Install any needed packages specified in the requirements.txt file
RUN pip install -r requirements.txt

# Run your bot script when the container launches
CMD ["python3", "bot.py"]
