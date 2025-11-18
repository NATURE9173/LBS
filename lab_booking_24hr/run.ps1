& "$PSScriptRoot\.venv\Scripts\activate"
Start-Process "http://127.0.0.1:5000"
python "$PSScriptRoot\app.py"
