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
from modules.cache_manager import CacheManager, cleanup_old_sessions

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

# Cleanup old sessions on app startup (once per session)
if 'cleanup_done' not in st.session_state:
    try:
        cleanup_old_sessions(Path("tmp"), max_age_hours=1.0)
        st.session_state.cleanup_done = True
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

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
if 'transcription_cache' not in st.session_state:
    st.session_state.transcription_cache = {}  # {video_name: cached_data}
if 'can_regenerate' not in st.session_state:
    st.session_state.can_regenerate = False
if 'last_limits' not in st.session_state:
    st.session_state.last_limits = {'max_words': 15, 'limit_type': 'Soft Limit'}
if 'uploaded_video_names' not in st.session_state:
    st.session_state.uploaded_video_names = []
if 'use_video_tags' not in st.session_state:
    st.session_state.use_video_tags = True


def process_videos(uploaded_files, api_key: str, soft_limit: int, hard_limit: int, use_video_tags: bool = True, use_cache: bool = False):
    """Main processing pipeline for multiple MP4 files"""

    # Create session-specific temp directory for multi-user isolation
    work_dir = Path("tmp") / st.session_state.session_id
    work_dir.mkdir(parents=True, exist_ok=True)

    # Initialize cache manager
    cache_mgr = CacheManager(work_dir)

    try:
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Generate deck name from filenames
        if len(uploaded_files) == 1:
            deck_name = Path(uploaded_files[0].name).stem
        else:
            deck_name = f"Combined_{len(uploaded_files)}_videos"

        all_cards = []
        card_counter = 0

        # Process each video file
        for file_idx, uploaded_file in enumerate(uploaded_files):
            # Extract filename without extension
            video_name = Path(uploaded_file.name).stem

            # Check if we have cached transcript
            cached_data = cache_mgr.get_transcript(video_name) if use_cache else None

            if cached_data:
                # Use cached data
                status_text.text(f"📦 Using cached transcription for {uploaded_file.name}...")
                words = cache_mgr.words_to_objects(cached_data['words'])
                video_path = cached_data['video_path']
                audio_path = cached_data['audio_path']

                # Re-extract audio if it was deleted
                if not os.path.exists(audio_path):
                    status_text.text(f"🎵 Re-extracting audio from {uploaded_file.name}...")
                    audio_path = extract_audio(video_path, str(cache_mgr.source_dir))
                    # Update cache with new audio path
                    cache_mgr.save_transcript(video_name, words, video_path, audio_path)

                progress = int((file_idx / len(uploaded_files)) * 50)
                progress_bar.progress(progress)
            else:
                # Step 1: Save uploaded MP4 file
                status_text.text(f"📁 Saving {uploaded_file.name}...")
                video_path = cache_mgr.source_dir / uploaded_file.name
                with open(video_path, 'wb') as f:
                    f.write(uploaded_file.read())

                progress = int((file_idx / len(uploaded_files)) * 10)
                progress_bar.progress(progress)

                # Step 2: Extract audio
                status_text.text(f"🎵 Extracting audio from {uploaded_file.name}...")
                audio_path = extract_audio(str(video_path), str(cache_mgr.source_dir))

                progress = int((file_idx / len(uploaded_files)) * 20) + 10
                progress_bar.progress(progress)

                # Step 3: Transcribe
                status_text.text(f"🎤 Transcribing {uploaded_file.name} (this may take several minutes)...")
                words = transcribe_audio(audio_path, api_key)

                # Cache the transcript
                cache_mgr.save_transcript(video_name, words, str(video_path), audio_path)

            progress = int((file_idx / len(uploaded_files)) * 30) + 20
            progress_bar.progress(progress)

            # Step 4: Segment into sentences
            status_text.text(f"✂️ Segmenting {uploaded_file.name} into sentences...")
            sentences = segment_into_sentences(words, soft_limit=soft_limit, hard_limit=hard_limit)
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
                    'sentence': sentence.text,
                    'video_name': video_name  # Store video name for tagging
                }

                all_cards.append(card)

            # Keep source audio/video files for regeneration (cleaned up after 1 hour)

        # Create single APKG with all cards
        status_text.text("📦 Creating Anki deck package...")
        progress_bar.progress(90)

        output_path = str(work_dir / f"{deck_name}.apkg")
        create_anki_deck(all_cards, deck_name, output_path, use_video_tags=use_video_tags)

        # Complete
        progress_bar.progress(100)
        status_text.text("✅ Complete!")

        # Store video names for regeneration
        video_names = [Path(f.name).stem for f in uploaded_files]

        return {
            'mode': 'combined',
            'deck_name': deck_name,
            'apkg_path': output_path,
            'card_count': len(all_cards),
            'preview_cards': all_cards,
            'video_names': video_names
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

        st.info("💡 All uploaded videos will be combined into a single Anki deck")

        use_video_tags = st.checkbox(
            "Add video name as tag to each card",
            value=True,
            help="Tags each card with its source video name. Useful for filtering cards by video in Anki (e.g., tag 'video1' for all cards from video1.mp4). Recommended when uploading multiple videos."
        )

        api_key = st.text_input(
            "AssemblyAI API Key",
            type="password",
            help="Get your free API key at assemblyai.com"
        )

        st.markdown("#### Word Limit Settings")
        col1, col2 = st.columns(2)

        with col1:
            max_words = st.number_input(
                "Maximum Words per Sentence",
                min_value=3,
                max_value=50,
                value=15,
                help="Maximum number of words per sentence. Note: 'Words' are determined by AssemblyAI's tokenization (e.g., は=1 word, 勉強=1 word, です=1 word)."
            )

        with col2:
            limit_type = st.radio(
                "Limit Type",
                options=["Soft Limit", "Hard Limit"],
                index=0,
                help=(
                    "**Soft Limit**: Tries to split at max words, but only when Japanese punctuation is found (。！？、). "
                    "Sentences may exceed the limit if no punctuation appears. Good for natural sentence breaks.\n\n"
                    "**Hard Limit**: Always splits at exactly max words, regardless of punctuation or sentence structure. "
                    "Guarantees no sentence exceeds the limit, but may split mid-sentence."
                ),
                horizontal=True
            )

        submit = st.form_submit_button("🚀 Generate Deck", use_container_width=True)

    if submit:
        if not uploaded_files or not api_key:
            st.error("Please provide both MP4 file(s) and API key")
        else:
            st.session_state.processing = True

            # Convert limit_type to soft_limit and hard_limit parameters
            if limit_type == "Soft Limit":
                soft_limit = max_words
                hard_limit = 50  # Effectively no hard limit
            else:  # Hard Limit
                soft_limit = max_words
                hard_limit = max_words  # Both limits are the same

            try:
                with st.spinner("Processing..."):
                    result = process_videos(uploaded_files, api_key, soft_limit, hard_limit, use_video_tags=use_video_tags, use_cache=False)

                    st.session_state.result = result
                    st.session_state.completed = True
                    st.session_state.can_regenerate = True
                    st.session_state.last_limits = {'max_words': max_words, 'limit_type': limit_type}
                    st.session_state.use_video_tags = use_video_tags
                    st.session_state.uploaded_video_names = result['video_names']
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.session_state.processing = False

else:
    # Show results
    result = st.session_state.result
    st.success(f"✅ Successfully generated {result['card_count']} cards in **{result['deck_name']}**!")

    # Preview cards
    st.subheader("Card Preview")
    for i, card in enumerate(result['preview_cards'][:15]):  # Show first 15 cards
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

    if result['card_count'] > 15:
        st.info(f"Showing 15 of {result['card_count']} cards")

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
            st.session_state.can_regenerate = False
            st.session_state.transcription_cache = {}
            st.rerun()

    # Regeneration section
    if st.session_state.can_regenerate:
        st.divider()
        st.subheader("🔄 Regenerate with Different Limits")
        st.info("💡 Using cached transcription - only re-segmenting (fast!)")

        with st.form("regenerate_form"):
            # Display current settings in a clean box
            tags_icon = "✅" if st.session_state.use_video_tags else "❌"
            tags_text = "Enabled" if st.session_state.use_video_tags else "Disabled"

            st.markdown(f"""
            <div style="background-color: #0E1117; padding: 16px; border-radius: 8px; margin-bottom: 16px; border: 1px solid #262730;">
                <div style="margin-bottom: 12px; color: #FAFAFA; font-weight: 600;">📋 Current Settings</div>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; color: #FAFAFA;">Max Words per Sentence</td>
                        <td style="padding: 8px 0; text-align: right; color: #FAFAFA; font-weight: 600;">{st.session_state.last_limits['max_words']}</td>
                    </tr>
                    <tr style="border-top: 1px solid #262730;">
                        <td style="padding: 8px 0; color: #FAFAFA;">Limit Type</td>
                        <td style="padding: 8px 0; text-align: right; color: #FAFAFA; font-weight: 600;">{st.session_state.last_limits['limit_type']}</td>
                    </tr>
                    <tr style="border-top: 1px solid #262730;">
                        <td style="padding: 8px 0; color: #FAFAFA;">Video Name Tags</td>
                        <td style="padding: 8px 0; text-align: right; color: #FAFAFA; font-weight: 600;">{tags_icon} {tags_text}</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                new_max_words = st.number_input(
                    "New Maximum Words",
                    min_value=3,
                    max_value=50,
                    value=st.session_state.last_limits['max_words'],
                    help="Maximum number of words per sentence"
                )

            with col2:
                new_limit_type = st.radio(
                    "New Limit Type",
                    options=["Soft Limit", "Hard Limit"],
                    index=0 if st.session_state.last_limits['limit_type'] == "Soft Limit" else 1,
                    help=(
                        "**Soft Limit**: Tries to split at max words when punctuation found.\n\n"
                        "**Hard Limit**: Always splits at exactly max words."
                    ),
                    horizontal=True
                )

            regenerate_submit = st.form_submit_button("🔄 Regenerate Deck", use_container_width=True)

        if regenerate_submit:
            # Convert limit_type to soft_limit and hard_limit
            if new_limit_type == "Soft Limit":
                new_soft_limit = new_max_words
                new_hard_limit = 50
            else:
                new_soft_limit = new_max_words
                new_hard_limit = new_max_words

            # Create a "fake" uploaded_files list for regeneration
            # We need to get the actual files from cache
            work_dir = Path("tmp") / st.session_state.session_id
            cache_mgr = CacheManager(work_dir)

            class FakeUploadedFile:
                def __init__(self, name):
                    self.name = name

                def read(self):
                    return b''  # Not used when use_cache=True

            fake_files = [FakeUploadedFile(f"{name}.mp4") for name in result['video_names']]

            try:
                with st.spinner("Regenerating with new limits..."):
                    # Use cached transcriptions and same tag preference
                    new_result = process_videos(
                        fake_files,
                        "",  # API key not needed when using cache
                        new_soft_limit,
                        new_hard_limit,
                        use_video_tags=st.session_state.use_video_tags,
                        use_cache=True
                    )

                    st.session_state.result = new_result
                    st.session_state.last_limits = {'max_words': new_max_words, 'limit_type': new_limit_type}
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Regeneration failed: {str(e)}")

# Footer
st.divider()
st.caption("Look at the [source code on GitHub](https://github.com/theramjad/yt-subs2srs)")
