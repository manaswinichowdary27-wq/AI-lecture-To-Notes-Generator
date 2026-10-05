import os
import io
import re
import streamlit as st
from dotenv import load_dotenv

# Optional libraries
try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

try:
    from google import genai
except ImportError:
    genai = None


# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

st.set_page_config(
    page_title="AI Lecture-to-Notes Generator",
    page_icon="🎓",
    layout="wide"
)


# --------------------------------------------------
# AI Configuration
# --------------------------------------------------

API_KEY = os.getenv("GOOGLE_API_KEY")

client = None

if API_KEY and genai:
    client = genai.Client(api_key=API_KEY)


# --------------------------------------------------
# Basic text processing
# --------------------------------------------------

def clean_text(text):
    """Clean unnecessary spaces and blank lines."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def generate_basic_notes(text):
    """
    Simple fallback note generator.
    Used when Google Gemini API is not configured.
    """

    sentences = re.split(r'(?<=[.!?])\s+', text)

    sentences = [s.strip() for s in sentences if s.strip()]

    important = sentences[:10]

    notes = "## 📝 Lecture Notes\n\n"

    for sentence in important:
        notes += f"- {sentence}\n"

    return notes


# --------------------------------------------------
# Gemini AI
# --------------------------------------------------

def generate_ai_response(prompt):
    """Generate response using Gemini."""

    if not client:
        return None

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        st.error(f"AI Error: {e}")
        return None


def generate_notes(text):
    prompt = f"""
You are an AI study assistant.

Convert the following lecture into clear and easy study notes.

Include:

1. Lecture title
2. Short summary
3. Important concepts
4. Key points
5. Definitions
6. Examples
7. Important formulas or facts if available
8. Final revision points

Use simple language suitable for college students.

Lecture:

{text}
"""

    result = generate_ai_response(prompt)

    if result:
        return result

    return generate_basic_notes(text)


def generate_summary(text):
    prompt = f"""
Summarize the following lecture in simple language.

Give:
- Short summary
- Main idea
- 5 important points

Lecture:

{text}
"""

    result = generate_ai_response(prompt)

    if result:
        return result

    sentences = re.split(r'(?<=[.!?])\s+', text)
    return " ".join(sentences[:5])


def generate_key_concepts(text):
    prompt = f"""
Extract the most important concepts from this lecture.

For each concept provide:
- Concept name
- Simple explanation

Lecture:

{text}
"""

    result = generate_ai_response(prompt)

    if result:
        return result

    words = text.split()

    return "\n".join(
        f"- {word}"
        for word in words[:15]
    )


def generate_mcqs(text):
    prompt = f"""
Create 10 multiple-choice questions from the lecture below.

For every question provide:
- Question
- A
- B
- C
- D
- Correct answer

Keep the questions suitable for college exams.

Lecture:

{text}
"""

    result = generate_ai_response(prompt)

    if result:
        return result

    return "AI MCQ generation requires a Google Gemini API key."


def generate_exam_questions(text):
    prompt = f"""
Generate important examination questions from the following lecture.

Create:

### Short Answer Questions
5 questions.

### Long Answer Questions
5 questions.

### Very Important Questions
5 questions.

Lecture:

{text}
"""

    result = generate_ai_response(prompt)

    if result:
        return result

    return "AI question generation requires a Google Gemini API key."


def explain_simply(text):
    prompt = f"""
Explain the following lecture as if teaching a beginner.

Use:
- Very simple language
- Small paragraphs
- Real-life examples
- Easy bullet points

Lecture:

{text}
"""

    result = generate_ai_response(prompt)

    if result:
        return result

    return generate_basic_notes(text)


def create_revision_sheet(text):
    prompt = f"""
Create a one-page revision sheet for this lecture.

Include:

- Topic
- Important definitions
- Key concepts
- Important points
- Formulas
- Examples
- Quick revision tips

Keep it concise.

Lecture:

