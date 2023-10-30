# Use the official Python image as the base image
FROM python:3.8

# Set the working directory inside the container
WORKDIR /app

# Copy your bot script and any other necessary files into the container
COPY bot.py .

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in the requirements.txt file
RUN pip install -r requirements.txt

# Expose the necessary ports (if required by your script)
EXPOSE 80

# Run your bot script when the container launches
CMD ["python3", "bot.py"]
