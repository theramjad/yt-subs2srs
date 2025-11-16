"""Subs2SRS Anki Card Generator - Streamlit App"""
import os
import shutil
import logging
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

# Page config
st.set_page_config(
    page_title="Subs2SRS Anki Card Generator",
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
st.markdown('<h1 class="main-header">🎴 Subs2SRS Anki Card Generator</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Convert MP4 videos to Anki flashcard decks</p>', unsafe_allow_html=True)

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'completed' not in st.session_state:
    st.session_state.completed = False
if 'apkg_path' not in st.session_state:
    st.session_state.apkg_path = None


def process_videos(uploaded_files, deck_name: str, api_key: str):
    """Main processing pipeline for multiple MP4 files"""

    # Create temp directory
    work_dir = Path("tmp") / "current"
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        progress_bar = st.progress(0)
        status_text = st.empty()

        all_cards = []
        card_counter = 0

        # Process each video file
        for file_idx, uploaded_file in enumerate(uploaded_files):
            # Extract filename without extension for prefix
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

            for i, sentence in enumerate(valid_sentences):
                # Update progress (40-80% for card generation)
                if len(valid_sentences) > 0:
                    sentence_progress = 40 + int(40 * (i / len(valid_sentences)))
                    progress_bar.progress(min(sentence_progress, 80))

                # Extract audio clip
                audio_clip_path = str(work_dir / f"clip_{card_counter}.mp3")
                extract_audio_clip(
                    audio_path,
                    sentence.start_time,
                    sentence.end_time,
                    audio_clip_path
                )

                # Extract screenshot at sentence start time
                screenshot_path = str(work_dir / f"screenshot_{card_counter}.jpg")
                frame_extractor.extract_frame(sentence.start_time, screenshot_path)

                # Add filename prefix to sentence if multiple videos
                sentence_text = sentence.text
                if len(uploaded_files) > 1:
                    sentence_text = f"[{video_name}] {sentence.text}"

                all_cards.append({
                    'audioFile': audio_clip_path,
                    'imageFile': screenshot_path,
                    'sentence': sentence_text
                })

                card_counter += 1

            # Delete source audio file to save space
            if os.path.exists(audio_path):
                os.remove(audio_path)

        # Step 6: Create APKG
        status_text.text("📦 Creating Anki deck package...")
        progress_bar.progress(90)

        output_path = str(work_dir / f"{deck_name}.apkg")
        create_anki_deck(all_cards, deck_name, output_path)

        # Complete
        progress_bar.progress(100)
        status_text.text("✅ Complete!")

        return output_path, len(all_cards), all_cards  # Return path, count, and all cards for preview

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

        deck_name = st.text_input(
            "Deck Name",
            placeholder="My Japanese Deck",
            help="Name for your Anki deck"
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
        elif not deck_name:
            st.error("Please provide a deck name")
        else:
            st.session_state.processing = True

            try:
                with st.spinner("Processing..."):
                    apkg_path, card_count, preview_cards = process_videos(uploaded_files, deck_name, api_key)

                    st.session_state.apkg_path = apkg_path
                    st.session_state.card_count = card_count
                    st.session_state.preview_cards = preview_cards
                    st.session_state.completed = True
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.session_state.processing = False

else:
    # Show results
    st.success(f"✅ Successfully generated {st.session_state.card_count} cards!")

    # Preview cards
    if st.session_state.preview_cards:
        st.subheader("Card Preview")

        # Card display with thumbnail and audio
        for i, card in enumerate(st.session_state.preview_cards):
            with st.container():
                col1, col2 = st.columns([3, 2])

                with col1:
                    sentence = card['sentence']
                    display_sentence = sentence if len(sentence) <= 100 else sentence[:100] + "..."
                    st.markdown(f"**#{i+1}:** {display_sentence}")
                    if len(sentence) > 100:
                        with st.expander("Show full sentence"):
                            st.write(sentence)

                    # Display thumbnail if available
                    if card.get('imageFile') and os.path.exists(card['imageFile']):
                        st.image(card['imageFile'], width=300)

                with col2:
                    st.audio(card['audioFile'])

                st.divider()

    # Download button
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        with open(st.session_state.apkg_path, 'rb') as f:
            st.download_button(
                label="📥 Download APKG",
                data=f,
                file_name=os.path.basename(st.session_state.apkg_path),
                mime="application/apkg",
                use_container_width=True
            )

    with col2:
        if st.button("🔄 Create Another Deck", use_container_width=True):
            # Clean up
            shutil.rmtree("tmp/current", ignore_errors=True)
            st.session_state.processing = False
            st.session_state.completed = False
            st.session_state.apkg_path = None
            st.rerun()

# Footer
st.divider()
st.caption("Made with ❤️ using Streamlit • Powered by AssemblyAI, FFmpeg, and genanki")
