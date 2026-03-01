###########################################################################################
# This Dockerfile runs an LMC.compatible websocket server at / on port 8000.              #
# To learn more about LMC, visit https://github.com/open-vulnera/open-vulnera/tree/master/docs/protocols/lmc-messages. #
###########################################################################################

FROM python:3.11.8

# Set environment variables
# ENV OPENAI_API_KEY ...

ENV HOST 0.0.0.0
# ^ Sets the server host to 0.0.0.0, Required for the server to be accessible outside the container

# Copy required files into container
RUN mkdir -p interpreter scripts
COPY interpreter/ interpreter/
COPY scripts/ scripts/
COPY poetry.lock pyproject.toml README.md ./

# Expose port 8000
EXPOSE 8000

# Install server dependencies
RUN pip install ".[server]"

# Start the server
ENTRYPOINT ["interpreter", "--server"]