{text}
"""

    result = generate_ai_response(prompt)

    if result:
        return result

    return generate_basic_notes(text)


# --------------------------------------------------
# Audio to Text
# --------------------------------------------------

def audio_to_text(audio_file):
    """Convert recorded audio into text."""

    if sr is None:
        return "SpeechRecognition is not installed."

    try:
        recognizer = sr.Recognizer()

        audio_data = sr.AudioFile(audio_file)

        with audio_data as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio)

        return text

    except Exception as e:
        return f"Audio processing error: {e}"


# --------------------------------------------------
# YouTube transcript
# --------------------------------------------------

def extract_video_id(url):

    patterns = [
        r"v=([^&]+)",
        r"youtu\.be/([^?]+)",
        r"youtube\.com/shorts/([^?]+)"
    ]

    for pattern in patterns:

        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None


def get_youtube_transcript(url):

    if YouTubeTranscriptApi is None:
        return None

    video_id = extract_video_id(url)

    if not video_id:
        return None

    try:

        transcript = YouTubeTranscriptApi.get_transcript(
            video_id
        )

        text = " ".join(
            item["text"]
            for item in transcript
        )

        return text

    except Exception:
        return None


# --------------------------------------------------
# Session state
# --------------------------------------------------

if "lecture_text" not in st.session_state:
    st.session_state.lecture_text = ""

if "result" not in st.session_state:
    st.session_state.result = ""


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("🎓 AI Lecture-to-Notes Generator")

st.write(
    "Convert lectures, transcripts, audio and YouTube videos "
    "into structured study material using AI."
)


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

st.sidebar.title("📚 Features")

feature = st.sidebar.selectbox(
    "Select Feature",
    [
        "Generate Notes",
        "Summary",
        "Key Concepts",
        "MCQs",
        "Exam Questions",
        "Explain Simply",
        "Revision Sheet"
    ]
)


# --------------------------------------------------
# Input section
# --------------------------------------------------

st.header("📥 Lecture Input")

input_type = st.radio(
    "Choose input type",
    [
        "Paste Text",
        "Upload TXT",
        "Upload Audio",
        "YouTube Video"
    ],
    horizontal=True
)


# --------------------------------------------------
# Paste text
# --------------------------------------------------

if input_type == "Paste Text":

    text = st.text_area(
        "Paste your lecture/transcript here:",
        height=300,
        placeholder="Paste lecture content..."
    )

    if text:
        st.session_state.lecture_text = text


# --------------------------------------------------
# Upload TXT
# --------------------------------------------------

elif input_type == "Upload TXT":

    uploaded_file = st.file_uploader(
        "Upload a TXT file",
        type=["txt"]
    )

    if uploaded_file:

        text = uploaded_file.read().decode(
            "utf-8",
            errors="ignore"
        )

        st.session_state.lecture_text = text

        st.success("Lecture file loaded successfully.")


# --------------------------------------------------
# Upload Audio
# --------------------------------------------------

elif input_type == "Upload Audio":

    uploaded_audio = st.file_uploader(
        "Upload lecture audio",
        type=["wav", "mp3", "flac"]
    )

    if uploaded_audio:

        st.audio(uploaded_audio)

        if st.button("🎤 Convert Audio to Text"):

            with st.spinner("Converting audio to text..."):

                audio_bytes = io.BytesIO(
                    uploaded_audio.read()
                )

                # SpeechRecognition works best with WAV
                if uploaded_audio.name.lower().endswith(".wav"):

                    text = audio_to_text(audio_bytes)

                    st.session_state.lecture_text = text

                    st.success(
                        "Audio converted to text."
                    )

                else:

                    st.warning(
                        "For best results, upload WAV audio. "
                        "MP3 conversion requires FFmpeg."
                    )


# --------------------------------------------------
# YouTube
# --------------------------------------------------

elif input_type == "YouTube Video":

    youtube_url = st.text_input(
        "Enter YouTube video URL"
    )

    if st.button("📺 Get Transcript"):

        if youtube_url:

            with st.spinner(
                "Getting YouTube transcript..."
            ):

                text = get_youtube_transcript(
                    youtube_url
                )

                if text:

                    st.session_state.lecture_text = text

                    st.success(
                        "Transcript loaded successfully."
                    )

                else:

                    st.error(
                        "Could not retrieve the transcript."
                    )


# --------------------------------------------------
# Show lecture
# --------------------------------------------------

if st.session_state.lecture_text:

    st.divider()

    st.subheader("📄 Lecture Content")

    with st.expander("View lecture text"):

        st.write(
            st.session_state.lecture_text
        )


# --------------------------------------------------
# Generate
# --------------------------------------------------

if st.session_state.lecture_text:

    st.divider()

    if st.button(
        "✨ Generate Study Material",
        type="primary"
    ):

        text = clean_text(
            st.session_state.lecture_text
        )

        with st.spinner(
            "AI is preparing your study material..."
        ):

            if feature == "Generate Notes":

                result = generate_notes(text)

            elif feature == "Summary":

                result = generate_summary(text)

            elif feature == "Key Concepts":

                result = generate_key_concepts(text)

            elif feature == "MCQs":

                result = generate_mcqs(text)

            elif feature == "Exam Questions":

                result = generate_exam_questions(text)

            elif feature == "Explain Simply":

                result = explain_simply(text)

            elif feature == "Revision Sheet":

                result = create_revision_sheet(text)

            else:

                result = "Please select a feature."

            st.session_state.result = result


# --------------------------------------------------
# Output
# --------------------------------------------------

if st.session_state.result:

    st.divider()

    st.header("📚 Generated Study Material")

    st.markdown(
        st.session_state.result
    )

    st.download_button(
        label="⬇️ Download Notes",
        data=st.session_state.result,
        file_name="lecture_notes.txt",
        mime="text/plain"
    )


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.divider()

st.caption(
    "AI Lecture-to-Notes Generator | Python + Streamlit + Gemini"
)

