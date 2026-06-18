# setup.ps1
# Setup virtual environment and dependencies for AI Music Generator

Write-Host "Creating virtual environment 'venv'..." -ForegroundColor Cyan
& "C:\Users\pavan\AppData\Local\Programs\Python\Python311\python.exe" -m venv venv

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create virtual environment."
    Exit 1
}

Write-Host "Upgrading pip..." -ForegroundColor Cyan
& "venv\Scripts\python.exe" -m pip install --upgrade pip

Write-Host "Installing dependencies from requirements.txt (this may take a minute)..." -ForegroundColor Cyan
& "venv\Scripts\python.exe" -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install dependencies."
    Exit 1
}

Write-Host "Environment set up successfully!" -ForegroundColor Green
