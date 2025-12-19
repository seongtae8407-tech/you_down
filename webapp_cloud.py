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

# 임시 저장 폴더
download_folder = "downloads"
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

# 세션 상태 초기화 (새로고침 되어도 데이터 유지)
if 'download_ready' not in st.session_state:
    st.session_state.download_ready = False
if 'file_path' not in st.session_state:
    st.session_state.file_path = ""
if 'file_name' not in st.session_state:
    st.session_state.file_name = ""
if 'mime_type' not in st.session_state:
    st.session_state.mime_type = ""

# 1. 사이드바: 쿠키 파일 설정
st.sidebar.header("🔧 설정 (403 에러 해결)")
st.sidebar.markdown("""
**사용 방법:**
1. `cookies.txt` 파일을 깃허브 저장소에 같이 올려두면 매번 업로드할 필요가 없습니다.
2. 만약 저장소의 쿠키가 만료되어 에러가 나면, 아래에 새 파일을 업로드해서 임시로 쓸 수 있습니다.
""")
uploaded_cookie = st.sidebar.file_uploader("쿠키 파일 갱신/임시 사용", type=["txt"])

# 2. 메인 입력
url = st.text_input("유튜브 링크 입력:", placeholder="https://youtube.com/...")
option = st.radio("형식 선택:", ("동영상 (MP4)", "음원 (MP3)"))

# [추가] 동영상 선택 시 화질 옵션 제공
quality_setting = "High"
if "동영상" in option:
    st.markdown("---")
    st.caption("💡 **팁:** '일반 화질'을 선택하면 다운로드 성공 확률이 훨씬 높습니다.")
    quality_choice = st.radio(
        "화질 선택 (서버 부하 조절):", 
        ("일반 화질 (720p/480p) - 추천 👍", "최고 화질 (1080p/4K) - 실패할 수 있음 ⚠️"),
        index=0 # 기본값을 일반 화질로 설정 (안정성 우선)
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
            
            # 기존 파일 청소
            if os.path.exists(download_folder):
                shutil.rmtree(download_folder)
            os.makedirs(download_folder)

            # 쿠키 파일 처리
            cookie_path = None
            if uploaded_cookie is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                    tmp.write(uploaded_cookie.getvalue())
                    cookie_path = tmp.name
                st.info("📂 업로드된 쿠키 파일을 사용합니다.")
            elif os.path.exists("cookies.txt"):
                cookie_path = "cookies.txt"
                st.info("📂 저장소에 있는 'cookies.txt' 파일을 자동으로 사용합니다.")
            else:
                st.warning("⚠️ 쿠키 파일이 없습니다. 유튜브 차단(403)이 발생할 수 있습니다.")

            # 쿠키 검사
            if cookie_path:
                with open(cookie_path, 'r', encoding='utf-8', errors='ignore') as f:
                    first_line = f.readline()
                    if "# Netscape HTTP Cookie File" not in first_line and "# This is a generated file" not in first_line:
                        st.warning("⚠️ 쿠키 파일 형식이 Netscape 포맷이 아닙니다. 'Get cookies.txt LOCALLY' 확장 프로그램을 사용해주세요.")

            # yt-dlp 옵션 기본 설정
            ydl_opts = {
                'outtmpl': f'{download_folder}/%(title)s.%(ext)s',
                'no_warnings': True,
                'cookiefile': cookie_path,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                }
            }

            # [수정] 옵션별 세부 설정 (화질 반영)
            if "음원" in option:
                # 오디오 모드
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            else:
                # 비디오 모드
                if quality_setting == "Low":
                    # 일반 화질: 높이를 720p 이하로 제한하여 메모리 절약
                    ydl_opts.update({
                        'format': 'best[height<=720]/bestvideo[height<=720]+bestaudio/best',
                        'merge_output_format': 'mp4',
                    })
                else:
                    # 최고 화질: 제한 없음 (서버 부하 높음)
                    ydl_opts.update({
                        'format': 'bestvideo+bestaudio/best',
                        'merge_output_format': 'mp4',
                    })

            # 다운로드 실행
            final_filename = ""
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'video')
                ext = 'mp3' if "음원" in option else 'mp4'
                
                # 파일 찾기
                for f in os.listdir(download_folder):
                    if f.endswith(f".{ext}"):
                        final_filename = os.path.join(download_folder, f)
                        break
            
            # 임시 쿠키 삭제
            if uploaded_cookie is not None and cookie_path and os.path.exists(cookie_path):
                os.remove(cookie_path)

            # 성공 시 세션 상태에 저장 (중요!)
            if final_filename and os.path.exists(final_filename) and os.path.getsize(final_filename) > 0:
                st.session_state.file_path = final_filename
                st.session_state.file_name = os.path.basename(final_filename)
                st.session_state.mime_type = "audio/mpeg" if "음원" in option else "video/mp4"
                st.session_state.download_ready = True
                
                file_size = os.path.getsize(final_filename) / (1024 * 1024)
                status.success(f"✅ 변환 완료! ({file_size:.1f} MB)")
            else:
                status.error("파일 생성 실패. (0바이트 또는 생성되지 않음)")

        except Exception as e:
            st.error(f"오류 발생: {e}")
            if "403" in str(e):
                st.warning("⚠️ 유튜브 서버 차단(403)입니다. 쿠키 파일을 확인해주세요.")

# 3. 다운로드 버튼 표시 (데이터 유효성 재확인)
if st.session_state.download_ready:
    try:
        if os.path.exists(st.session_state.file_path):
            with open(st.session_state.file_path, "rb") as file:
                # 파일을 메모리로 읽어서 버튼에 전달
                file_bytes = file.read()
                
                # 데이터가 비어있지 않은 경우에만 버튼 생성
                if len(file_bytes) > 0:
                    st.download_button(
                        label=f"📥 다운로드: {st.session_state.file_name}",
                        data=file_bytes,
                        file_name=st.session_state.file_name,
                        mime=st.session_state.mime_type
                    )
                else:
                    st.error("오류: 변환된 파일의 크기가 0입니다. 다시 시도해주세요.")
                    st.session_state.download_ready = False
        else:
            st.warning("⚠️ 파일이 삭제되었습니다. 다시 변환해주세요.")
            st.session_state.download_ready = False
    except Exception as e:
        st.error(f"다운로드 버튼 생성 중 오류: {e}")
