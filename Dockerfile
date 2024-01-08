# Use an official Python 3.11 runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

# Expose a port for the Streamlit app
EXPOSE 8501

# Set an environment variable for the port
ENV PORT=8501

# Specify the command to run on container start
CMD streamlit run main.py --server.port $PORT