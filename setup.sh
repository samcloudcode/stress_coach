#!/bin/bash

# Install Streamlit dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create Streamlit config file
mkdir -p ~/.streamlit
echo "\
[general]\n\
email = \"samstitt@gmail.com\"\n\
" > ~/.streamlit/credentials.toml
echo "\
[server]\n\
headless = true\n\
enableCORS=false\n\
port = $PORT\n\
" > ~/.streamlit/config.toml
