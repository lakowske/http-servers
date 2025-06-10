#!/bin/bash

echo "Content-Type: text/plain"
echo ""
echo "hello world"

if [ -f "/usr/local/apache2/conf/passwd" ]; then
    echo "User file exists"
else
    echo "User file does not exist"
fi
