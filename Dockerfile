# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make start script executable
RUN chmod +x start.sh

# Make port 8000 available (default — matches HF Space manifest and
# docker-compose). 7860 and 8501 are kept for legacy / Streamlit use.
EXPOSE 8000
EXPOSE 7860
EXPOSE 8501

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Default command: start both backend and Streamlit via start.sh
CMD ["./start.sh"]
