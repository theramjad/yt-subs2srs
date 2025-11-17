"""Anki deck generation using genanki"""
import os
import random
import logging
import genanki

logger = logging.getLogger(__name__)


def create_subs2srs_model():
    """Create Anki note model for subs2srs cards"""
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


def create_anki_deck(
    cards: list,
    deck_name: str,
    output_path: str,
    use_video_tags: bool = False
) -> str:
    """
    Create APKG file from cards

    Args:
        cards: List of card dicts with audioFile, imageFile, sentence, video_name
        deck_name: Name for the deck
        output_path: Path for output APKG file
        use_video_tags: If True, tag each card with its video_name

    Returns:
        str: Path to created APKG file
    """
    logger.info(f"Creating Anki deck: {deck_name}")

    # Create deck
    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = genanki.Deck(deck_id, deck_name)

    # Create model
    model = create_subs2srs_model()

    # Collect media files
    media_files = []

    # Add cards
    for card in cards:
        audio_file = card['audioFile']
        image_file = card['imageFile']
        sentence = card['sentence']

        # Get basenames for Anki references
        audio_basename = os.path.basename(audio_file)

        # Handle optional image
        if image_file:
            image_basename = os.path.basename(image_file)
            image_html = f'<img src="{image_basename}">'
            if os.path.exists(image_file):
                media_files.append(image_file)
        else:
            image_html = ''

        # Add audio to media files
        if os.path.exists(audio_file):
            media_files.append(audio_file)

        # Create note with optional tags
        tags = []
        if use_video_tags and 'video_name' in card:
            # Clean video name for tag (remove special characters, replace spaces with underscores)
            video_tag = card['video_name'].replace(' ', '_').replace('-', '_')
            tags.append(video_tag)

        note = genanki.Note(
            model=model,
            fields=[
                f'[sound:{audio_basename}]',
                image_html,
                sentence,
            ],
            tags=tags
        )

        deck.add_note(note)

    # Generate package
    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(output_path)

    logger.info(f"APKG created: {output_path} ({len(cards)} cards)")
    return output_path
