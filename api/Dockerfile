FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copys the current directory contents into the container at /app
COPY . . 

# Command to run the script
CMD ["python", "api.py"]
