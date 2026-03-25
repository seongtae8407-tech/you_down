import streamlit as st
import yt_dlp
import os
import tempfile

# 페이지 설정
st.set_page_config(page_title="유튜브 다운로더", page_icon="🎬")

st.title("🎬 YouTube Cloud Downloader")
st.write("서버 차단(403) 방지를 위해 쿠키 파일이 필요할 수 있습니다.")

# [추가] 무료 서버 용량 제한 안내
st.info("⚠️ **주의:** Streamlit 무료 서버의 메모리 한계로 인해, **20분 이상의 고화질 영상**은 실패할 수 있습니다.")

# 세션 상태 초기화
if 'download_ready' not in st.session_state:
    st.session_state.download_ready = False
if 'file_name' not in st.session_state:
    st.session_state.file_name = ""
if 'file_data' not in st.session_state:
    st.session_state.file_data = None
if 'mime_type' not in st.session_state:
    st.session_state.mime_type = ""

# 1. 사이드바: 쿠키 파일 설정
st.sidebar.header("🔧 설정 (403 에러 해결)")

with st.sidebar.expander("❓ 쿠키(cookies.txt) 어떻게 다운받나요?", expanded=False):
    st.markdown("""
    1. 브라우저에서 **'Get cookies.txt LOCALLY'** 확장 프로그램 설치.
    2. 유튜브 접속 후 확장 프로그램 실행 -> **Export** 클릭.
    3. 다운받은 파일을 아래에 업로드하세요.
    """)

uploaded_cookie = st.sidebar.file_uploader("쿠키 파일 업로드 (cookies.txt)", type=["txt"])

# 2. 메인 입력
url = st.text_input("유튜브 링크 입력:", placeholder="https://youtube.com/...")
option = st.radio("형식 선택:", ("동영상 (MP4)", "음원 (MP3)"))

# 화질 설정 로직
quality_setting = "Low"
if "동영상" in option:
    st.markdown("---")
    quality_choice = st.radio(
        "화질 선택:", 
        ("일반 화질 (720p 이하) - 권장 👍", "최고 화질 (원본) - 실패 가능성 있음 ⚠️"),
        index=0 
    )
    quality_setting = "Low" if "일반" in quality_choice else "High"

# 변환 버튼
if st.button("변환 시작"):
    if not url:
        st.error("링크를 입력해주세요.")
    else:
        status = st.empty()
        status.info("작업을 시작합니다... (영상이 길면 오래 걸릴 수 있습니다)")
        
        try:
            st.session_state.download_ready = False
            
            cookie_path = None
            temp_cookie_file = None 

            if uploaded_cookie is not None:
                temp_cookie_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
                temp_cookie_file.write(uploaded_cookie.getvalue())
                temp_cookie_file.close()
                cookie_path = temp_cookie_file.name
            elif os.path.exists("cookies.txt"):
                cookie_path = "cookies.txt"

            with tempfile.TemporaryDirectory() as temp_dir:
                # 기본 옵션 설정
                ydl_opts = {
                    'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
                    'cookiefile': cookie_path,
                    'noplaylist': True,
                    'quiet': True,
                    'no_warnings': True,
                }

                # [핵심 수정] 포맷 선택 로직 강화
                if "음원" in option:
                    ydl_opts.update({
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                    })
                else:
                    if quality_setting == "Low":
                        # MP4 우선, 720p 이하 중 가장 좋은 것 선택
                        ydl_opts.update({
                            'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
                            'merge_output_format': 'mp4',
                        })
                    else:
                        # 최고 화질 시도하되, 없으면 차선책(fallback) 선택
                        ydl_opts.update({
                            'format': 'bestvideo+bestaudio/best',
                            'merge_output_format': 'mp4',
                        })

                # 다운로드 실행
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    ext = 'mp3' if "음원" in option else 'mp4'
                    
                    # 실제 생성된 파일 찾기
                    final_filename = None
                    for f in os.listdir(temp_dir):
                        if f.endswith(f".{ext}"):
                            final_filename = os.path.join(temp_dir, f)
                            break
                
                    if final_filename and os.path.exists(final_filename):
                        with open(final_filename, "rb") as f:
                            st.session_state.file_data = f.read()
                        
                        st.session_state.file_name = os.path.basename(final_filename)
                        st.session_state.mime_type = "audio/mpeg" if "음원" in option else "video/mp4"
                        st.session_state.download_ready = True
                        status.success(f"✅ 변환 완료: {st.session_state.file_name}")
                    else:
                        status.error("파일 변환에 실패했습니다. 포맷을 찾을 수 없습니다.")

            if temp_cookie_file:
                os.remove(temp_cookie_file.name)

        except Exception as e:
            st.error(f"오류 발생: {e}")
            if "403" in str(e):
                st.warning("⚠️ 유튜브 차단입니다. 최신 쿠키 파일을 업로드해주세요.")

# 3. 다운로드 버튼
if st.session_state.download_ready and st.session_state.file_data:
    st.download_button(
        label="📥 파일 다운로드 하기",
        data=st.session_state.file_data,
        file_name=st.session_state.file_name,
        mime=st.session_state.mime_type
    )
