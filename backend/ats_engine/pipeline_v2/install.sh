#!/bin/bash
# install.sh — One-shot dependency installer for ATS Resume Screening System v4

set -e

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   ATS Resume System v4 — Dependency Installer        ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Tesseract ────────────────────────────────────────────────────────────────
echo "📦  Installing Tesseract OCR binary..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo apt-get update -qq
    sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
    echo "✅  Tesseract installed (apt)"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    if command -v brew &>/dev/null; then
        brew install tesseract
        echo "✅  Tesseract installed (brew)"
    else
        echo "⚠️   Homebrew not found. Install manually: https://brew.sh"
    fi
else
    echo "⚠️   Windows detected. Install Tesseract manually:"
    echo "    https://github.com/UB-Mannheim/tesseract/wiki"
fi

# ── MongoDB ──────────────────────────────────────────────────────────────────
echo ""
echo "📦  Setting up MongoDB..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! command -v mongod &>/dev/null; then
        echo "   Installing MongoDB via apt..."
        sudo apt-get install -y mongodb
        sudo systemctl enable mongodb
        sudo systemctl start mongodb
        echo "✅  MongoDB installed and started (apt)"
    else
        echo "✅  MongoDB already installed"
        sudo systemctl start mongodb 2>/dev/null || true
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v mongod &>/dev/null; then
        echo "   Installing MongoDB via brew..."
        brew tap mongodb/brew
        brew install mongodb-community
        brew services start mongodb-community
        echo "✅  MongoDB installed and started (brew)"
    else
        brew services start mongodb-community 2>/dev/null || true
        echo "✅  MongoDB started"
    fi
else
    echo "⚠️   Windows: run MongoDB via Docker:"
    echo "    docker run -d -p 27017:27017 --name mongo mongo:7"
fi

# ── Python packages ───────────────────────────────────────────────────────────
echo ""
echo "📦  Installing Python packages..."
pip install \
    pdfplumber \
    "pdfminer.six" \
    PyMuPDF \
    pytesseract \
    Pillow \
    spacy \
    dateparser \
    rapidfuzz \
    sentence-transformers \
    scikit-learn \
    numpy \
    torch \
    pymongo

# ── spaCy model ───────────────────────────────────────────────────────────────
echo ""
echo "📦  Downloading spaCy en_core_web_md..."
python -m spacy download en_core_web_md

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ✅  All dependencies installed!                     ║"
echo "║                                                      ║"
echo "║  Start:  python main.py --resumes ./resumes/         ║"
echo "║  DB:     python main.py --list-db                    ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""