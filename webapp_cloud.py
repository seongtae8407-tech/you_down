import streamlit as st
import yt_dlp
import os
import shutil
import tempfile
import time

# 페이지 설정
st.set_page_config(page_title="유튜브 다운로더", page_icon="🎬")

st.title("🎬 YouTube Cloud Downloader")
st.write("서버 차단(403) 방지를 위해 쿠키 파일이 필요할 수 있습니다.")

# [추가] 무료 서버 용량 제한 안내
st.info("⚠️ **주의:** Streamlit 무료 서버의 메모리 한계로 인해, **20분 이상의 고화질 영상**이나 **500MB 이상의 파일**은 다운로드가 실패하거나 멈출 수 있습니다.")

# 세션 상태 초기화
if 'download_ready' not in st.session_state:
    st.session_state.download_ready = False
if 'file_name' not in st.session_state:
    st.session_state.file_name = ""
if 'file_data' not in st.session_state:
    st.session_state.file_data = None  # 파일 내용을 메모리에 저장할 변수
if 'mime_type' not in st.session_state:
    st.session_state.mime_type = ""

# 1. 사이드바: 쿠키 파일 설정
st.sidebar.header("🔧 설정 (403 에러 해결)")

# [핵심 변경] 쿠키 다운로드 방법을 아주 쉽고 직관적으로 안내
with st.sidebar.expander("❓ 쿠키(cookies.txt) 어떻게 다운받나요?", expanded=True):
    st.markdown("""
    **단 1분이면 됩니다!**
    1. PC 크롬 브라우저에서 👉 [여기(확장프로그램)](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpgnnhmhfhkio)를 눌러 설치합니다.
    2. [유튜브 홈페이지](https://youtube.com)에 접속합니다.
    3. 우측 상단 🧩퍼즐 아이콘을 눌러 방금 설치한 프로그램(쿠키 아이콘)을 켭니다.
    4. **[Export]** 버튼을 누르면 `cookies.txt`가 내 컴퓨터로 다운로드됩니다.
    5. 다운받은 파일을 아래 빈칸에 끌어다 놓으세요!
    """)

uploaded_cookie = st.sidebar.file_uploader("쿠키 파일 업로드 (cookies.txt)", type=["txt"])

# 2. 메인 입력
url = st.text_input("유튜브 링크 입력:", placeholder="https://youtube.com/...")
option = st.radio("형식 선택:", ("동영상 (MP4)", "음원 (MP3)"))

# 동영상 선택 시 화질 옵션 제공
quality_setting = "High"
if "동영상" in option:
    st.markdown("---")
    st.caption("💡 **팁:** '일반 화질'을 선택하면 다운로드 성공 확률이 훨씬 높습니다.")
    quality_choice = st.radio(
        "화질 선택 (서버 부하 조절):", 
        ("일반 화질 (720p/480p) - 추천 👍", "최고 화질 (1080p/4K) - 실패할 수 있음 ⚠️"),
        index=0 
    )
    
    if "일반" in quality_choice:
        quality_setting = "Low"
    else:
        quality_setting = "High"

# 변환 버튼 (누르면 처리 시작)
if st.button("변환 시작"):
    if not url:
        st.error("링크를 입력해주세요.")
    else:
        status = st.empty()
        status.info("작업을 시작합니다... (잠시만 기다려주세요)")
        
        try:
            # 상태 초기화
            st.session_state.download_ready = False
            st.session_state.file_data = None
            
            # 쿠키 파일 처리
            cookie_path = None
            # 임시 쿠키 파일 생성을 위한 관리자
            temp_cookie_file = None 

            if uploaded_cookie is not None:
                # 사용자가 업로드한 경우 임시 파일 생성
                temp_cookie_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
                temp_cookie_file.write(uploaded_cookie.getvalue())
                temp_cookie_file.close() # 쓰기 종료 후 닫기
                cookie_path = temp_cookie_file.name
                st.info("📂 업로드된 쿠키 파일을 사용합니다.")
            elif os.path.exists("cookies.txt"):
                cookie_path = "cookies.txt"
                st.info("📂 저장소에 있는 'cookies.txt' 파일을 자동으로 사용합니다.")
            else:
                st.warning("⚠️ 쿠키 파일이 없습니다. 유튜브 차단(403)이 발생할 수 있습니다.")

            # 쿠키 형식 검사
            if cookie_path:
                with open(cookie_path, 'r', encoding='utf-8', errors='ignore') as f:
                    first_line = f.readline()
                    if "# Netscape HTTP Cookie File" not in first_line and "# This is a generated file" not in first_line:
                        st.warning("⚠️ 쿠키 파일 형식이 Netscape 포맷이 아닙니다. 안내된 확장 프로그램을 사용해주세요.")

            # 임시 디렉토리 사용 (작업 끝나면 자동 삭제됨)
            with tempfile.TemporaryDirectory() as temp_dir:
                
                # yt-dlp 옵션
                ydl_opts = {
                    'outtmpl': f'{temp_dir}/%(title)s.%(ext)s', # 임시 폴더에 저장
                    'no_warnings': True,
                    'cookiefile': cookie_path,
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    }
                }

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
                        ydl_opts.update({
                            'format': 'best[height<=720]/bestvideo[height<=720]+bestaudio/best',
                            'merge_output_format': 'mp4',
                        })
                    else:
                        ydl_opts.update({
                            'format': 'bestvideo+bestaudio/best',
                            'merge_output_format': 'mp4',
                        })

                # 다운로드 실행
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    ext = 'mp3' if "음원" in option else 'mp4'
                    
                    # 파일 찾기
                    final_filename = None
                    for f in os.listdir(temp_dir):
                        if f.endswith(f".{ext}"):
                            final_filename = os.path.join(temp_dir, f)
                            break
                
                    # 파일 처리 및 메모리 저장
                    if final_filename and os.path.exists(final_filename):
                        file_size_mb = os.path.getsize(final_filename) / (1024 * 1024)
                        
                        if file_size_mb > 0:
                            # 파일을 메모리로 완전히 읽어들임
                            with open(final_filename, "rb") as f:
                                st.session_state.file_data = f.read()
                            
                            st.session_state.file_name = os.path.basename(final_filename)
                            st.session_state.mime_type = "audio/mpeg" if "음원" in option else "video/mp4"
                            st.session_state.download_ready = True
                            
                            status.success(f"✅ 변환 완료! ({file_size_mb:.1f} MB)")
                        else:
                            status.error("파일이 생성되었으나 비어있습니다 (0바이트).")
                    else:
                        status.error("파일 생성 실패.")
            
            # 임시 생성된 쿠키 파일 삭제
            if temp_cookie_file and os.path.exists(temp_cookie_file.name):
                os.remove(temp_cookie_file.name)

        except Exception as e:
            st.error(f"오류 발생: {e}")
            if "403" in str(e):
                st.warning("⚠️ 유튜브 서버 차단(403)입니다. 사이드바의 안내에 따라 쿠키 파일을 다시 업로드해주세요.")

# 3. 다운로드 버튼 표시 (메모리에 저장된 데이터 사용)
if st.session_state.download_ready and st.session_state.file_data:
    st.download_button(
        label=f"📥 다운로드: {st.session_state.file_name}",
        data=st.session_state.file_data,
        file_name=st.session_state.file_name,
        mime=st.session_state.mime_type
    )
elif st.session_state.download_ready and not st.session_state.file_data:
    st.warning("⚠️ 데이터가 만료되었습니다. 다시 변환해주세요.")
