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

# 1. 사이드바: 쿠키 파일 업로드 (403 에러 해결용)
st.sidebar.header("🔧 설정 (403 에러 해결)")
cookie_file = st.sidebar.file_uploader("cookies.txt 파일을 업로드하세요", type=["txt"])
st.sidebar.info("유튜브가 서버 IP를 차단할 경우, 크롬 확장프로그램('Get cookies.txt LOCALLY')으로 추출한 쿠키 파일이 필요합니다.")

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

            # 쿠키 파일 처리
            cookie_path = None
            if cookie_file is not None:
                # 업로드된 쿠키 파일을 임시로 저장
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                    tmp.write(cookie_file.getvalue())
                    cookie_path = tmp.name

            # yt-dlp 옵션 설정
            ydl_opts = {
                'outtmpl': f'{download_folder}/%(title)s.%(ext)s',
                'no_warnings': True,
                # 쿠키 파일이 있으면 사용
                'cookiefile': cookie_path if cookie_path else None,
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
            
            # 임시 쿠키 파일 삭제
            if cookie_path and os.path.exists(cookie_path):
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
                st.warning("⚠️ 유튜브가 서버 접근을 차단했습니다. 왼쪽 사이드바에 'cookies.txt'를 업로드하면 해결됩니다.")
