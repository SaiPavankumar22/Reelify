# 🎬 Smart Video Processor with Reel Creation

Transform your long videos into engaging social media reels with AI-powered highlights extraction. This application automatically identifies the most engaging moments from your videos and creates TikTok/Reels-ready vertical clips.

## ✨ Features

- **Video Processing**: Upload MP4, MOV, or AVI files or paste a YouTube URL
- **AI-Powered Highlights**: Uses Whisper for transcription and GPT-3.5 to identify engaging moments
- **Automatic Reel Creation**: Generates vertical (9:16) reels from identified highlights
- **Quality Checks**: Validates output reels for proper format and duration
- **Batch Processing**: Process multiple highlights in one go
- **Easy Download**: Download individual reels or all as a ZIP file

## 🛠️ Requirements

- Python 3.8+
- FFmpeg (for video processing)
- OpenAI API key (for GPT-3.5)

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone [your-repository-url]
   cd Smart-Video-Processor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

4. Install FFmpeg:
   - Download from [FFmpeg's official website](https://ffmpeg.org/download.html)
   - Add FFmpeg to your system PATH

## 🚀 Usage

1. Run the application:
   ```bash
   streamlit run main.py
   ```

2. In the web interface:
   - Upload a video file OR paste a YouTube URL
   - Wait for the AI to process the video and identify highlights
   - Preview and download the generated reels

## 🎯 How It Works

1. **Video Input**: Accepts file uploads or YouTube URLs
2. **Audio Extraction**: Extracts audio from the video
3. **Transcription**: Uses OpenAI's Whisper model to transcribe the audio
4. **Highlight Detection**: Sends transcript to GPT-3.5 to identify engaging moments
5. **Reel Creation**: Creates vertical (1080x1920) video clips for each highlight
6. **Quality Check**: Validates each reel meets quality standards
7. **Output**: Provides download links for individual reels or a ZIP archive

## 🔧 Configuration

Modify these parameters in the code as needed:
- `max_duration` in `create_reel()`: Maximum duration for each reel (default: 30 seconds)
- GPT model and parameters in the chat completion call
- Video resolution and format settings

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI](https://openai.com) for Whisper and GPT models
- [FFmpeg](https://ffmpeg.org/) for video processing
- [Streamlit](https://streamlit.io/) for the web interface
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube video downloads

---

Made with ❤️ by Sai Pavan
