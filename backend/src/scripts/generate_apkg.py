#!/usr/bin/env python3
"""
Generate Anki APKG file from subs2srs cards using genanki
Usage: python generate_apkg.py <cards_json_file> <output_apkg_path>
"""

import sys
import json
import genanki
import random
import os

def create_subs2srs_model():
    """Create the Anki note model for subs2srs cards"""
    model_id = random.randrange(1 << 30, 1 << 31)

    return genanki.Model(
        model_id,
        'Subs2SRS Japanese',
        fields=[
            {'name': 'Audio'},
            {'name': 'Image'},
            {'name': 'Sentence'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{Audio}}<br>{{Image}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Sentence}}',
            },
        ],
        css="""
.card {
    font-family: "Hiragino Kaku Gothic Pro", "Meiryo", "MS Gothic", sans-serif;
    font-size: 24px;
    text-align: center;
    color: black;
    background-color: white;
}

img {
    max-width: 100%;
    height: auto;
}
        """
    )

def generate_apkg(cards_data_path, output_path):
    """
    Generate APKG file from cards data

    Args:
        cards_data_path: Path to JSON file containing cards data
        output_path: Path where APKG file should be saved
    """
    # Load cards data
    with open(cards_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    deck_name = data.get('deckName', 'Japanese Video')
    cards = data.get('cards', [])
    media_dir = data.get('mediaDir', '')

    # Create deck
    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = genanki.Deck(deck_id, deck_name)

    # Create model
    model = create_subs2srs_model()

    # Collect media files
    media_files = []

    # Add cards to deck
    for card in cards:
        audio_file = card.get('audioFile', '')
        image_file = card.get('imageFile', '')
        sentence = card.get('sentence', '')

        # Get basenames for media references in Anki
        audio_basename = os.path.basename(audio_file)
        image_basename = os.path.basename(image_file)

        # Add full paths to media files list
        if os.path.exists(audio_file):
            media_files.append(audio_file)
        if os.path.exists(image_file):
            media_files.append(image_file)

        # Create note
        note = genanki.Note(
            model=model,
            fields=[
                f'[sound:{audio_basename}]',
                f'<img src="{image_basename}">',
                sentence,
            ]
        )

        deck.add_note(note)

    # Generate package
    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(output_path)

    print(f'Successfully created APKG: {output_path}')
    print(f'Deck name: {deck_name}')
    print(f'Number of cards: {len(cards)}')
    print(f'Media files: {len(media_files)}')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python generate_apkg.py <cards_json_file> <output_apkg_path>')
        sys.exit(1)

    cards_data_path = sys.argv[1]
    output_path = sys.argv[2]

    if not os.path.exists(cards_data_path):
        print(f'Error: Cards data file not found: {cards_data_path}')
        sys.exit(1)

    generate_apkg(cards_data_path, output_path)
