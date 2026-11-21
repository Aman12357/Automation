import httpx
from fastapi import HTTPException
from .config import settings

BASE_URL = "https://www.googleapis.com/youtube/v3"

def _request(resource: str, params: dict):
    if not settings.youtube_api_key:
        raise HTTPException(503, "YouTube Data API is not configured. Add YOUTUBE_API_KEY to backend/.env.")
    try:
        response = httpx.get(f"{BASE_URL}/{resource}", params={**params, "key": settings.youtube_api_key}, timeout=20.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        detail = "YouTube Data API rejected the request."
        try: detail = exc.response.json().get("error", {}).get("message", detail)
        except Exception: pass
        raise HTTPException(exc.response.status_code, detail)
    except httpx.HTTPError:
        raise HTTPException(502, "Could not reach YouTube Data API.")

def get_channel(channel_id: str):
    data = _request("channels", {"part":"snippet,contentDetails,statistics","id":channel_id,"maxResults":1})
    items=data.get("items", [])
    if not items: raise HTTPException(404,"YouTube channel was not found or is not publicly available.")
    item=items[0]
    return {"channel_id":item["id"],"title":item.get("snippet",{}).get("title"),
            "description":item.get("snippet",{}).get("description"),
            "published_at":item.get("snippet",{}).get("publishedAt"),
            "uploads_playlist_id":item.get("contentDetails",{}).get("relatedPlaylists",{}).get("uploads"),
            "public_statistics":item.get("statistics",{})}

def list_playlists(channel_id: str, page_token: str | None = None):
    params={"part":"snippet,contentDetails","channelId":channel_id,"maxResults":50}
    if page_token: params["pageToken"]=page_token
    data=_request("playlists",params)
    return {"items":[{"playlist_id":x["id"],"title":x.get("snippet",{}).get("title"),
                      "description":x.get("snippet",{}).get("description"),
                      "item_count":x.get("contentDetails",{}).get("itemCount",0)} for x in data.get("items",[])],
            "next_page_token":data.get("nextPageToken")}

def list_playlist_videos(playlist_id: str, page_token: str | None = None):
    params={"part":"snippet,contentDetails","playlistId":playlist_id,"maxResults":50}
    if page_token: params["pageToken"]=page_token
    data=_request("playlistItems",params)
    return {"items":[{"video_id":x.get("contentDetails",{}).get("videoId"),
                      "title":x.get("snippet",{}).get("title"),
                      "description":x.get("snippet",{}).get("description"),
                      "published_at":x.get("contentDetails",{}).get("videoPublishedAt"),
                      "thumbnail":x.get("snippet",{}).get("thumbnails",{}).get("medium",{}).get("url")}
                     for x in data.get("items",[]) if x.get("contentDetails",{}).get("videoId")],
            "next_page_token":data.get("nextPageToken")}
