import streamlit as st
from backend import process_youtube_video, app, content_manager
from streamlit_mic_recorder import speech_to_text
from langchain_core.messages import HumanMessage, AIMessage
import os
import uuid
import traceback

# Clean CSS with minimal scrolling area
st.markdown("""
<style>
    /* Reduce main container padding */
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;  
    }
    
    /* Reduce header margin */
    .stTitle h1 {
        margin-bottom: 0.5rem !important;
    }
    
    /* Sidebar background */
    .css-1d391kg, .css-1lcbmhc {
        background-color: #FFFFFF !important;
    }
            
    /* Sidebar header styling */
    .sidebar-header {
        margin-top: 0.5rem !important;    /* Less margin above */
        margin-bottom: 1.5rem !important; /* More margin below */
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #F3C623;
        color: #10375C;
        font-size: 1.3em !important;
    }
    
    /* Adjust sidebar section spacing */
    .sidebar-section {
        margin-bottom: 1.5rem !important;
    }        
    
    /* Minimal message container */
    .messages-area {
        min-height: 300px;
        max-height: 65vh;
        overflow-y: auto;
        margin-bottom: 5px;  /* Reduced from 10px */
    }
    
    /* User message styling */
    .user-message {
        background: linear-gradient(135deg, #FFEAA7 0%, #FDCB6E 100%);
        color: #2D3436;
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        border: 1px solid #FDCB6E;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Assistant message styling */
    .assistant-message {
        background: linear-gradient(135deg, #74B9FF 0%, #0984E3 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 80%;
        border: 1px solid #74B9FF;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Error message styling */
    .error-message {
        background: linear-gradient(135deg, #FF7675 0%, #D63031 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 80%;
        border: 1px solid #FF7675;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Thinking message styling */
    .thinking-message {
        background: #f8f9fa;
        color: #6c757d;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 80%;
        border: 1px solid #dee2e6;
        font-style: italic;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #F3C623 0%, #EB8317 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        height: 44px;  /* Match input height */
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #EB8317 0%, #D35400 100%);
        color: white;
    }
    
    /* Chat input styling */
    .stChatInput>div>div>input {
        background-color: white;
        border: 2px solid #DFE6E9;
        border-radius: 25px;
        padding: 8px 16px;
        margin-top: 5px;  /* Reduced margin */
        margin-button: 10px;    
    }
    
    /* Remove margins and reduce spacing */
    .stChatInput {
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
    }
    
    section[data-testid="stHorizontalBlock"] {
        margin-bottom: 5px !important;  /* Reduced */
        gap: 10px !important;  /* Space between columns */
    }
    
    .stHorizontalBlock {
        gap: 10px !important;
    }
    
    /* Hide streamlit default elements */
    #MainMenu {visibility: visible !important;;}
    header {visibility: visible !important;;}
    footer{visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "content_loaded" not in st.session_state:
    st.session_state['content_loaded'] = False

if "current_source_url" not in st.session_state:
    st.session_state['current_source_url'] = ""

if "current_source_type" not in st.session_state:
    st.session_state['current_source_type'] = ""

if "thread_id" not in st.session_state:
    st.session_state['thread_id'] = str(uuid.uuid4())

if "waiting_for_response" not in st.session_state:
    st.session_state['waiting_for_response'] = False

if "debug_mode" not in st.session_state:
    st.session_state['debug_mode'] = False

# Language options
LANGUAGE_OPTIONS = {
    "English": "en",
    "Hindi": "hi", 
    "French": "fr",
    "Spanish": "es",
    "German": "de"
}

# --- Sidebar for Content Loading ---
st.sidebar.markdown('<div class="sidebar-header">📥 Content Sources</div>', unsafe_allow_html=True)

# Debug mode toggle
#st.session_state['debug_mode'] = st.sidebar.checkbox("Debug Mode", value=False)

# Content type selection
content_type = st.sidebar.radio(
    "Select Content Type",
    ["YouTube Video", "Web Content"],
    help="Choose the type of content to analyze"
)

if content_type == "YouTube Video":
    youtube_url = st.sidebar.text_input(
        "Enter YouTube URL",
        value=st.session_state.get('current_source_url', ''),
        placeholder="https://www.youtube.com/watch?v=..."
    )
    
    selected_language_name = st.sidebar.selectbox(
        "Select Transcript Language", 
        list(LANGUAGE_OPTIONS.keys())
    )
    language = LANGUAGE_OPTIONS[selected_language_name]
    
    load_button = st.sidebar.button("🎥 Load YouTube Video", type="primary")
    
    if load_button and youtube_url:
        with st.spinner("Loading YouTube video transcript..."):
            try:
                # Clear previous content state when loading new content
                st.session_state['content_loaded'] = False
                
                process_youtube_video(youtube_url, language)
                st.session_state['content_loaded'] = True
                st.session_state['current_source_url'] = youtube_url
                st.session_state['current_source_type'] = "youtube"
                st.sidebar.success("✅ YouTube video loaded successfully!")
                
                # Add a system message about the loaded content
                system_msg = f"📹 YouTube video loaded: {youtube_url}"
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": system_msg,
                    "audio_file": None
                })
                
            except Exception as e:
                st.session_state['content_loaded'] = False
                error_msg = f"❌ Error loading YouTube video: {str(e)}"
                st.sidebar.error(error_msg)
                if st.session_state['debug_mode']:
                    st.sidebar.code(traceback.format_exc())

else:  # Web Content
    web_url = st.sidebar.text_input(
        "Enter Web URL",
        value=st.session_state.get('current_source_url', ''),
        placeholder="https://example.com/article.pdf or https://arxiv.org/..."
    )
    
    load_web_button = st.sidebar.button("🌐 Load Web Content", type="primary")
    
    if load_web_button and web_url:
        with st.spinner("Loading and processing web content..."):
            try:
                # Clear previous content state when loading new content
                st.session_state['content_loaded'] = False
                
                success, message = content_manager.load_web_content(web_url)
                if success:
                    st.session_state['content_loaded'] = True
                    st.session_state['current_source_url'] = web_url
                    st.session_state['current_source_type'] = "web"
                    st.sidebar.success(f"✅ {message}")    
                    
                    # Add a system message about the loaded content
                    system_msg = f"🌐 Web content loaded: {web_url}"
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": system_msg,
                        "audio_file": None
                    })
                else:
                    st.session_state['content_loaded'] = False
                    st.sidebar.error(f"❌ {message}")
            except Exception as e:
                st.session_state['content_loaded'] = False
                error_msg = f"❌ Error loading web content: {str(e)}"
                st.sidebar.error(error_msg)
                if st.session_state['debug_mode']:
                    st.sidebar.code(traceback.format_exc())

# Show current content status
if st.session_state['content_loaded']:
    source_type = "YouTube Video" if st.session_state['current_source_type'] == "youtube" else "Web Content"
    st.sidebar.info(f"✅ {source_type} Loaded")
    st.sidebar.caption(f"Source: {st.session_state['current_source_url']}")
else:
    st.sidebar.warning("⚠️ No content loaded")

# --- Audio Settings ---
auto_play_audio = st.sidebar.checkbox(
    "Auto-play response audio", 
    value=True,
    help="Generate and auto-play audio responses"
)

# --- Controls ---
col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state['waiting_for_response'] = False
        st.rerun()

with col2:
    if st.button("🔄 Reset All", use_container_width=True):
        st.session_state.messages = []
        st.session_state['content_loaded'] = False
        st.session_state['current_source_url'] = ""
        st.session_state['current_source_type'] = ""
        st.session_state['waiting_for_response'] = False
        st.session_state['thread_id'] = str(uuid.uuid4())
        st.rerun()

# --- Main Chat Section ---
st.title("🤖 Intellexa : A Content Analysis AI")
st.markdown("Analyze YouTube videos, research papers, news articles, and web content!")

# Content status indicator
if not st.session_state['content_loaded']:
    st.warning("💡 Please load content from the sidebar to start analyzing!")

# Minimal scrolling area for messages
st.markdown('<div class="messages-area" id="messages-area">', unsafe_allow_html=True)

# Display all messages instantly
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="user-message">
            <strong>👤 You:</strong><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    elif "error" in message["content"].lower() or "❌" in message["content"]:
        st.markdown(f"""
        <div class="error-message">
            <strong>🤖 Intellexa:</strong><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="assistant-message">
            <strong>🤖 Intellexa:</strong><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)
        
        # Audio for assistant messages
        if ("audio_file" in message and message["audio_file"] and 
            auto_play_audio and os.path.exists(message["audio_file"])):
            st.audio(message["audio_file"], format='audio/mp3', autoplay=True)

