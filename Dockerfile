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

# Make the Hugging Face Space port available
EXPOSE 7860

# Define environment variable
ENV PYTHONUNBUFFERED=1
ENV API_BASE_URL=http://127.0.0.1:8000/api/v1

CMD ["sh", "-c", "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 & exec streamlit run streamlit_app/app.py --server.address=0.0.0.0 --server.port=7860"]
