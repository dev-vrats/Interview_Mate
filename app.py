import streamlit as st
import google.generativeai as genai
# Note: Removed speech_recognition, gTTS, threading, and os as they conflict
# with Streamlit's execution model and reliable web deployment.

# ----------------- CONFIG -----------------

# Using your placeholder API key
genai.configure(api_key="AIzaSyDXjTyyhFWhyJPOV87y7XPnjQzdMXC6kBs")

st.set_page_config(page_title="InterviewMate", page_icon="🤖", layout="centered")
st.title("🎯 InterviewMate - Your AI Interview Mentor")
st.markdown("---")

# Use gemini-2.5-flash for fast and effective generation
MODEL = "gemini-2.5-flash" 

# ----------------- SESSION STATE -----------------
# Initialize state variables
if "questions" not in st.session_state:
    st.session_state.questions = []
if "role" not in st.session_state:
    st.session_state.role = ""
if "user_answer" not in st.session_state:
    st.session_state.user_answer = ""
if "feedback" not in st.session_state:
    st.session_state.feedback = ""
if "feedback_language" not in st.session_state:
    st.session_state.feedback_language = "Hinglish"

# ----------------- Step 1: Enter Job Role -----------------
role_input = st.text_input("1.Enter the job role (e.g., Software Engineer, Marketing Manager):", 
                          value=st.session_state.role)

# Check if role changed to trigger new questions
if role_input and role_input != st.session_state.role:
    st.session_state.role = role_input
    st.session_state.questions = []  # Clear previous questions
    st.session_state.user_answer = "" # Clear previous answer
    st.session_state.feedback = "" # Clear previous feedback

# ----------------- Step 2: Generate Questions -----------------
if st.session_state.role:
    if not st.session_state.questions:
        with st.spinner(f"Preparing interview questions for **{st.session_state.role}**..."):
            try:
                model = genai.GenerativeModel(MODEL) 
                prompt = f"Generate 3 simple and realistic interview questions for a {st.session_state.role} position. Format them as a numbered list."
                response = model.generate_content(prompt)
                
                # Split and clean the response text
                st.session_state.questions = [
                    q.strip() for q in response.text.split("\n") 
                    if q.strip() and len(q.strip()) > 5 
                ]
            except Exception as e:
                st.error(f"Error generating questions. Please check your API key and ensure the environment has access to the internet. Error: {e}")
                st.session_state.role = "" # Reset role to prevent loop

    # ✅ Show questions
    if st.session_state.questions:
        st.subheader("2.Your Questions:")
        question_list = "\n".join(st.session_state.questions)
        st.markdown(question_list)

        st.markdown("---")

        # ----------------- Step 3: Answer Section -----------------
        st.subheader("3.Provide Your Answer")
        st.markdown("Choose one of the questions above and type your full answer below.")
        
        # --- NEW LANGUAGE SELECTION ---
        st.session_state.feedback_language = st.radio(
            "Select Feedback Language:",
            ("Hinglish", "English"),
            index=0 if st.session_state.feedback_language == "Hinglish" else 1,
            horizontal=True
        )
        st.markdown("---")
        # --- END NEW LANGUAGE SELECTION ---

        # Text input area
        st.session_state.user_answer = st.text_area(
            "Your Answer:", 
            value=st.session_state.user_answer, 
            height=200, 
            key="answer_input"
        )
        
        # ----------------- Step 4: Get Feedback -----------------
        if st.button("✨ Get Feedback on Answer", type="primary"):
            if st.session_state.user_answer.strip():
                with st.spinner("Analyzing your answer and generating feedback..."):
                    try:
                        model = genai.GenerativeModel(MODEL)
                        
                        # Define prompt based on selected language
                        selected_language = st.session_state.feedback_language
                        
                        if selected_language == "English":
                            language_instruction = "Provide professional and constructive feedback in **pure English**."
                        else: # Hinglish
                            language_instruction = "Provide professional and constructive feedback in **Hinglish (a mix of Hindi and English)**. **Ensure all Hindi words are written using the Roman (English) alphabet.**"

                        feedback_prompt = (
                            f"Evaluate this interview answer for a {st.session_state.role} position:\n\n"
                            f"Answer: {st.session_state.user_answer}\n\n"
                            f"{language_instruction} Also, highlight strengths, weaknesses, and give a numerical score out of 10. Use markdown for formatting."
                        )

                        feedback_response = model.generate_content(feedback_prompt)
                        st.session_state.feedback = feedback_response.text
                    except Exception as e:
                        st.error(f"Error generating feedback: {e}")
            else:
                st.warning("Please type your answer in the box above before getting feedback.")

# Display feedback if available
if st.session_state.feedback:
    st.markdown("---")
    st.subheader("💬 AI Feedback:")
    st.markdown(st.session_state.feedback)

# Info if no role entered
else:
    st.info("👆 Enter a job role above to start your mock interview!")
