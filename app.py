"""Video to Sub2SRS Decks - Streamlit App"""
import os
import shutil
import logging
import hashlib
import time
import zipfile
import streamlit as st
from pathlib import Path
from modules.audio_processor import extract_audio, extract_audio_clip
from modules.transcriber import transcribe_audio
from modules.segmenter import segment_into_sentences, filter_valid_sentences
from modules.anki_deck import create_anki_deck
from modules.video_frame_extractor import VideoFrameExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_hash_filename(prefix: str, extension: str) -> str:
    """Generate a random hash-based filename to avoid special characters"""
    # Use timestamp + random component for uniqueness
    unique_string = f"{time.time()}{os.urandom(16).hex()}"
    hash_value = hashlib.md5(unique_string.encode()).hexdigest()
    return f"{prefix}-{hash_value}.{extension}"


# Page config
st.set_page_config(
    page_title="Video to Sub2SRS Decks",
    page_icon="🎴",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #667eea;
        padding: 1rem 0;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">Video to Subs2srs Decks</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Convert MP4 videos to Anki flashcard decks</p>', unsafe_allow_html=True)

# Initialize session state
if 'session_id' not in st.session_state:
    # Generate unique session ID for multi-user isolation
    st.session_state.session_id = hashlib.md5(f"{time.time()}{os.urandom(16).hex()}".encode()).hexdigest()
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'completed' not in st.session_state:
    st.session_state.completed = False
if 'apkg_path' not in st.session_state:
    st.session_state.apkg_path = None


def process_videos(uploaded_files, deck_mode: str, api_key: str):
    """Main processing pipeline for multiple MP4 files"""

    # Create session-specific temp directory for multi-user isolation
    work_dir = Path("tmp") / st.session_state.session_id
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        progress_bar = st.progress(0)
        status_text = st.empty()

        combined_mode = (deck_mode == "Combined Deck")

        if combined_mode:
            # Generate deck name from filenames
            if len(uploaded_files) == 1:
                deck_name = Path(uploaded_files[0].name).stem
            else:
                deck_name = f"Combined_{len(uploaded_files)}_videos"

            all_cards = []
            card_counter = 0

        else:  # Separate Decks mode
            decks = []  # List of (deck_name, cards, apkg_path) tuples

        # Process each video file
        for file_idx, uploaded_file in enumerate(uploaded_files):
            # Extract filename without extension
            video_name = Path(uploaded_file.name).stem

            # Step 1: Save uploaded MP4 file
            status_text.text(f"📁 Saving {uploaded_file.name}...")
            video_path = work_dir / uploaded_file.name
            with open(video_path, 'wb') as f:
                f.write(uploaded_file.read())

            progress = int((file_idx / len(uploaded_files)) * 10)
            progress_bar.progress(progress)

            # Step 2: Extract audio
            status_text.text(f"🎵 Extracting audio from {uploaded_file.name}...")
            audio_path = extract_audio(str(video_path), str(work_dir))

            progress = int((file_idx / len(uploaded_files)) * 20) + 10
            progress_bar.progress(progress)

            # Step 3: Transcribe
            status_text.text(f"🎤 Transcribing {uploaded_file.name} (this may take several minutes)...")
            words = transcribe_audio(audio_path, api_key)

            progress = int((file_idx / len(uploaded_files)) * 30) + 20
            progress_bar.progress(progress)

            # Step 4: Segment into sentences
            status_text.text(f"✂️ Segmenting {uploaded_file.name} into sentences...")
            sentences = segment_into_sentences(words)
            valid_sentences = filter_valid_sentences(sentences)

            st.info(f"📹 **{video_name}**: {len(valid_sentences)} sentences")

            progress = int((file_idx / len(uploaded_files)) * 40) + 30
            progress_bar.progress(progress)

            # Step 5: Generate cards with screenshots
            status_text.text(f"🎴 Generating cards for {uploaded_file.name}...")

            # Initialize frame extractor for this video
            frame_extractor = VideoFrameExtractor(str(video_path))

            video_cards = []
            for i, sentence in enumerate(valid_sentences):
                # Update progress (40-80% for card generation)
                if len(valid_sentences) > 0:
                    sentence_progress = 40 + int(40 * (i / len(valid_sentences)))
                    progress_bar.progress(min(sentence_progress, 80))

                # Extract audio clip - use hash-based filenames to avoid special characters in Anki
                audio_clip_filename = generate_hash_filename("audio", "mp3")
                screenshot_filename = generate_hash_filename("image", "jpg")

                audio_clip_path = str(work_dir / audio_clip_filename)
                screenshot_path = str(work_dir / screenshot_filename)

                if combined_mode:
                    card_counter += 1

                extract_audio_clip(
                    audio_path,
                    sentence.start_time,
                    sentence.end_time,
                    audio_clip_path
                )

                # Extract screenshot at sentence start time
                frame_extractor.extract_frame(sentence.start_time, screenshot_path)

                card = {
                    'audioFile': audio_clip_path,
                    'imageFile': screenshot_path,
                    'sentence': sentence.text
                }

                if combined_mode:
                    all_cards.append(card)
                else:
                    video_cards.append(card)

            # Delete source audio file to save space
            if os.path.exists(audio_path):
                os.remove(audio_path)

            # For separate decks mode, create APKG for this video
            if not combined_mode:
                status_text.text(f"📦 Creating deck for {video_name}...")
                output_path = str(work_dir / f"{video_name}.apkg")
                create_anki_deck(video_cards, video_name, output_path)
                decks.append({
                    'name': video_name,
                    'cards': video_cards,
                    'apkg_path': output_path,
                    'card_count': len(video_cards)
                })

        # For combined mode, create single APKG
        if combined_mode:
            status_text.text("📦 Creating combined Anki deck package...")
            progress_bar.progress(90)

            output_path = str(work_dir / f"{deck_name}.apkg")
            create_anki_deck(all_cards, deck_name, output_path)

            # Complete
            progress_bar.progress(100)
            status_text.text("✅ Complete!")

            return {
                'mode': 'combined',
                'deck_name': deck_name,
                'apkg_path': output_path,
                'card_count': len(all_cards),
                'preview_cards': all_cards
            }
        else:
            # Complete
            progress_bar.progress(100)
            status_text.text("✅ Complete!")

            total_cards = sum(d['card_count'] for d in decks)
            return {
                'mode': 'separate',
                'decks': decks,
                'total_cards': total_cards
            }

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise


# Main UI
if not st.session_state.completed:
    # Input form
    with st.form("input_form"):
        uploaded_files = st.file_uploader(
            "Upload MP4 Video Files",
            type=['mp4'],
            accept_multiple_files=True,
            help="Upload one or more Japanese MP4 video files"
        )

        deck_mode = st.radio(
            "Deck Mode",
            options=["Combined Deck", "Separate Decks"],
            help="Combine all videos into one deck, or create separate decks per video",
            horizontal=True
        )

        api_key = st.text_input(
            "AssemblyAI API Key",
            type="password",
            help="Get your free API key at assemblyai.com"
        )

        submit = st.form_submit_button("🚀 Generate Deck", use_container_width=True)

    if submit:
        if not uploaded_files or not api_key:
            st.error("Please provide both MP4 file(s) and API key")
        else:
            st.session_state.processing = True

            try:
                with st.spinner("Processing..."):
                    result = process_videos(uploaded_files, deck_mode, api_key)

                    st.session_state.result = result
                    st.session_state.completed = True
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.session_state.processing = False

else:
    # Show results based on mode
    result = st.session_state.result

    if result['mode'] == 'combined':
        st.success(f"✅ Successfully generated {result['card_count']} cards in **{result['deck_name']}**!")

        # Preview cards
        st.subheader("Card Preview")
        for i, card in enumerate(result['preview_cards'][:10]):  # Show first 10 cards
            with st.container():
                col1, col2 = st.columns([3, 2])

                with col1:
                    sentence = card['sentence']
                    display_sentence = sentence if len(sentence) <= 100 else sentence[:100] + "..."
                    st.markdown(f"**#{i+1}:** {display_sentence}")
                    if len(sentence) > 100:
                        with st.expander("Show full sentence"):
                            st.write(sentence)

                    # Display screenshot
                    if card.get('imageFile') and os.path.exists(card['imageFile']):
                        st.image(card['imageFile'], width=300)

                with col2:
                    st.audio(card['audioFile'])

                st.divider()

        if result['card_count'] > 10:
            st.info(f"Showing 10 of {result['card_count']} cards")

        # Download button
        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            with open(result['apkg_path'], 'rb') as f:
                st.download_button(
                    label="📥 Download APKG",
                    data=f,
                    file_name=os.path.basename(result['apkg_path']),
                    mime="application/apkg",
                    use_container_width=True
                )

        with col2:
            if st.button("🔄 Create Another Deck", use_container_width=True):
                # Clean up session-specific directory
                session_dir = Path("tmp") / st.session_state.session_id
                shutil.rmtree(session_dir, ignore_errors=True)
                st.session_state.processing = False
                st.session_state.completed = False
                st.session_state.result = None
                st.rerun()

    else:  # Separate decks mode
        st.success(f"✅ Successfully generated {result['total_cards']} cards across {len(result['decks'])} decks!")

        # Show deck summaries
        st.subheader("Generated Decks")
        for deck in result['decks']:
            with st.expander(f"📦 {deck['name']} ({deck['card_count']} cards)"):
                # Preview first 3 cards from this deck
                for i, card in enumerate(deck['cards'][:3]):
                    col1, col2 = st.columns([3, 2])

                    with col1:
                        sentence = card['sentence']
                        display_sentence = sentence if len(sentence) <= 100 else sentence[:100] + "..."
                        st.markdown(f"**#{i+1}:** {display_sentence}")
                        if card.get('imageFile') and os.path.exists(card['imageFile']):
                            st.image(card['imageFile'], width=200)

                    with col2:
                        st.audio(card['audioFile'])

                    st.divider()

                if deck['card_count'] > 3:
                    st.caption(f"Showing 3 of {deck['card_count']} cards")

            # Download button for this deck (outside expander)
            with open(deck['apkg_path'], 'rb') as f:
                st.download_button(
                    label=f"📥 Download {deck['name']}.apkg",
                    data=f,
                    file_name=os.path.basename(deck['apkg_path']),
                    mime="application/apkg",
                    use_container_width=True,
                    key=f"download_{deck['name']}"
                )
            st.write("")  # Add spacing

        # Download all button
        st.divider()

        # Create zip file with all decks
        work_dir = Path("tmp") / st.session_state.session_id
        zip_path = work_dir / "all_decks.zip"

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for deck in result['decks']:
                zipf.write(deck['apkg_path'], os.path.basename(deck['apkg_path']))

        with open(zip_path, 'rb') as f:
            st.download_button(
                label="📥 Download All Decks (ZIP)",
                data=f,
                file_name="all_decks.zip",
                mime="application/zip",
                use_container_width=True
            )

        # Create another deck button
        st.divider()
        if st.button("🔄 Create Another Deck", use_container_width=True):
            # Clean up session-specific directory
            session_dir = Path("tmp") / st.session_state.session_id
            shutil.rmtree(session_dir, ignore_errors=True)
            st.session_state.processing = False
            st.session_state.completed = False
            st.session_state.result = None
            st.rerun()

# Footer
st.divider()
st.caption("Look at the [source code on GitHub](https://github.com/theramjad/yt-subs2srs)")
