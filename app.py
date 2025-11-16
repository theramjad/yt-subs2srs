"""Subs2SRS Anki Card Generator - Streamlit App"""
import os
import shutil
import logging
import streamlit as st
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
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
if 'video_progress' not in st.session_state:
    st.session_state.video_progress = {}


def process_single_video(uploaded_file, work_dir: Path, api_key: str, combined_mode: bool,
                        card_counter_lock: Lock, card_counter: dict, video_index: int,
                        total_videos: int, progress_containers: dict):
    """Process a single video file and return results"""
    try:
        video_name = Path(uploaded_file.name).stem

        # Update progress: Saving
        progress_containers[video_index]['status'].text(f"📁 Saving...")
        progress_containers[video_index]['progress'].progress(10)

        # Step 1: Save uploaded MP4 file
        video_path = work_dir / uploaded_file.name
        with open(video_path, 'wb') as f:
            f.write(uploaded_file.getvalue())

        # Update progress: Extracting audio
        progress_containers[video_index]['status'].text(f"🎵 Extracting audio...")
        progress_containers[video_index]['progress'].progress(20)

        # Step 2: Extract audio
        audio_path = extract_audio(str(video_path), str(work_dir))

        # Update progress: Transcribing
        progress_containers[video_index]['status'].text(f"🎤 Transcribing (may take several minutes)...")
        progress_containers[video_index]['progress'].progress(30)

        # Step 3: Transcribe
        words = transcribe_audio(audio_path, api_key)

        # Update progress: Segmenting
        progress_containers[video_index]['status'].text(f"✂️ Segmenting into sentences...")
        progress_containers[video_index]['progress'].progress(60)

        # Step 4: Segment into sentences
        sentences = segment_into_sentences(words)
        valid_sentences = filter_valid_sentences(sentences)

        progress_containers[video_index]['info'].info(f"**{video_name}**: {len(valid_sentences)} sentences")

        # Update progress: Generating cards
        progress_containers[video_index]['status'].text(f"🎴 Generating {len(valid_sentences)} cards...")
        progress_containers[video_index]['progress'].progress(70)

        # Step 5: Generate cards with screenshots
        frame_extractor = VideoFrameExtractor(str(video_path))
        video_cards = []

        for i, sentence in enumerate(valid_sentences):
            # Update card generation progress
            card_progress = 70 + int(25 * (i / max(len(valid_sentences), 1)))
            progress_containers[video_index]['progress'].progress(min(card_progress, 95))

            # Extract audio clip and screenshot
            if combined_mode:
                with card_counter_lock:
                    counter = card_counter['value']
                    card_counter['value'] += 1
                audio_clip_path = str(work_dir / f"clip_{counter}.mp3")
                screenshot_path = str(work_dir / f"screenshot_{counter}.jpg")
            else:
                audio_clip_path = str(work_dir / f"{video_name}_clip_{i}.mp3")
                screenshot_path = str(work_dir / f"{video_name}_screenshot_{i}.jpg")

            extract_audio_clip(audio_path, sentence.start_time, sentence.end_time, audio_clip_path)
            frame_extractor.extract_frame(sentence.start_time, screenshot_path)

            # Add filename prefix to sentence only in combined mode with multiple videos
            sentence_text = sentence.text
            if combined_mode and total_videos > 1:
                sentence_text = f"[{video_name}] {sentence.text}"

            card = {
                'audioFile': audio_clip_path,
                'imageFile': screenshot_path,
                'sentence': sentence_text
            }
            video_cards.append(card)

        # Delete source audio file to save space
        if os.path.exists(audio_path):
            os.remove(audio_path)

        # Update progress: Complete
        progress_containers[video_index]['status'].text(f"✅ Complete!")
        progress_containers[video_index]['progress'].progress(100)

        return {
            'video_name': video_name,
            'cards': video_cards,
            'card_count': len(video_cards)
        }

    except Exception as e:
        progress_containers[video_index]['status'].text(f"❌ Error: {str(e)}")
        logger.error(f"Processing {uploaded_file.name} failed: {str(e)}")
        raise


