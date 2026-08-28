import sys
import argparse
import asyncio
from .client import YukiAPI

def main():
    parser = argparse.ArgumentParser(
        prog="yuki-dl",
        description="Official CLI for Yuki YouTube Music & Video Downloader"
    )
    parser.add_argument("query", nargs="?", help="Song name, YouTube URL, or Video ID")
    parser.add_argument("-v", "--video", action="store_true", help="Download Video (MP4) instead of Audio")
    parser.add_argument("-s", "--search", action="store_true", help="Search only and display results")
    parser.add_argument("-l", "--limit", type=int, default=5, help="Search results limit (default: 5)")
    parser.add_argument("-u", "--url", action="store_true", help="Print direct streaming URL only")
    parser.add_argument("-o", "--output", default="downloads", help="Output directory (default: downloads)")
    parser.add_argument("--version", action="version", version="yukiytapi 1.0.0")

    args = parser.parse_args()

    if not args.query:
        parser.print_help()
        sys.exit(0)

    async def run():
        async with YukiAPI() as yuki:
            if args.search:
                print(f"\n🔍 Searching YukiAPI for: '{args.query}'...\n")
                results = await yuki.search(args.query, limit=args.limit)
                if not results:
                    print("❌ No tracks found.")
                    return
                for idx, t in enumerate(results, 1):
                    print(f" {idx}. {t.title}")
                    print(f"    ⏱  Duration: {t.duration} | 🆔 ID: {t.id} | 👤 Channel: {t.channel}")
                    print(f"    🔗 Link: {t.link}\n")
                return

            if args.url:
                media_type = "video" if args.video else "audio"
                stream_url = await yuki.get_stream(args.query, type=media_type)
                print(stream_url)
                return

            media_type = "video" if args.video else "audio"
            print(f"\n🎵 Fetching '{args.query}' from YukiAPI...")
            track = await yuki.details(args.query)
            print(f"▶️ Title:    {track.title}")
            print(f"⏱ Duration: {track.duration} ({track.duration_sec}s)")
            print(f"🆔 Video ID: {track.id}")
            print(f"📥 Downloading ({media_type.upper()})...")

            file_path = await yuki.download(args.query, type=media_type, output_dir=args.output)
            print(f"\n✅ Downloaded successfully to:\n   {file_path}\n")

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
