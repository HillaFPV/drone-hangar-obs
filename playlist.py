import random
from yt_dlp import YoutubeDL

def seconds_to_mm_ss(seconds):
    m, s = divmod(seconds, 60)
    if m == 0:
        return f"{s:02d}s"
    else:
        return f"{m}:{s:02d}"

# Simple list of emojis to choose from.
emojis = ["🚁", "💨", "⚡", "🎥", "🎬", "💥", "🚀", "🔥", "🤩", "✈️", "👀", "🌪️", "🎙️", "📺", "📻", "▶️", "🎤", "🎧"]

def main():
    """
    Main function to process the YouTube playlist and print channel info.
    """
    playlist_url = input("Drop the youtube playlist URL: ")
    print("Fetching video list from the playlist. This will take a moment...")
    
    try:
        ydl_opts = {
            'ignoreerrors': True,
            'quiet': True,
            'download': False,
        }

        with YoutubeDL(ydl_opts) as ydl:
            playlist_data = ydl.extract_info(playlist_url, download=False)

        # Iterate through the entries (individual videos)
        for video in playlist_data['entries']:
            if video is None:
                continue
            print(f"{video.get('title')} ({seconds_to_mm_ss(video.get('duration'))})")
            print(f"{video.get('webpage_url')}")
            print(f"Views: {video.get('view_count')} / Thumbs Up: {video.get('like_count')}")
            print(f"{video.get('uploader')} ({video.get('channel_follower_count')} subs - {video.get('uploader_url')}?sub_confirmation=1")
            print()
            
            video_url = video.get('url')
            if not video_url:
                continue
                
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()