def process_videos(uploaded_files, deck_mode: str, api_key: str):
    """Main processing pipeline for multiple MP4 files with parallel processing"""

    # Create temp directory
    work_dir = Path("tmp") / "current"
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        combined_mode = (deck_mode == "Combined Deck")

        # Generate deck name for combined mode
        if combined_mode:
            if len(uploaded_files) == 1:
                deck_name = Path(uploaded_files[0].name).stem
            else:
                deck_name = f"Combined_{len(uploaded_files)}_videos"

        # Create progress UI for each video (max 3 columns)
        st.write(f"### Processing {len(uploaded_files)} video(s) in parallel (max 3 at a time)")

        progress_containers = {}
        num_videos = len(uploaded_files)

        # Create columns for progress tracking (max 3 per row)
        for row_start in range(0, num_videos, 3):
            row_videos = min(3, num_videos - row_start)
            cols = st.columns(row_videos)

            for col_idx in range(row_videos):
                video_idx = row_start + col_idx
                if video_idx < num_videos:
                    with cols[col_idx]:
                        st.markdown(f"**📹 {uploaded_files[video_idx].name}**")
                        progress_containers[video_idx] = {
                            'progress': st.progress(0),
                            'status': st.empty(),
                            'info': st.empty()
                        }

        # Shared state for thread-safe card counting
        card_counter_lock = Lock()
        card_counter = {'value': 0}

        # Process videos in parallel using ThreadPoolExecutor
        all_results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all videos for processing
            future_to_video = {
                executor.submit(
                    process_single_video,
                    uploaded_file,
                    work_dir,
                    api_key,
                    combined_mode,
                    card_counter_lock,
                    card_counter,
                    idx,
                    len(uploaded_files),
                    progress_containers
                ): (idx, uploaded_file) for idx, uploaded_file in enumerate(uploaded_files)
            }

            # Collect results as they complete
            for future in as_completed(future_to_video):
                idx, uploaded_file = future_to_video[future]
                try:
                    result = future.result()
                    all_results.append(result)
                except Exception as e:
                    logger.error(f"Video {uploaded_file.name} failed: {str(e)}")
                    st.error(f"Failed to process {uploaded_file.name}: {str(e)}")

        # Sort results by original order
        all_results.sort(key=lambda x: next(i for i, f in enumerate(uploaded_files) if Path(f.name).stem == x['video_name']))

        # Create deck(s) based on mode
        st.write("---")
        final_status = st.empty()
        final_progress = st.progress(0)

        if combined_mode:
            # Combine all cards into one deck
            final_status.text("📦 Creating combined Anki deck package...")
            final_progress.progress(90)

            all_cards = []
            for result in all_results:
                all_cards.extend(result['cards'])

            output_path = str(work_dir / f"{deck_name}.apkg")
            create_anki_deck(all_cards, deck_name, output_path)

            final_progress.progress(100)
            final_status.text("✅ Complete!")

            return {
                'mode': 'combined',
                'deck_name': deck_name,
                'apkg_path': output_path,
                'card_count': len(all_cards),
                'preview_cards': all_cards
            }
        else:
            # Create separate decks
            final_status.text("📦 Creating individual Anki deck packages...")
            decks = []

            for i, result in enumerate(all_results):
                final_progress.progress(int(90 + (i / len(all_results) * 10)))
                output_path = str(work_dir / f"{result['video_name']}.apkg")
                create_anki_deck(result['cards'], result['video_name'], output_path)
                decks.append({
                    'name': result['video_name'],
                    'cards': result['cards'],
                    'apkg_path': output_path,
                    'card_count': result['card_count']
                })

            final_progress.progress(100)
            final_status.text("✅ Complete!")

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
                shutil.rmtree("tmp/current", ignore_errors=True)
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

                # Download button for this deck
                with open(deck['apkg_path'], 'rb') as f:
                    st.download_button(
                        label=f"📥 Download {deck['name']}.apkg",
                        data=f,
                        file_name=os.path.basename(deck['apkg_path']),
                        mime="application/apkg",
                        use_container_width=True,
                        key=f"download_{deck['name']}"
                    )

        # Create another deck button
        st.divider()
        if st.button("🔄 Create Another Deck", use_container_width=True):
            shutil.rmtree("tmp/current", ignore_errors=True)
            st.session_state.processing = False
            st.session_state.completed = False
            st.session_state.result = None
            st.rerun()

# Footer
st.divider()
st.caption("Made with ❤️ using Streamlit • Powered by AssemblyAI, FFmpeg, and genanki")
