import os 
import ffmpeg 
import openai 
import whisper 
import tempfile 
import streamlit as st 
import re
import zipfile
import shutil
import time
import gc
import yt_dlp
import sqlite3
import bcrypt
from datetime import datetime
from dotenv import load_dotenv 
from moviepy.editor import VideoFileClip 

load_dotenv() 
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 

os.environ["PATH"] = r"C:\Users\dsaip\Downloads\ffmpeg-7.1.1-full_build\ffmpeg-7.1.1-full_build\bin" + os.pathsep + os.environ.get("PATH", "") 

def init_database():
    """Initialize SQLite database with users and history tables"""
    conn = sqlite3.connect('reelify.db')
    cursor = conn.cursor()
    

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processing_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            video_name TEXT,
            video_duration REAL,
            reels_generated INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def register_user(name, email, password):
    """Register a new user"""
    try:
        conn = sqlite3.connect('reelify.db')
        cursor = conn.cursor()
        

        cursor.execute('SELECT email FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            return False, "Email already registered"
        

        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
        ''', (name, email, password_hash))
        
        conn.commit()
        conn.close()
        return True, "Registration successful"
    except Exception as e:
        return False, f"Registration failed: {str(e)}"

def login_user(email, password):
    """Authenticate user login"""
    try:
        conn = sqlite3.connect('reelify.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name, email, password_hash FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and verify_password(password, user[3]):
            return True, {"id": user[0], "name": user[1], "email": user[2]}
        else:
            return False, "Invalid email or password"
    except Exception as e:
        return False, f"Login failed: {str(e)}"

def save_processing_history(user_id, video_name, video_duration, reels_count):
    """Save processing history to database"""
    try:
        conn = sqlite3.connect('reelify.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO processing_history (user_id, video_name, video_duration, reels_generated)
            VALUES (?, ?, ?, ?)
        ''', (user_id, video_name, video_duration, reels_count))
        
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Failed to save history: {str(e)}")

def get_user_history(user_id):
    """Get user's processing history"""
    try:
        conn = sqlite3.connect('reelify.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT video_name, video_duration, reels_generated, created_at
            FROM processing_history 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (user_id,))
        
        history = cursor.fetchall()
        conn.close()
        return history
    except Exception as e:
        st.error(f"Failed to fetch history: {str(e)}")
        return []

