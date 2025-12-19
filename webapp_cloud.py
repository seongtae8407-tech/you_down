import streamlit as st
import yt_dlp
import os
import shutil
import tempfile

# 페이지 설정
st.set_page_config(page_title="유튜브 다운로더", page_icon="🎬")

st.title("🎬 YouTube Cloud Downloader")
st.write("서버 차단(403) 방지를 위해 쿠키 파일이 필요할 수 있습니다.")

# 임시 저장 폴더
download_folder = "downloads"
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

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

if st.button("변환 시작"):
    if not url:
        st.error("링크를 입력해주세요.")
    else:
        status = st.empty()
        status.info("작업을 시작합니다... (잠시만 기다려주세요)")
        
        try:
            # 기존 파일 청소
            if os.path.exists(download_folder):
                shutil.rmtree(download_folder)
            os.makedirs(download_folder)

            # 쿠키 파일 우선순위 결정
            # 1순위: 사이드바에서 직접 업로드한 파일 (임시 사용)
            # 2순위: 깃허브 저장소에 있는 'cookies.txt' (기본 사용)
            cookie_path = None
            
            if uploaded_cookie is not None:
                # 사용자가 방금 업로드한 경우
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                    tmp.write(uploaded_cookie.getvalue())
                    cookie_path = tmp.name
                st.info("📂 업로드된 쿠키 파일을 사용합니다.")
            elif os.path.exists("cookies.txt"):
                # 저장소에 파일이 있는 경우
                cookie_path = "cookies.txt"
                st.info("📂 저장소에 있는 'cookies.txt' 파일을 자동으로 사용합니다.")
            else:
                st.warning("⚠️ 쿠키 파일이 없습니다. 유튜브 차단(403)이 발생할 수 있습니다.")

            # yt-dlp 옵션 설정
            ydl_opts = {
                'outtmpl': f'{download_folder}/%(title)s.%(ext)s',
                'no_warnings': True,
                # 쿠키 파일이 있으면 사용
                'cookiefile': cookie_path,
                # 차단 방지를 위한 추가 헤더
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
                ydl_opts.update({
                    'format': 'bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4',
                })

            # 다운로드 수행
            final_filename = ""
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'video')
                ext = 'mp3' if "음원" in option else 'mp4'
                
                for f in os.listdir(download_folder):
                    if f.endswith(f".{ext}"):
                        final_filename = os.path.join(download_folder, f)
                        break
            
            # 임시 생성된 쿠키 파일만 삭제 (저장소 원본은 삭제 안 함)
            if uploaded_cookie is not None and cookie_path and os.path.exists(cookie_path):
                os.remove(cookie_path)

            # 다운로드 버튼 생성
            if final_filename and os.path.exists(final_filename):
                status.success("✅ 변환 완료! 아래 버튼을 눌러 저장하세요.")
                with open(final_filename, "rb") as file:
                    btn = st.download_button(
                        label="📥 내 컴퓨터로 파일 저장하기",
                        data=file,
                        file_name=os.path.basename(final_filename),
                        mime="audio/mpeg" if "음원" in option else "video/mp4"
                    )
            else:
                status.error("파일 생성 실패 (유튜브 차단이 지속될 수 있습니다).")

        except Exception as e:
            st.error(f"오류 발생: {e}")
            if "403" in str(e):
                st.warning("⚠️ 유튜브 차단(403 Forbidden)이 발생했습니다. 쿠키 파일이 만료되었을 수 있으니 새로 업로드해주세요.")