# Show thinking message while waiting for response
if st.session_state['waiting_for_response']:
    st.markdown("""
    <div class="thinking-message">
        <strong>🤖 Assistant:</strong><br>
        🤔 Thinking...
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Input section - CLOSER TO BOTTOM
input_col1, input_col2 = st.columns([3, 7])

with input_col1:
    speech_text = speech_to_text(
        language="en", 
        start_prompt="🎤 Record", 
        stop_prompt="⏹️ Stop", 
        key="speech_input",
        just_once=True,
        use_container_width=True
    )

with input_col2:
    user_input = st.chat_input(
        "Type your message here..." if not st.session_state['waiting_for_response'] else "Please wait...",
        disabled=st.session_state['waiting_for_response']
    )

# Process input
final_input = None

if user_input and not st.session_state['waiting_for_response']:
    final_input = user_input
elif speech_text and not st.session_state['waiting_for_response']:
    final_input = speech_text
    st.success(f"🎤 Voice input: \"{speech_text}\"")

if final_input:
    # INSTANTLY add user message and show thinking
    st.session_state.messages.append({"role": "user", "content": final_input, "audio_file": None})
    st.session_state['waiting_for_response'] = True
    st.rerun()

# Process AI response (runs after rerun)
if st.session_state['waiting_for_response'] and st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_message = st.session_state.messages[-1]["content"]
    
    try:
        config = {"configurable": {"thread_id": st.session_state['thread_id']}}
        request_data = {
            "messages": [HumanMessage(content=user_message)],
            "generate_audio": auto_play_audio,
            "current_source": st.session_state['current_source_url'] if st.session_state['content_loaded'] else None
        }
        
        # Add debug info
        if st.session_state['debug_mode']:
            st.sidebar.write("🔍 Debug Info:")
            st.sidebar.json({
                "content_loaded": st.session_state['content_loaded'],
                "current_source": st.session_state['current_source_url'],
                "thread_id": st.session_state['thread_id']
            })
        
        response = app.invoke(request_data, config=config)
        ai_response = response['messages'][-1].content
        audio_file = response.get('audio_file')

        # Add AI response
        st.session_state.messages.append({
            "role": "assistant", 
            "content": ai_response,
            "audio_file": audio_file
        })
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        
        # More specific error handling for the LangChain prompt issue
        if "missing variables" in str(e) or "ChatPromptTemplate" in str(e):
            error_msg = """
            ❌ Prompt Configuration Error
            
            There's an issue with the AI system configuration. This usually happens when:
            
            1. **No content is loaded** - Please load a YouTube video or web content first
            2. **Backend prompt template mismatch** - The AI system expects certain variables that aren't available
            
            **Troubleshooting steps:**
            - Make sure you've loaded content using the sidebar
            - Try resetting the chat and loading content again
            - Check if the backend services are properly configured
            """
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": error_msg,
            "audio_file": None
        })
        
        if st.session_state['debug_mode']:
            st.sidebar.error("Detailed Error:")
            st.sidebar.code(traceback.format_exc())
    
    finally:
        st.session_state['waiting_for_response'] = False
        st.rerun()

# Auto-scroll to bottom
st.markdown(
    """
    <script>
    setTimeout(() => {
        const messagesArea = document.getElementById('messages-area');
        if (messagesArea) {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        }
        window.scrollTo(0, document.body.scrollHeight);
    }, 100);
    </script>
    """,
    unsafe_allow_html=True
)