def show_auth_page():
    """Show authentication page (login/register)"""
    st.title("🎬 Smart Video Processor - Authentication")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            email = st.text_input("Email", type="default")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")
            
            if submit_login:
                if email and password:
                    success, result = login_user(email, password)
                    if success:
                        st.session_state['user'] = result
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(result)
                else:
                    st.error("Please fill in all fields")
    
    with tab2:
        st.subheader("Create New Account")
        with st.form("register_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_register = st.form_submit_button("Register")
            
            if submit_register:
                if name and email and password and confirm_password:
                    if password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters long")
                    else:
                        success, message = register_user(name, email, password)
                        if success:
                            st.success(message)
                            st.info("Please login with your new account")
                        else:
                            st.error(message)
                else:
                    st.error("Please fill in all fields")

def show_user_profile():
    """Show user profile and history"""
    user = st.session_state.get('user')
    if not user:
        return
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Welcome, {user['name']}!**")
    st.sidebar.markdown(f"📧 {user['email']}")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()
    
    if st.sidebar.button("📊 View History"):
        st.session_state['show_history'] = True
    

    if st.session_state.get('show_history', False):
        st.markdown("## 📊 Your Processing History")
        history = get_user_history(user['id'])
        
        if history:
            for i, (video_name, duration, reels_count, created_at) in enumerate(history):
                with st.expander(f"📹 {video_name or 'Video'} - {created_at}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Duration", f"{duration:.1f}s" if duration else "N/A")
                    with col2:
                        st.metric("Reels Generated", reels_count or 0)
                    with col3:
                        st.metric("Date", created_at.split()[0] if created_at else "N/A")
        else:
            st.info("No processing history found. Start creating some reels!")
        
        if st.button("🔙 Back to Main"):
            st.session_state['show_history'] = False
            st.rerun()


def parse_timestamp(timestamp_str):
    try:
        if 's' in timestamp_str:
            return float(timestamp_str.replace('s', ''))
        parts = timestamp_str.split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        else:
            return float(parts[0])
    except:
        return 0

def extract_timestamps_from_gpt_response(gpt_response, max_duration=None):
    timestamps = []
    pattern = r'\[([^\]]+)\]\s*-\s*\[([^\]]+)\]'
    matches = re.findall(pattern, gpt_response)
    for start_str, end_str in matches:
        start_seconds = parse_timestamp(start_str.strip())
        end_seconds = parse_timestamp(end_str.strip())
        if start_seconds < end_seconds:
            if max_duration:
                if start_seconds >= max_duration:
                    st.warning(f"⚠️ Skipping segment {start_str}-{end_str}: starts after video ends ({max_duration:.1f}s)")
                    continue
                if end_seconds > max_duration:
                    st.warning(f"⚠️ Adjusting end time for segment {start_str}-{end_str}: was beyond video duration")
                    end_seconds = max_duration
            timestamps.append((start_seconds, end_seconds))
    return timestamps

def download_youtube_video(url, output_dir):
    """Download YouTube video using yt-dlp"""
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
            video_path = os.path.join(output_dir, f"{safe_title}.mp4")
            
            ydl_opts['outtmpl'] = video_path
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                ydl_download.download([url])
                
            for file in os.listdir(output_dir):
                if safe_title in file and file.endswith(('.mp4', '.mkv', '.webm')):
                    actual_path = os.path.join(output_dir, file)
                    if actual_path != video_path and file.endswith('.mp4'):
                        return actual_path
                    elif not file.endswith('.mp4'):
                        mp4_path = os.path.join(output_dir, f"{safe_title}.mp4")
                        ffmpeg.input(actual_path).output(mp4_path).run(overwrite_output=True, quiet=True)
                        os.remove(actual_path)
                        return mp4_path
                        
            return video_path if os.path.exists(video_path) else None
            
    except Exception as e:
        raise Exception(f"Failed to download video: {str(e)}")

def create_reel(input_video_path, start_time, end_time, output_path, max_duration=30, video_duration=None):
    clip = clip_resized = clip_final = None
    try:
        if video_duration:
            if start_time >= video_duration:
                raise ValueError("Start time is beyond video duration")
            if end_time > video_duration:
                end_time = video_duration
        duration = end_time - start_time
        if duration > max_duration:
            end_time = start_time + max_duration
        if duration < 1:
            raise ValueError("Segment too short")
        clip = VideoFileClip(input_video_path).subclip(start_time, end_time)
        original_width, original_height = clip.size
        target_width, target_height = 1080, 1920
        scale = min(target_width / original_width, target_height / original_height)
        new_width, new_height = int(original_width * scale), int(original_height * scale)
        clip_resized = clip.resize((new_width, new_height))
        if new_width < target_width or new_height < target_height:
            clip_final = clip_resized.on_color(
                size=(target_width, target_height),
                color=(0, 0, 0),
                pos='center'
            )
        else:
            clip_final = clip_resized
        temp_audio = f'temp-audio-{int(time.time())}.m4a'
        clip_final.write_videofile(output_path, codec='libx264', audio_codec='aac',
                                   temp_audiofile=temp_audio, remove_temp=True, verbose=False, logger=None)
        return True
    except Exception as e:
        st.error(f"❌ Error creating reel: {e}")
        return False
    finally:
        for clip_obj in [clip_final, clip_resized, clip]:
            try:
                if clip_obj:
                    clip_obj.close()
                    del clip_obj
            except:
                pass
        gc.collect()

def evaluate_reel_quality(reel_path, expected_start, expected_end, transcript_segment=""):
    quality_report = {'duration_check': False, 'resolution_check': False,
                      'file_exists': False, 'file_size_mb': 0, 'issues': []}
    clip = None
    try:
        if not os.path.exists(reel_path):
            quality_report['issues'].append("Reel file does not exist")
            return quality_report
        quality_report['file_exists'] = True
        size = os.path.getsize(reel_path) / (1024 * 1024)
        quality_report['file_size_mb'] = round(size, 2)
        if size < 0.1:
            quality_report['issues'].append("File size too small")
        clip = VideoFileClip(reel_path)
        actual_duration = clip.duration
        expected_duration = expected_end - expected_start
        if abs(actual_duration - expected_duration) <= 2:
            quality_report['duration_check'] = True
        else:
            quality_report['issues'].append(f"Duration mismatch: got {actual_duration:.1f}s")
        if clip.size == (1080, 1920):
            quality_report['resolution_check'] = True
        else:
            quality_report['issues'].append(f"Wrong resolution: {clip.size}")
        if actual_duration < 5:
            quality_report['issues'].append("Reel too short (< 5s)")
        elif actual_duration > 60:
            quality_report['issues'].append("Reel too long (> 60s)")
    except Exception as e:
        quality_report['issues'].append(f"Error analyzing reel: {str(e)}")
    finally:
        try:
            if clip:
                clip.close()
        except:
            pass
        gc.collect()
    return quality_report

def create_download_zip(reel_paths, tmpdir):
    zip_path = os.path.join(tmpdir, "video_reels.zip")
    with zipfile.ZipFile(zip_path, 'w') as zip_file:
        for i, reel_path in enumerate(reel_paths, 1):
            if os.path.exists(reel_path):
                zip_file.write(reel_path, f"reel_{i}.mp4")
    return zip_path

def main_app():
    """Main application after authentication"""
    st.title("🎬 Smart Video Processor with Reel Creation")
    

    show_user_profile()
    

    if st.session_state.get('show_history', False):
        return
    
    uploaded_file = st.file_uploader("📤 Upload a video", type=["mp4", "mov", "avi"])
    video_url = st.text_input("🔗 Or paste a YouTube video URL")

    tmpdir = tempfile.mkdtemp()
    video_path = None
    video_name = None

    if video_url and not uploaded_file:
        with st.spinner("Downloading video from YouTube..."):
            try:
                video_path = download_youtube_video(video_url, tmpdir)
                if video_path and os.path.exists(video_path):
                    video_name = os.path.basename(video_path)
                    st.success("✅ Download complete!")
                    st.video(video_path)
                else:
                    st.error("❌ Failed to download video - file not found after download")
            except Exception as e:
                st.error(f"❌ YouTube download failed: {e}")
                st.info("💡 Try using a different YouTube URL or upload the video file directly")

    if uploaded_file:
        video_path = os.path.join(tmpdir, "input_video.mp4")
        video_name = uploaded_file.name
        with open(video_path, "wb") as f:
            f.write(uploaded_file.read())
        st.success("✅ File uploaded successfully!")
        st.video(video_path)

    if video_path and os.path.exists(video_path):
        try:
            st.toast("Extracting audio...")
            audio_path = os.path.join(tmpdir, "audio.wav")
            ffmpeg.input(video_path).output(audio_path, **{'q:a': 0, 'map': 'a'}).run(overwrite_output=True, quiet=True)
            st.audio(audio_path)

            st.toast("Getting video duration...")
            video_clip = VideoFileClip(video_path)
            video_duration = video_clip.duration
            video_clip.close()
            minutes, seconds = int(video_duration // 60), int(video_duration % 60)
            duration_str = f"{minutes:02d}:{seconds:02d}"
            st.info(f"🎥 Video Duration: {duration_str}")

            st.toast("Transcribing audio...")
            model = whisper.load_model("base")
            result = model.transcribe(audio_path)
            transcript = result["text"]
            st.markdown("### 📝 Transcript")
            st.write(transcript)

            st.toast("Sending to GPT...")
            prompt = f"""
    Identify 3-5 most engaging moments for social media reels from this transcript.

    Timestamps should be within {duration_str} ({video_duration:.2f} seconds total).
    Use [MM:SS] - [MM:SS] format for each highlight.

    Transcript:
    {transcript}
    """
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            gpt_response = response.choices[0].message.content
            st.markdown("### 🎯 Highlighted Segments")
            st.text(gpt_response)

            timestamps = extract_timestamps_from_gpt_response(gpt_response, video_duration)
            if timestamps:
                st.markdown("## 🎞️ Reel Creation")
                reel_paths = []
                quality_reports = []
                progress_bar = st.progress(0)
                status = st.empty()
                for i, (start, end) in enumerate(timestamps):
                    status.text(f"Creating reel {i+1}/{len(timestamps)}...")
                    reel_path = os.path.join(tmpdir, f"reel_{i+1}.mp4")
                    success = create_reel(video_path, start, end, reel_path, video_duration=video_duration)
                    if success:
                        reel_paths.append(reel_path)
                        quality = evaluate_reel_quality(reel_path, start, end)
                        quality_reports.append(quality)
                        st.video(reel_path)
                        with open(reel_path, 'rb') as f:
                            st.download_button(
                                f"⬇️ Download Reel {i+1}", 
                                f.read(), 
                                file_name=f"reel_{i+1}.mp4",
                                key=f"download_reel_{i+1}"
                            )
                    progress_bar.progress((i + 1) / len(timestamps))
                
                st.success("✅ All reels processed!")
                
                # Save to history
                user = st.session_state.get('user')
                if user:
                    save_processing_history(user['id'], video_name, video_duration, len(reel_paths))
                
                if len(reel_paths) > 1:
                    zip_path = create_download_zip(reel_paths, tmpdir)
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            "⬇️ Download All Reels (ZIP)", 
                            f.read(), 
                            file_name="video_reels.zip",
                            key="download_all_reels"
                        )
            else:
                st.warning("No valid timestamps found. GPT output may be malformed.")
        except Exception as e:
            st.error(f"❌ Error occurred: {e}")
            import traceback
            st.error(f"Full error: {traceback.format_exc()}")
        finally:
            try:
                time.sleep(1)
                gc.collect()
                if os.path.exists(tmpdir):
                    shutil.rmtree(tmpdir, ignore_errors=True)
            except Exception as cleanup_error:
                st.warning(f"⚠️ Cleanup issue: {cleanup_error}")


def main():
    st.set_page_config(page_title="Smart Video Processor", layout="centered")
    

    init_database()
    

    if 'user' not in st.session_state:
        show_auth_page()
    else:
        main_app()

if __name__ == "__main__":
    main()