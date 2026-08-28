from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Track:
    id: str
    vidid: str
    title: str
    duration: str
    duration_min: str
    duration_sec: int
    link: str
    thumbnail: str
    channel: str = ""
    views: str = ""

    def __iter__(self):
        """Allows tuple unpacking: title, dur_min, dur_sec, thumb, vidid = track"""
        return iter((self.title, self.duration_min, self.duration_sec, self.thumbnail, self.vidid))

    def __getitem__(self, item: str) -> Any:
        """Allows dictionary indexing: track['title'], track['id'], etc."""
        return getattr(self, item, None)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "vidid": self.vidid,
            "title": self.title,
            "duration": self.duration,
            "duration_min": self.duration_min,
            "duration_sec": self.duration_sec,
            "link": self.link,
            "thumbnail": self.thumbnail,
            "channel": self.channel,
            "views": self.views,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Track":
        vid_id = data.get("id") or data.get("vidid") or ""
        dur = str(data.get("duration") or data.get("duration_min") or "N/A")
        dur_sec = int(data.get("duration_sec") or 0)
        dur_min = str(data.get("duration_min") or dur)
        return cls(
            id=vid_id,
            vidid=vid_id,
            title=str(data.get("title") or "Unknown Track"),
            duration=dur,
            duration_min=dur_min,
            duration_sec=dur_sec,
            link=str(data.get("link") or f"https://www.youtube.com/watch?v={vid_id}"),
            thumbnail=str(data.get("thumbnail") or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"),
            channel=str(data.get("channel") or ""),
            views=str(data.get("views") or "")
        )
