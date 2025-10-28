import streamlit as st
import google.generativeai as genai
import re # <--- NEW: Added for robust parsing

# ----------------- CONFIG -----------------

# Using your placeholder API key
# REMINDER: Replace with your actual key for deployment.
genai.configure(api_key="AIzaSyDXjTyyhFWhyJPOV87y7XPnjQzdMXC6kBs")

# The layout is set to 'wide' for a modern look.
st.set_page_config(page_title="InterviewMate Pro", page_icon="🤖", layout="wide") 
st.title("InterviewMate Pro - Your AI Interview Mentor")
st.markdown("A smarter way to practice interviews.")
st.markdown("---")
# ----------------- BACKGROUND IMAGE -----------------

page_bg_img = """
<style>
.stApp {
background-image: url("https://images.unsplash.com/photo-1655841439659-0afc60676b70?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&q=80&w=1740");
background-size: cover;
background-attachment: fixed;
background-repeat: no-repeat;
background-position: center;
backdrop-filter: blur(10px);
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

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
st.subheader("1. 🧑‍💻 Define Your Role and Level")
role_input = st.text_input("Enter the specific job role:", 
                          value=st.session_state.role, 
                          placeholder="e.g., Python Developer, UX Designer, Financial Analyst")

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
        st.info("👆 Enter a job role in Step 1 to begin your AI-powered mock interview! Check the **Settings** menu (>>) left to select your job level.")
