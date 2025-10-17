import os
import re
import json
import logging
import aiohttp
import asyncio
import ssl
import certifi
from bs4 import BeautifulSoup
from dotenv import load_dotenv


class PastryClient:
    def __init__(self, base_url="https://pastry.diy", verify_ssl=True, cert_path=None):
        load_dotenv()
        self.username = os.getenv("PASTRY_USERNAME")
        self.token = os.getenv("PASTRY_TOKEN")

        if not self.username or not self.token:
            raise ValueError("PASTRY_USERNAME or PASTRY_TOKEN not set in environment or .env file.")

        self.base_url = base_url.rstrip("/")
        self.verify_ssl = verify_ssl
        self.cert_path = cert_path or certifi.where()
        self.ssl_context = None

        if verify_ssl:
            self.ssl_context = ssl.create_default_context(cafile=self.cert_path)
        else:
            self.ssl_context = False

        self.arr = []
        self.session: aiohttp.ClientSession | None = None
        self.banned_words = self._refresh_banned_words()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=self.ssl_context),
            headers={"User-Agent": "Mozilla/5.0 (PastryAdminBot/2.0)"}
        )
        await self._login()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()

    # --- Banned words loader ---
    def _refresh_banned_words(self) -> list[str]:
        banned_path = r"C:\Users\savaj\OneDrive\Documents\coding_tests\admin bot 2\banned.json"
        try:
            with open(banned_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                if all(isinstance(entry, dict) and "word" in entry for entry in data):
                    words = [entry["word"].lower() for entry in data]
                elif all(isinstance(entry, str) for entry in data):
                    words = [entry.lower() for entry in data]
                else:
                    words = []
            else:
                words = []
            logging.info(f"Loaded {len(words)} banned words.")
            return words
        except Exception as e:
            logging.warning(f"Could not load banned.json: {e}")
            return []

    # --- Async login ---
    async def _login(self):
        login_url = f"{self.base_url}/login"
        try:
            async with self.session.get(login_url) as resp:
                text = await resp.text()
                soup = BeautifulSoup(text, "html.parser")
                csrf = soup.find("input", {"name": "csrf_token"})
                payload = {"username": self.username, "user_token": self.token}
                if csrf:
                    payload["csrf_token"] = csrf.get("value", "")

            async with self.session.post(login_url, data=payload) as resp:
                html = await resp.text()
                if "Welcome, guest!" in html:
                    logging.error("Login failed — check credentials.")
                else:
                    logging.info("Login successful.")
        except Exception as e:
            logging.exception(f"Login error: {e}")

    # --- Async data fetching ---
    async def _get_total_pages(self) -> int:
        try:
            async with self.session.get(f"{self.base_url}/admin/pastes") as resp:
                text = await resp.text()
                soup = BeautifulSoup(text, "html.parser")
                pagination = soup.find("nav", class_="pagination")
                if pagination:
                    match = re.search(r"Page \d+ of (\d+)", pagination.get_text(strip=True))
                    if match:
                        return int(match.group(1))
        except Exception as e:
            logging.warning(f"Could not get total pages: {e}")
        return 1

    async def _fetch_page_entries(self, page_num: int):
        """Fetch entries from a single admin page asynchronously."""
        url = f"{self.base_url}/admin/pastes"
        if page_num > 1:
            url += f"?page={page_num}"

        try:
            async with self.session.get(url) as resp:
                text = await resp.text()
                soup = BeautifulSoup(text, "html.parser")
                entries = []
                for row in soup.select("tr"):
                    link = row.find("a", href=True)
                    user_link = row.find("a", href=re.compile(r"^/profile/"))
                    if link and user_link:
                        paste_url = link["href"]
                        username = user_link["href"].split("/")[-1]
                        entries.append([paste_url, username])
                return entries
        except Exception as e:
            logging.warning(f"Error fetching page {page_num}: {e}")
            return []

    # --- Async database refresh ---
    async def refresh_database(self):
        total_pages = await self._get_total_pages()
        self.arr.clear()
        logging.info(f"Fetching {total_pages} pages...")

        # fetch pages concurrently but not all at once (to avoid server overload)
        semaphore = asyncio.Semaphore(10)
        async def limited_fetch(p):
            async with semaphore:
                return await self._fetch_page_entries(p)

        tasks = [limited_fetch(p) for p in range(1, total_pages + 1)]
        results = await asyncio.gather(*tasks)
        for res in results:
            self.arr.extend(res)

        logging.info(f"Database refreshed. Found {len(self.arr)} entries.")

    # --- Check functions ---
    def check_for_banned_urls(self):
        flagged = []
        banned_set = {f"/{w}" for w in self.banned_words}
        for url, owner in self.arr:
            if owner == self.username:
                continue
            if url.lower() in banned_set:
                flagged.append((url, owner))
                logging.warning(f"BANNED WORD DETECTED: {url} owned by {owner}")
        return flagged

    def search_by_username(self, username: str) -> str:
        urls = [url for url, owner in self.arr if owner.lower() == username.lower()]
        return f"User {username} owns the URLs: {', '.join(urls)}" if urls else f"User {username} not found, OR they don't own any urls."

    def search_by_url(self, url: str) -> str:
        for u, owner in self.arr:
            if u.strip("/") == url.strip("/"):
                return f"{owner} owns the URL {u}"
        return f"No owner found for URL: {url}"
