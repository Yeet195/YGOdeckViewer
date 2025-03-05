# Yu-Gi-Oh! Deck Viewer

A modern desktop application for viewing and analyzing Yu-Gi-Oh! deck files, built with PyWebView and TailwindCSS.

## Project Structure

The application is organized into the following structure:

```
yugioh-deck-viewer/
├── app/
│   ├── __init__.py
│   ├── api.py                # PyWebView API for JavaScript
│   ├── card_service.py       # Card data retrieval and analysis
│   └── deck_parser.py        # Deck file format parsers
├── main.py                   # Application entry point
└── requirements.txt          # Python dependencies
```

## Features

- Open and parse YDK deck files
- Import decks from YDKE URLs and Omega Format
- View cards in Main, Extra, and Side decks
- Analyze deck statistics (card types, attributes, levels, etc.)
- View detailed card information and images
- Copy deck list in CardMarket wants list format

## Installation

1. Clone this repository or download the source code
2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python main.py
   ```

## Supported Formats

- **YDK Files**: Standard Yu-Gi-Oh! deck file format
- **YDKE URLs**: Used by various online deck builders
- **Omega Format**: Used by EDOPro/Omega

## Requirements

- Python 3.7+
- Internet connection (for fetching card data)
- Modern web browser (should be installed on your system)

## Credits

- Card data is fetched from the [YGOProDeck API](https://db.ygoprodeck.com/api-guide/)
- Deck parsing logic based on various Yu-Gi-Oh! deck format specifications