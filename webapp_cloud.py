import streamlit as st
import yt_dlp
import os
import shutil

# 페이지 설정
st.set_page_config(page_title="유튜브 다운로더", page_icon="🎬")

st.title("🎬 YouTube Cloud Downloader")
st.write("서버에서 변환 후 다운로드 버튼을 생성합니다.")

# 임시 저장 폴더 (클라우드 환경용)
download_folder = "downloads"
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

url = st.text_input("유튜브 링크 입력:", placeholder="https://youtube.com/...")
option = st.radio("형식 선택:", ("동영상 (MP4)", "음원 (MP3)"))

if st.button("변환 시작"):
    if not url:
        st.error("링크를 입력해주세요.")
    else:
        status = st.empty()
        status.info("작업을 시작합니다... (잠시만 기다려주세요)")
        
        try:
            # 1. 기존 파일 청소 (서버 용량 관리)
            if os.path.exists(download_folder):
                shutil.rmtree(download_folder)
            os.makedirs(download_folder)

            # 2. 옵션 설정
            ydl_opts = {
                'outtmpl': f'{download_folder}/%(title)s.%(ext)s',
                'no_warnings': True,
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

            # 3. 다운로드 수행
            final_filename = ""
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'video')
                ext = 'mp3' if "음원" in option else 'mp4'
                # 실제 저장된 파일명 찾기
                for f in os.listdir(download_folder):
                    if f.endswith(f".{ext}"):
                        final_filename = os.path.join(download_folder, f)
                        break
            
            # 4. 다운로드 버튼 생성
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
                status.error("파일 생성에 실패했습니다.")

        except Exception as e:
            st.error(f"오류 발생: {e}")