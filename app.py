import streamlit as st
import google.generativeai as genai
import re # <--- NEW: Added for robust parsing

# ----------------- CONFIG -----------------

# Using your placeholder API key
# REMINDER: Replace with your actual key for deployment.
genai.configure(api_key="AIzaSyDXjTyyhFWhyJPOV87y7XPnjQzdMXC6kBs")

# The layout is set to 'wide' for a modern look.
st.set_page_config(page_title="InterviewMate Pro", page_icon="🤖", layout="wide") 

# ----------------- VIDEO BACKGROUND AND CUSTOM STYLES -----------------

page_bg_img = """
<style>
/* Keyframe for the subtle fade-in animation */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* --- CURSOR ANIMATION ELEMENTS --- */
@keyframes cursorPulse {
    0% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 0.8; }
    100% { transform: scale(1); opacity: 0.5; }
}

#custom-cursor {
    position: fixed;
    width: 15px; /* Size of the custom cursor */
    height: 15px;
    border-radius: 50%;
    background-color: rgba(255, 255, 255, 0.5); /* Semi-transparent white */
    pointer-events: none; /* Crucial: allows clicks to pass through */
    transform: translate(-50%, -50%); /* Center the dot */
    transition: transform 0.1s ease-out, background-color 0.1s ease-out; /* Smooth movement */
    z-index: 9999; /* Always on top */
    /* Subtle pulsing animation */
    animation: cursorPulse 1.5s infinite alternate;
}

/* State when hovering over interactive elements (optional, but good UX) */
.stApp:hover #custom-cursor {
    background-color: rgba(26, 140, 255, 0.8); /* Change color on hover to blue */
    transform: translate(-50%, -50%) scale(1.5); /* Enlarge cursor on hover */
    animation: none; /* Stop pulse when interacting */
}
/* --- END CURSOR ANIMATION ELEMENTS --- */


/* --- VIDEO BACKGROUND STYLES --- */
#video-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: -100; /* Position behind Streamlit content */
    overflow: hidden;
}

#video-bg {
    min-width: 100%; 
    min-height: 100%;
    width: auto;
    height: auto;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    object-fit: cover;
}

.video-overlay {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 100%;
    /* Dark overlay for text readability */
    background-color: rgba(0, 0, 0, 0.75); 
    z-index: -99;
}

.stApp {
    /* Set app background to transparent so video can be seen */
    background: transparent; 
    background-attachment: fixed;
    background-repeat: no-repeat;
    background-position: center;
    backdrop-filter: blur(10px); /* Keep the blur effect */
}

/* Custom styles for the centered, animated title */
.main-title {
    text-align: center;
    font-size: 3.5rem; /* Large font size for desktop */
    font-weight: 800; /* Bold */
    color: #FFFFFF; /* Bright white */
    margin-bottom: 0px; /* Reduce space before subtitle */
    font-family: 'Helvetica Neue', Arial, sans-serif; /* Minimalist font */
    animation: fadeIn 1s ease-out; /* Apply animation */
    white-space: nowrap; /* CRUCIAL: Forces text to stay on one line on desktop */
}

/* MEDIA QUERY FOR MOBILE: Adjust font size on smaller screens to prevent overflow/wrapping */
@media (max-width: 600px) {
    .main-title {
        font-size: 2.5rem; /* Smaller font size for mobile */
        white-space: nowrap; /* Ensure text remains on one line */
    }
}

/* Custom styles for the centered subtitle */
.sub-mentor-text {
    text-align: center;
    font-size: 1.25rem; /* Subtitle font size */
    font-weight: 300; /* Light font weight */
    color: #CCCCCC; /* Light gray color */
    margin-top: 0px; /* Align closely with title */
    margin-bottom: 1rem;
    font-family: 'Helvetica Neue', Arial, sans-serif; /* Minimalist font */
    animation: fadeIn 1.5s ease-out; /* Delayed animation */
}

/* Hide Streamlit's default title and markdown elements */
.stApp header {
    visibility: hidden;
    height: 0;
}
.stApp h1 {
    visibility: hidden;
    height: 0;
}
</style>

<!-- Video and Overlay container injected via st.markdown -->
<div id="video-container">
    <!-- 
        Updated: Added 'playsinline' for better compatibility, especially on mobile/iOS.
        Crucially, we rely on 'autoplay', 'muted', and 'loop' to work together.
    -->
    <video id="video-bg" autoplay muted loop playsinline> 
        <source src="https://cdn.pixabay.com/video/2022/11/13/138770-770553751_large.mp4" type="video/mp4">
        Your browser does not support the video tag.
    </video>
    <div class="video-overlay"></div>
</div>

<script>
    // JavaScript to make the custom cursor follow the mouse
    const cursor = document.getElementById('custom-cursor');
    document.addEventListener('mousemove', e => {
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';
    });
</script>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# ----------------- CUSTOM CENTERED HEADER -----------------

# Replaced st.title and st.markdown with custom HTML for centering and styling
st.markdown('<div class="main-title">InterviewMate Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-mentor-text">Your AI Interview Mentor</div>', unsafe_allow_html=True)

st.markdown("---")
# ----------------- END CUSTOM HEADER -----------------

# Use gemini-2.5-flash for fast and effective generation
MODEL = "gemini-2.5-flash" 

# ----------------- SESSION STATE -----------------
# Initialize state variables
if "questions" not in st.session_state:
    st.session_state.questions = []
if "role" not in st.session_state:
    st.session_state.role = ""
if "level" not in st.session_state: 
    st.session_state.level = "Junior/Entry"
if "user_answer" not in st.session_state:
    st.session_state.user_answer = ""
if "feedback" not in st.session_state:
    st.session_state.feedback = ""
if "feedback_language" not in st.session_state:
    st.session_state.feedback_language = "Hinglish"
    
# Function to clear session and restart
def clear_session():
    """Resets all session state variables to restart the process."""
    st.session_state.questions = []
    st.session_state.role = ""
    st.session_state.level = "Junior/Entry"
    st.session_state.user_answer = ""
    st.session_state.feedback = ""
    st.session_state.feedback_language = "Hinglish"
    st.rerun() 

# ----------------- SIDEBAR: Controls & Options -----------------
# Streamlit handles the sidebar's initial state and the "=" menu icon automatically.
with st.sidebar:
    
    st.header("⚙️ Interview Settings")
    
    # NEW OPTION: Job Level
    st.session_state.level = st.selectbox(
        "Select Job Level:",
        ("Junior/Entry", "Mid-Level/Senior", "Lead/Architect"),
        key="level_select",
        help="This affects the complexity of the generated questions and feedback."
    )
    
    st.markdown("---")
    
    # Restart Button
    st.button("Start New Interview", on_click=clear_session, type="secondary")
    

# ----------------- Step 1: Enter Job Role -----------------
st.subheader("Define Your Role and Level")
role_input = st.text_input("Enter the specific job role:", 
                          value=st.session_state.role, 
                          placeholder="e.g., Software Developer, Psychologist, Financial Analyst...")

# Check if role or level changed to trigger new questions
level_changed = st.session_state.level != st.session_state.get("last_level", "Junior/Entry")
if role_input and (role_input != st.session_state.role or level_changed):
    st.session_state.role = role_input
    st.session_state.questions = []  # Clear previous questions
    st.session_state.user_answer = "" # Clear previous answer
    st.session_state.feedback = "" # Clear previous feedback
    st.session_state.last_level = st.session_state.level # Store current level

# ----------------- Step 2: Generate Questions -----------------
if st.session_state.role:
    if not st.session_state.questions:
        with st.spinner(f"Preparing interview questions for **{st.session_state.level} {st.session_state.role}**..."):
            try:
                model = genai.GenerativeModel(MODEL) 
                
                # --- FIX 1: STRICTER PROMPT ---
                prompt = (
                    f"Generate 3 simple, realistic, and challenging interview questions "
                    f"for a **{st.session_state.level} {st.session_state.role}** position. "
                    f"Ensure the questions are appropriate for the selected level. "
                    f"Format them **strictly as a numbered list (1. Question, 2. Question, 3. Question)** with NO extra introductory or concluding text, notes, or explanations whatsoever."
                )
                response = model.generate_content(prompt)
                
                # --- FIX 2: ROBUST PARSING WITH REGEX ---
                # Use regex to find lines starting with a number, a period, and optional whitespace.
                # This ensures we only capture the actual numbered questions.
                question_lines = re.findall(r"^\s*\d+\.\s*(.+)", response.text, re.MULTILINE)
                st.session_state.questions = [q.strip() for q in question_lines if q.strip()]
                
                if not st.session_state.questions: # Fallback for completely malformed response
                    st.session_state.questions = ["Could not generate specific questions. Please try again or refine the role."]


            except Exception as e:
                st.error(f"Error generating questions: {e}")
                st.session_state.role = "" 

    # ✅ Show questions
    if st.session_state.questions:
        st.subheader(f"2. Your Questions for **{st.session_state.level} {st.session_state.role}**:")
        
        # Display questions using st.container with a border
        questions_container = st.container(border=True)
        with questions_container:
            for i, question in enumerate(st.session_state.questions):
                # The question text is already clean, so we just prefix it here.
                st.write(f"**Q{i+1}:** {question}")

        st.markdown("---")

        # ----------------- Step 3: Answer Section -----------------
        st.subheader("3. 📝 Provide Your Answer and Select Language")
        st.markdown("Choose a question and type your full answer below. Focus on clarity, structure, and relevance.")
        
        # --- LANGUAGE SELECTION ---
        feedback_options = ("Hinglish", "English", "Polish")
        language_index = feedback_options.index(st.session_state.feedback_language) if st.session_state.feedback_language in feedback_options else 0
        
        st.session_state.feedback_language = st.radio(
            "Select Feedback Language:",
            feedback_options,
            index=language_index,
            horizontal=True,
            key="lang_radio"
        )
        st.markdown("---")
        # --- END LANGUAGE SELECTION ---

        # Text input area
        st.session_state.user_answer = st.text_area(
            "Your Comprehensive Answer (for one question):", 
            value=st.session_state.user_answer, 
            height=200, 
            key="answer_input",
            placeholder="Type your detailed, structured answer here..."
        )
        
        # ----------------- Step 4: Get Feedback -----------------
        if st.button("✨ Get Detailed AI Feedback", type="primary"):
            if st.session_state.user_answer.strip():
                with st.spinner("Analyzing your answer and generating detailed feedback..."):
                    try:
                        model = genai.GenerativeModel(MODEL)
                        
                        # Define prompt based on selected language
                        selected_language = st.session_state.feedback_language
                        
                        if selected_language == "English":
                            language_instruction = "Provide professional and constructive feedback in **pure English**."
                        elif selected_language == "Polish":
                            language_instruction = "Provide professional and constructive feedback in **pure Polish** (język polski)."
                        else: # Hinglish
                            language_instruction = "Provide professional and constructive feedback in **Hinglish (a mix of Hindi and English)**. **Ensure all Hindi words are written using the Roman (English) alphabet.**"

                        feedback_prompt = (
                            f"Evaluate this interview answer for a **{st.session_state.level} {st.session_state.role}** position.\n\n"
                            f"Answer to evaluate: {st.session_state.user_answer}\n\n"
                            f"{language_instruction} Also, highlight **Strengths**, **Areas for Improvement (Weaknesses)**, and give a numerical **Score out of 10** for the answer quality. Use clear and professional markdown formatting (like bolding and bullet points) to structure the feedback."
                        )

                        feedback_response = model.generate_content(feedback_prompt)
                        st.session_state.feedback = feedback_response.text
                    except Exception as e:
                        st.error(f"Error generating feedback: {e}")
            else:
                st.warning("🚨 Please type your answer in the box above before requesting feedback.")

# Display feedback if available
if st.session_state.feedback:
    st.markdown("---")
    st.subheader("💬 Detailed AI Feedback:")
    feedback_container = st.container(border=True)
    with feedback_container:
        st.markdown(st.session_state.feedback)

# Info if no role entered
else:
    if not st.session_state.role:
        st.info("Enter a job role to start your AI mock interview! Adjust your job level in Settings (>>)")
