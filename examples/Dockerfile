# This is a Dockerfile for using an isolated instance of Open Interpreter

# Start with Python 3.11
FROM python:3.11

# Replace <your_openai_api_key> with your own key
ENV OPENAI_API_KEY <your_openai_api_key>

# Install Open Interpreter
RUN pip install open-vulnera


# To run the container

# docker build -t openvulnera .
# docker run -d -it --name interpreter-instance openvulnera interpreter
# docker attach interpreter-instance

# To mount a volume
# docker run -d -it -v /path/on/your/host:/path/in/the/container --name interpreter-instance openvulnera interpreter
