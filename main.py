import os
import webview
import tempfile

from app.deck_parser import parse_ydk_file, parse_ydke_url, OmegaFormatDecoder
from app.api import DeckViewerAPI


def main():
    # Create API instance
    api = DeckViewerAPI()

    # Get the directory of this script
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Create a temporary HTML file with all resources embedded
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Yu-Gi-Oh! Deck Viewer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        primary: '#6366f1',
                        secondary: '#4f46e5',
                        dark: '#111827',
                        darker: '#0f172a'
                    }
                }
            }
        };
    </script>
    <style>
        .loading {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 100;
        }

        .card-preview {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.9);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 50;
        }

        .card-preview-content {
            display: flex;
            flex-direction: column;
            align-items: center;
            max-width: 90%;
            max-height: 90%;
            overflow: auto;
        }

        @media (min-width: 768px) {
            .card-preview-content {
                flex-direction: row;
                align-items: flex-start;
            }
        }

        .card-preview-image {
            max-height: 60vh;
            object-fit: contain;
        }

        .card-preview-details {
            max-width: 400px;
            margin-top: 1rem;
        }

        @media (min-width: 768px) {
            .card-preview-details {
                margin-top: 0;
                margin-left: 1rem;
                max-height: 60vh;
                overflow-y: auto;
            }
        }

        .card-container {
            width: 80px;
        }

        @media (min-width: 640px) {
            .card-container {
                width: 100px;
            }
        }

        @media (min-width: 1280px) {
            .card-container {
                width: 120px;
            }
        }

        .hidden {
            display: none !important;
        }

        .stat-circle {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
    </style>
    <link rel="icon" href="data:,">
</head>
<body class="bg-dark text-gray-100 min-h-screen">
    <div id="loading" class="loading hidden">
        <div class="text-center p-5 bg-darker rounded-lg">
            <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mx-auto"></div>
            <p class="mt-4 text-lg">Loading...</p>
        </div>
    </div>

    <div id="cardPreview" class="card-preview hidden">
        <div class="card-preview-content">
            <img id="previewImage" class="card-preview-image rounded-lg shadow-xl" src="" alt="Card preview">
            <div id="previewDetails" class="card-preview-details bg-darker p-5 rounded-lg">
                <h2 id="previewName" class="text-xl font-bold mb-2"></h2>
                <div id="previewInfo" class="text-sm space-y-2"></div>
            </div>
        </div>
        <button onclick="closeCardPreview()" class="absolute top-4 right-4 text-white text-2xl hover:text-red-500">
            <i class="fas fa-times"></i>
        </button>
    </div>

    <nav class="bg-darker p-4">
        <div class="container mx-auto flex justify-between items-center">
            <div class="flex items-center">
                <span class="text-xl font-bold">Yu-Gi-Oh! Deck Viewer</span>
            </div>
            <div class="flex items-center space-x-4">
                <button id="openYDKBtn" class="px-4 py-2 bg-primary hover:bg-secondary rounded-lg transition">
                    <i class="fas fa-folder-open mr-2"></i>Open YDK
                </button>
                <button id="showImportFormBtn" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition">
                    <i class="fas fa-file-import mr-2"></i>Import From Text
                </button>
            </div>
        </div>
    </nav>

    <div id="importFormContainer" class="hidden">
        <div class="container mx-auto p-4 bg-darker mt-4 rounded-lg">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-bold">Import Deck</h2>
                <button id="closeImportBtn" class="text-gray-400 hover:text-white">
                    <i class="fas fa-times"></i>
                </button>
            </div>

            <div class="mb-4">
                <label class="block mb-2">Format:</label>
                <div class="flex space-x-4">
                    <label class="inline-flex items-center">
                        <input type="radio" name="importFormat" value="ydke" class="mr-2" checked>
                        YDKE URL
                    </label>
                    <label class="inline-flex items-center">
                        <input type="radio" name="importFormat" value="omega" class="mr-2">
                        Omega Format
                    </label>
                </div>
            </div>

            <div class="mb-4">
                <textarea id="importText" class="w-full h-32 p-2 bg-gray-800 text-white rounded-lg"
                    placeholder="Paste your YDKE URL or Omega format text here..."></textarea>
            </div>

            <button id="importDeckBtn" class="px-4 py-2 bg-primary hover:bg-secondary rounded-lg transition">
                <i class="fas fa-file-import mr-2"></i>Import Deck
            </button>
        </div>
    </div>

    <div id="noDeckMessage" class="container mx-auto p-8 text-center">
        <div class="bg-darker rounded-lg p-8 max-w-lg mx-auto">
            <i class="fas fa-cards fa-4x text-gray-600 mb-4"></i>
            <h2 class="text-2xl font-bold mb-2">No Deck Loaded</h2>
            <p class="text-gray-400 mb-4">Open a YDK file or import a deck to get started.</p>
            <div class="flex justify-center space-x-4">
                <button id="openYDKBtnAlt" class="px-4 py-2 bg-primary hover:bg-secondary rounded-lg transition">
                    <i class="fas fa-folder-open mr-2"></i>Open YDK
                </button>
                <button id="showImportFormBtnAlt" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition">
                    <i class="fas fa-file-import mr-2"></i>Import From Text
                </button>
            </div>
        </div>
    </div>

    <div id="deckContent" class="hidden container mx-auto p-4">
        <div class="flex justify-between items-center mb-4">
            <h1 class="text-2xl font-bold">Deck Viewer</h1>
            <button id="downloadCardmarketBtn" class="px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg transition">
                <i class="fas fa-copy mr-2"></i>Copy CardMarket Wants List
            </button>
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <!-- Stats Panel -->
            <div class="bg-darker rounded-lg p-4">
                <h2 class="text-xl font-bold mb-4 flex items-center">
                    <i class="fas fa-chart-pie mr-2 text-primary"></i>Deck Statistics
                </h2>
                <div id="deckStats" class="space-y-4">
                    <!-- Stats will be filled by JavaScript -->
                </div>
            </div>

            <!-- Main Sections -->
            <div class="lg:col-span-2 space-y-4">
                <!-- Main Deck -->
                <div class="bg-darker rounded-lg p-4">
                    <h2 class="text-xl font-bold mb-4 flex items-center">
                        <i class="fas fa-layer-group mr-2 text-blue-500"></i>
                        Main Deck <span id="mainCount" class="ml-2 text-sm text-gray-400">(0 cards)</span>
                    </h2>
                    <div id="mainDeck" class="flex flex-wrap gap-2">
                        <!-- Cards will be filled by JavaScript -->
                    </div>
                </div>

                <!-- Extra Deck -->
                <div class="bg-darker rounded-lg p-4">
                    <h2 class="text-xl font-bold mb-4 flex items-center">
                        <i class="fas fa-star mr-2 text-purple-500"></i>
                        Extra Deck <span id="extraCount" class="ml-2 text-sm text-gray-400">(0 cards)</span>
                    </h2>
                    <div id="extraDeck" class="flex flex-wrap gap-2">
                        <!-- Cards will be filled by JavaScript -->
                    </div>
                </div>

                <!-- Side Deck -->
                <div class="bg-darker rounded-lg p-4">
                    <h2 class="text-xl font-bold mb-4 flex items-center">
                        <i class="fas fa-exchange-alt mr-2 text-green-500"></i>
                        Side Deck <span id="sideCount" class="ml-2 text-sm text-gray-400">(0 cards)</span>
                    </h2>
                    <div id="sideDeck" class="flex flex-wrap gap-2">
                        <!-- Cards will be filled by JavaScript -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Utility functions
        function showLoading() {
            document.getElementById('loading').classList.remove('hidden');
        }

        function hideLoading() {
            document.getElementById('loading').classList.add('hidden');
        }

        function showCardPreview(card) {
            const previewElement = document.getElementById('cardPreview');
            const imageElement = document.getElementById('previewImage');
            const nameElement = document.getElementById('previewName');
            const infoElement = document.getElementById('previewInfo');

            // Set image and name
            imageElement.src = card.image_url || 'https://images.ygoprodeck.com/images/cards/back_high.jpg';
            nameElement.textContent = card.name || 'Unknown Card';

            // Clear previous info
            infoElement.innerHTML = '';

            // Add card details
            if (card.type) {
                addInfoRow(infoElement, 'Type', card.type);
            }

            if (card.race) {
                addInfoRow(infoElement, 'Race', card.race);
            }

            if (card.attribute) {
                addInfoRow(infoElement, 'Attribute', card.attribute);
            }

            if (card.level) {
                addInfoRow(infoElement, 'Level/Rank', card.level);
            }

            if (card.atk !== undefined) {
                addInfoRow(infoElement, 'ATK', card.atk);
            }

            if (card.def !== undefined) {
                addInfoRow(infoElement, 'DEF', card.def);
            }

            if (card.desc) {
                const descRow = document.createElement('div');
                descRow.className = 'mt-4';
                descRow.innerHTML = `
                    <h3 class="font-bold text-primary">Description</h3>
                    <p class="mt-1 text-gray-300">${card.desc}</p>
                `;
                infoElement.appendChild(descRow);
            }

            // Show the preview
            previewElement.classList.remove('hidden');
        }

        function closeCardPreview() {
            document.getElementById('cardPreview').classList.add('hidden');
        }

        function addInfoRow(container, label, value) {
            const row = document.createElement('div');
            row.className = 'flex justify-between border-b border-gray-700 py-1';
            row.innerHTML = `
                <span class="font-medium">${label}:</span>
                <span>${value}</span>
            `;
            container.appendChild(row);
        }

        function showImportForm() {
            document.getElementById('importFormContainer').classList.remove('hidden');
            document.getElementById('noDeckMessage').classList.add('hidden');
        }

        function hideImportForm() {
            document.getElementById('importFormContainer').classList.add('hidden');
            if (!document.getElementById('deckContent').classList.contains('hidden')) {
                document.getElementById('noDeckMessage').classList.add('hidden');
            } else {
                document.getElementById('noDeckMessage').classList.remove('hidden');
            }
        }

        // Rendering functions
        function renderCardSection(elementId, cards) {
            const container = document.getElementById(elementId);
            container.innerHTML = '';

            cards.forEach(card => {
                const cardElement = document.createElement('div');
                cardElement.className = 'card-container relative';

                // Card count badge for multiple copies
                let countBadge = '';
                if (card.count > 1) {
                    countBadge = `<div class="absolute top-0 right-0 bg-primary text-white rounded-full w-6 h-6 flex items-center justify-center font-bold z-10">
                        ${card.count}
                    </div>`;
                }

                cardElement.innerHTML = `
                    ${countBadge}
                    <img src="${card.image_url || 'https://images.ygoprodeck.com/images/cards/back_high.jpg'}"
                        alt="${card.name}"
                        class="rounded-lg shadow-lg w-full hover:shadow-xl cursor-pointer"
                        onerror="this.src='https://images.ygoprodeck.com/images/cards/back_high.jpg'"
                        data-card-id="${card.id}">
                `;

                const imgElement = cardElement.querySelector('img');
                imgElement.addEventListener('click', () => showCardPreview(card));

                container.appendChild(cardElement);
            });
        }

        function renderDeckStats(stats) {
            const statsContainer = document.getElementById('deckStats');
            statsContainer.innerHTML = '';

            // Card Count Summary
            const countSummary = document.createElement('div');
            countSummary.className = 'bg-gray-800 rounded-lg p-3';
            countSummary.innerHTML = `
                <h3 class="font-bold mb-2">Card Count</h3>
                <div class="grid grid-cols-3 gap-2 text-center">
                    <div class="bg-gray-700 rounded p-2">
                        <div class="text-blue-400 font-bold">${stats.main_deck}</div>
                        <div class="text-xs">Main</div>
                    </div>
                    <div class="bg-gray-700 rounded p-2">
                        <div class="text-purple-400 font-bold">${stats.extra_deck}</div>
                        <div class="text-xs">Extra</div>
                    </div>
                    <div class="bg-gray-700 rounded p-2">
                        <div class="text-green-400 font-bold">${stats.side_deck}</div>
                        <div class="text-xs">Side</div>
                    </div>
                </div>
            `;
            statsContainer.appendChild(countSummary);

            // Card Types Distribution
            if (stats.card_types && Object.keys(stats.card_types).length > 0) {
                const cardTypes = document.createElement('div');
                cardTypes.className = 'bg-gray-800 rounded-lg p-3';

                let cardTypesHTML = '<h3 class="font-bold mb-2">Card Types</h3><div class="space-y-1">';

                const colors = {
                    'Normal Monster': '#f9ca24',
                    'Effect Monster': '#e17055',
                    'Fusion Monster': '#6c5ce7',
                    'Ritual Monster': '#0984e3',
                    'Synchro Monster': '#dfe6e9',
                    'Xyz Monster': '#2d3436',
                    'Pendulum Monster': '#00b894',
                    'Link Monster': '#00cec9',
                    'Spell Card': '#00b894',
                    'Trap Card': '#d63031'
                };

                for (const [type, count] of Object.entries(stats.card_types)) {
                    const color = colors[type] || '#636e72';
                    cardTypesHTML += `
                        <div class="flex items-center justify-between">
                            <div class="flex items-center">
                                <span class="stat-circle" style="background-color: ${color}"></span>
                                ${type}
                            </div>
                            <span class="font-bold">${count}</span>
                        </div>
                    `;
                }

                cardTypesHTML += '</div>';
                cardTypes.innerHTML = cardTypesHTML;
                statsContainer.appendChild(cardTypes);
            }

            // Attributes Distribution
            if (stats.attributes && Object.keys(stats.attributes).length > 0) {
                const attributes = document.createElement('div');
                attributes.className = 'bg-gray-800 rounded-lg p-3';

                let attributesHTML = '<h3 class="font-bold mb-2">Attributes</h3><div class="space-y-1">';

                const colors = {
                    'DARK': '#2d3436',
                    'LIGHT': '#fdcb6e',
                    'EARTH': '#b33939',
                    'WATER': '#0984e3',
                    'FIRE': '#e17055',
                    'WIND': '#00b894',
                    'DIVINE': '#e84393'
                };

                for (const [attr, count] of Object.entries(stats.attributes)) {
                    const color = colors[attr] || '#636e72';
                    attributesHTML += `
                        <div class="flex items-center justify-between">
                            <div class="flex items-center">
                                <span class="stat-circle" style="background-color: ${color}"></span>
                                ${attr}
                            </div>
                            <span class="font-bold">${count}</span>
                        </div>
                    `;
                }

                attributesHTML += '</div>';
                attributes.innerHTML = attributesHTML;
                statsContainer.appendChild(attributes);
            }

            // Monster Types Distribution
            if (stats.monster_types && Object.keys(stats.monster_types).length > 0) {
                const monsterTypes = document.createElement('div');
                monsterTypes.className = 'bg-gray-800 rounded-lg p-3';

                let monsterTypesHTML = '<h3 class="font-bold mb-2">Monster Types</h3><div class="space-y-1">';

                for (const [type, count] of Object.entries(stats.monster_types)) {
                    monsterTypesHTML += `
                        <div class="flex items-center justify-between">
                            <div>${type}</div>
                            <span class="font-bold">${count}</span>
                        </div>
                    `;
                }

                monsterTypesHTML += '</div>';
                monsterTypes.innerHTML = monsterTypesHTML;
                statsContainer.appendChild(monsterTypes);
            }

            // Levels/Ranks Distribution
            if (stats.levels && Object.keys(stats.levels).length > 0) {
                const levels = document.createElement('div');
                levels.className = 'bg-gray-800 rounded-lg p-3';

                let levelsHTML = '<h3 class="font-bold mb-2">Levels/Ranks</h3><div class="grid grid-cols-4 gap-2 text-center">';

                for (let i = 1; i <= 12; i++) {
                    const count = stats.levels[i] || 0;
                    const opacity = count > 0 ? 1 : 0.3;

                    levelsHTML += `
                        <div class="bg-gray-700 rounded p-1" style="opacity: ${opacity}">
                            <div class="font-bold">${count}</div>
                            <div class="text-xs">★${i}</div>
                        </div>
                    `;
                }

                levelsHTML += '</div>';
                levels.innerHTML = levelsHTML;
                statsContainer.appendChild(levels);
            }
        }

        function renderDeck(deck, stats) {
            // Update card counts
            document.getElementById('mainCount').textContent = `(${stats.main_deck} cards)`;
            document.getElementById('extraCount').textContent = `(${stats.extra_deck} cards)`;
            document.getElementById('sideCount').textContent = `(${stats.side_deck} cards)`;

            // Render each section
            renderCardSection('mainDeck', deck.main);
            renderCardSection('extraDeck', deck.extra);
            renderCardSection('sideDeck', deck.side);

            // Render stats
            renderDeckStats(stats);
        }

        // API Functions
        async function openYDKFile() {
            showLoading();
            try {
                console.log("Opening YDK file...");
                const filePath = await pywebview.api.open_file_dialog();
                console.log("File path:", filePath);
                if (filePath) {
                    const result = await pywebview.api.load_ydk_file(filePath);
                    console.log("Load result:", result);
                    if (result.status === 'success') {
                        await loadDeckInfo();
                    } else {
                        alert('Error: ' + result.message);
                    }
                }
            } catch (error) {
                console.error("Error in openYDKFile:", error);
                alert('Error opening file: ' + error);
            }
            hideLoading();
        }

        async function importDeck() {
            showLoading();
            try {
                console.log("Importing deck...");
                const importText = document.getElementById('importText').value.trim();
                const format = document.querySelector('input[name="importFormat"]:checked').value;
                console.log("Format:", format, "Text length:", importText.length);

                let result;
                if (format === 'ydke') {
                    result = await pywebview.api.load_ydke_url(importText);
                } else if (format === 'omega') {
                    result = await pywebview.api.load_omega_format(importText);
                }
                console.log("Import result:", result);

                if (result && result.status === 'success') {
                    hideImportForm();
                    await loadDeckInfo();
                } else {
                    alert('Error: ' + (result ? result.message : 'Unknown error'));
                }
            } catch (error) {
                console.error("Error in importDeck:", error);
                alert('Error importing deck: ' + error);
            }
            hideLoading();
        }

        async function loadDeckInfo() {
            showLoading();
            try {
                console.log("Loading deck info...");
                const deckInfo = await pywebview.api.get_deck_info();
                console.log("Deck info:", deckInfo);

                if (deckInfo && deckInfo.status === 'success') {
                    renderDeck(deckInfo.deck, deckInfo.stats);
                    document.getElementById('noDeckMessage').classList.add('hidden');
                    document.getElementById('deckContent').classList.remove('hidden');
                } else {
                    const message = deckInfo && deckInfo.message ? deckInfo.message : 'Failed to load deck information';
                    alert('Error: ' + message);
                }
            } catch (error) {
                console.error("Error in loadDeckInfo:", error);
                alert('Error loading deck info: ' + error);
            }
            hideLoading();
        }

        async function copyCardmarketWantsList() {
            showLoading();
            try {
                // Get the current deck information
                const deckInfo = await pywebview.api.get_deck_info();
        
                if (deckInfo.status !== 'success') {
                    alert('Error: ' + deckInfo.message);
                    hideLoading();
                    return;
                }
        
                // Generate the wants list content
                let contentParts = [];
        
                // Main Deck
                if (deckInfo.deck.main.length > 0) {
                    contentParts.push('');
                    deckInfo.deck.main.forEach(card => {
                        contentParts.push(`${card.count}x ${card.name}`);
                    });
                    contentParts.push(''); // Empty line
                }
                
                // Extra Deck
                if (deckInfo.deck.extra.length > 0) {
                    contentParts.push('');
                    deckInfo.deck.extra.forEach(card => {
                        contentParts.push(`${card.count}x ${card.name}`);
                    });
                    contentParts.push(''); // Empty line
                }
                
                // Side Deck
                if (deckInfo.deck.side.length > 0) {
                    contentParts.push('');
                    deckInfo.deck.side.forEach(card => {
                        contentParts.push(`${card.count}x ${card.name}`);
                    });
                }

                const content = contentParts.join(String.fromCharCode(10));
        
                // Copy the content to the clipboard
                await navigator.clipboard.writeText(content);
                alert('CardMarket wants list copied to clipboard!');
            } catch (error) {
                console.error("Error in copyCardmarketWantsList:", error);
                alert('Error copying CardMarket wants list: ' + error);
            } finally {
                hideLoading();
            }
        }

        // Initialize when DOM is loaded
        document.addEventListener('DOMContentLoaded', function() {
            console.log("DOM loaded, initializing...");

            // Setup basic navigation buttons
            document.getElementById('openYDKBtn').addEventListener('click', openYDKFile);
            document.getElementById('openYDKBtnAlt').addEventListener('click', openYDKFile);
            document.getElementById('showImportFormBtn').addEventListener('click', showImportForm);
            document.getElementById('showImportFormBtnAlt').addEventListener('click', showImportForm);
            document.getElementById('closeImportBtn').addEventListener('click', hideImportForm);
            document.getElementById('importDeckBtn').addEventListener('click', importDeck);

            // Setup copy button
            const copyBtn = document.getElementById('downloadCardmarketBtn');
            if (copyBtn) {
                copyBtn.addEventListener('click', copyCardmarketWantsList);
            }

            console.log('Event listeners initialized successfully');
        });
    </script>
</body>
</html>"""
        f.write(html_content)
        temp_html_path = f.name

    # Create window with the inline HTML file
    webview.create_window('Yu-Gi-Oh! Deck Viewer', url=temp_html_path, js_api=api, min_size=(1000, 700))
    webview.start(debug=False)

    # Clean up the temporary file
    try:
        os.unlink(temp_html_path)
    except:
        pass


if __name__ == '__main__':
    main()
