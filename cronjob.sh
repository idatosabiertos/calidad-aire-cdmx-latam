#!/bin/bash
python3 app.py
zip output.zip output/*.*
curl -i -X POST -F "file=@output.zip" http://localhost:8000/
