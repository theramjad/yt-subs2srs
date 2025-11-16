"""Subs2SRS Anki Card Generator - Streamlit App"""
import os
import shutil
import logging
import streamlit as st
from pathlib import Path
from modules.video_downloader import download_video
from modules.audio_processor import extract_audio, extract_audio_clip
from modules.transcriber import transcribe_audio
from modules.segmenter import segment_into_sentences, filter_valid_sentences
from modules.screenshot import extract_screenshot
from modules.anki_deck import create_anki_deck

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
st.markdown('<p class="subtitle">Convert YouTube videos to Anki flashcard decks</p>', unsafe_allow_html=True)

# Initialize session state
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'completed' not in st.session_state:
    st.session_state.completed = False
if 'apkg_path' not in st.session_state:
    st.session_state.apkg_path = None


def process_video(youtube_url: str, api_key: str):
    """Main processing pipeline"""

    # Create temp directory
    work_dir = Path("tmp") / "current"
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Download video
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("⬇️ Downloading video (360p)...")
        progress_bar.progress(10)
        video_path, title = download_video(youtube_url, str(work_dir))

        st.info(f"📹 **{title}**")

        # Step 2: Extract audio
        status_text.text("🎵 Extracting audio...")
        progress_bar.progress(20)
        audio_path = extract_audio(video_path, str(work_dir))

        # Re-download video for screenshots (was deleted after audio extraction)
        status_text.text("⬇️ Re-downloading video for screenshots...")
        progress_bar.progress(25)
        video_path, _ = download_video(youtube_url, str(work_dir))

        # Step 3: Transcribe
        status_text.text("🎤 Transcribing audio (this may take several minutes)...")
        progress_bar.progress(30)
        words = transcribe_audio(audio_path, api_key)

        # Step 4: Segment into sentences
        status_text.text("✂️ Segmenting into sentences...")
        progress_bar.progress(60)
        sentences = segment_into_sentences(words)
        valid_sentences = filter_valid_sentences(sentences)

        st.success(f"Created {len(valid_sentences)} sentences")

        # Step 5: Generate cards
        status_text.text(f"🎴 Generating {len(valid_sentences)} cards...")
        progress_bar.progress(70)

        cards = []
        for i, sentence in enumerate(valid_sentences):
            # Update progress
            card_progress = 70 + int(20 * (i / len(valid_sentences)))
            progress_bar.progress(card_progress)

            # Extract audio clip
            audio_clip_path = str(work_dir / f"clip_{i}.mp3")
            extract_audio_clip(
                audio_path,
                sentence.start_time,
                sentence.end_time,
                audio_clip_path
            )

            # Extract screenshot
            screenshot_path = str(work_dir / f"screenshot_{i}.webp")
            extract_screenshot(
                video_path,
                sentence.start_time,
                screenshot_path
            )

            cards.append({
                'audioFile': audio_clip_path,
                'imageFile': screenshot_path,
                'sentence': sentence.text
            })

        # Delete video to save space
        os.remove(video_path)

        # Step 6: Create APKG
        status_text.text("📦 Creating Anki deck package...")
        progress_bar.progress(90)

        output_path = str(work_dir / f"{title}.apkg")
        create_anki_deck(cards, title, output_path)

        # Complete
        progress_bar.progress(100)
        status_text.text("✅ Complete!")

        return output_path, len(cards), cards[:3]  # Return path, count, and preview

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise


# Main UI
if not st.session_state.completed:
    # Input form
    with st.form("input_form"):
        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Enter the URL of a Japanese YouTube video"
        )

        api_key = st.text_input(
            "AssemblyAI API Key",
            type="password",
            help="Get your free API key at assemblyai.com"
        )

        submit = st.form_submit_button("🚀 Generate Deck", use_container_width=True)

    if submit:
        if not youtube_url or not api_key:
            st.error("Please provide both YouTube URL and API key")
        else:
            st.session_state.processing = True

            try:
                with st.spinner("Processing..."):
                    apkg_path, card_count, preview_cards = process_video(youtube_url, api_key)

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
        st.subheader("Card Preview (first 3 cards)")

        for i, card in enumerate(st.session_state.preview_cards):
            with st.expander(f"Card {i+1}: {card['sentence'][:50]}..."):
                # Show screenshot
                st.image(card['imageFile'], use_container_width=True)

                # Show audio
                st.audio(card['audioFile'])

                # Show sentence
                st.markdown(f"**Sentence:** {card['sentence']}")

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
st.caption("Made with ❤️ using Streamlit • Powered by AssemblyAI, yt-dlp, and genanki")
