import time
import logging
from typing import Optional, Dict, Any, List
import requests

logger = logging.getLogger(__name__)

# In-memory cache for Codeforces ratings: {handle_lower: {"data": dict, "expires_at": float}}
_CF_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL_SECONDS = 600  # 10 minutes


class CodeforcesClient:
    """
    Client for the public Codeforces REST API.
    Supports single and batch handle lookups with in-memory TTL caching.
    """

    BASE_URL = "https://codeforces.com/api"

    @classmethod
    def get_user_info(cls, handle: str) -> Optional[Dict[str, Any]]:
        """Fetch info for a single handle."""
        if not handle or not handle.strip():
            return None

        handle = handle.strip()
        cached = cls._get_from_cache(handle)
        if cached is not None:
            return cached

        results = cls.get_users_info([handle])
        return results.get(handle.lower())

    @classmethod
    def get_users_info(cls, handles: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Batch fetch info for multiple Codeforces handles.
        Returns a dict mapping handle (lowercase) -> user_info dict.
        """
        if not handles:
            return {}

        clean_handles = list({h.strip() for h in handles if h and h.strip()})
        if not clean_handles:
            return {}

        now = time.time()
        results: Dict[str, Dict[str, Any]] = {}
        to_fetch: List[str] = []

        for h in clean_handles:
            cached = cls._get_from_cache(h)
            if cached is not None:
                results[h.lower()] = cached
            else:
                to_fetch.append(h)

        if not to_fetch:
            return results

        try:
            handles_query = ";".join(to_fetch)
            url = f"{cls.BASE_URL}/user.info?handles={handles_query}"
            resp = requests.get(url, timeout=4.0)

            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "OK":
                    for user_data in data.get("result", []):
                        handle_key = user_data.get("handle", "").lower()
                        info = {
                            "handle": user_data.get("handle", ""),
                            "rating": user_data.get("rating", 0) or 0,
                            "maxRating": user_data.get("maxRating", 0) or 0,
                            "rank": user_data.get("rank", "unrated") or "unrated",
                            "maxRank": user_data.get("maxRank", "unrated") or "unrated",
                            "avatar": user_data.get("avatar", ""),
                            "titlePhoto": user_data.get("titlePhoto", ""),
                        }
                        results[handle_key] = info
                        _CF_CACHE[handle_key] = {
                            "data": info,
                            "expires_at": now + _CACHE_TTL_SECONDS,
                        }
            else:
                # If batch failed (e.g. one invalid handle in batch), fallback to single lookups
                for single_h in to_fetch:
                    try:
                        s_resp = requests.get(f"{cls.BASE_URL}/user.info?handles={single_h}", timeout=2.0)
                        if s_resp.status_code == 200 and s_resp.json().get("status") == "OK":
                            u_data = s_resp.json()["result"][0]
                            info = {
                                "handle": u_data.get("handle", single_h),
                                "rating": u_data.get("rating", 0) or 0,
                                "maxRating": u_data.get("maxRating", 0) or 0,
                                "rank": u_data.get("rank", "unrated") or "unrated",
                                "maxRank": u_data.get("maxRank", "unrated") or "unrated",
                                "avatar": u_data.get("avatar", ""),
                                "titlePhoto": u_data.get("titlePhoto", ""),
                            }
                            results[single_h.lower()] = info
                            _CF_CACHE[single_h.lower()] = {
                                "data": info,
                                "expires_at": now + _CACHE_TTL_SECONDS,
                            }
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Failed to fetch Codeforces user info for handles {to_fetch}: {e}")

        return results

    @classmethod
    def _get_from_cache(cls, handle: str) -> Optional[Dict[str, Any]]:
        cached = _CF_CACHE.get(handle.lower())
        if cached and cached["expires_at"] > time.time():
            return cached["data"]
        return None
