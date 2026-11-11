import os
import re
import shutil
import subprocess
import time
from urllib.parse import urlparse

import requests
from mutagen.id3 import APIC, TIT2, TPE1, TALB, TDRC
from mutagen.mp3 import MP3
import yt_dlp

# ─────────────────────────────────────────────
# CONFIGURACION (edita aquí)
# ─────────────────────────────────────────────

VERSION = "2.5"
BASE_DIR = "/storage/emulated/0/Download"
SPOTIFY_API = "https://musicfab.io/api/spotify"
USER_AGENT = "Mozilla/5.0"

AUDIO_DIR = os.path.join(BASE_DIR, "RB-Audio")
VIDEO_DIR = os.path.join(BASE_DIR, "RB-Video")

PLATFORM_DIRS = {
    "spotify": os.path.join(AUDIO_DIR, "Spotify"),
    "youtubemusic": os.path.join(AUDIO_DIR, "YouTubeMusic"),
    "soundcloud": os.path.join(AUDIO_DIR, "SoundCloud"),
    "facebook": os.path.join(VIDEO_DIR, "Facebook"),
    "instagram": os.path.join(VIDEO_DIR, "Instagram"),
    "tiktok": os.path.join(VIDEO_DIR, "TikTok"),
    "youtube": os.path.join(VIDEO_DIR, "YouTube"),
    "twitter": os.path.join(VIDEO_DIR, "Twitter"),
    "reddit": os.path.join(VIDEO_DIR, "Reddit"),
    "pinterest": os.path.join(VIDEO_DIR, "Pinterest"),
    "vimeo": os.path.join(VIDEO_DIR, "Vimeo"),
    "twitch": os.path.join(VIDEO_DIR, "Twitch"),
    "otros": os.path.join(VIDEO_DIR, "Otros"),
}

# ─────────────────────────────────────────────
# COLORES ANSI
# ─────────────────────────────────────────────

class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

# ─────────────────────────────────────────────
# BANNER
# ─────────────────────────────────────────────

def banner():
    clear()
    art = f"""
{C.BLUE}{C.BOLD}
███████╗██████╗  ██████╗ ████████╗██╗███████╗██╗   ██╗
██╔════╝██╔══██╗██╔═══██╗╚══██╔══╝██║██╔════╝╚██╗ ██╔╝
███████╗██████╔╝██║   ██║   ██║   ██║█████╗   ╚████╔╝
╚════██║██╔═══╝ ██║   ██║   ██║   ██║██╔══╝    ╚██╔╝
███████║██║     ╚██████╔╝   ██║   ██║██║        ██║
╚══════╝╚═╝      ╚═════╝    ╚═╝   ╚═╝╚═╝        ╚═╝
{C.RESET}
{C.WHITE}{C.BOLD}         RB MODS  ·  MULTI-DOWNLOADER v{VERSION}         {C.RESET}
{C.DIM} Spotify · YT Music · YouTube · TikTok · Instagram{C.RESET}
"""
    print(art)
    print(f"{C.BLUE}╔══════════════════════════════════════════════════════╗{C.RESET}")
    print(f"{C.BLUE}║{C.RESET}  {C.CYAN}Autor   :{C.RESET} {C.WHITE}RB MODS{C.RESET}")
    print(f"{C.BLUE}║{C.RESET}  {C.CYAN}Versión :{C.RESET} {C.WHITE}{VERSION}{C.RESET}")
    print(f"{C.BLUE}╚══════════════════════════════════════════════════════╝{C.RESET}")
    print()

# ─────────────────────────────────────────────
# BARRA DE PROGRESO Y MARCOS
# ─────────────────────────────────────────────

def progress_bar(percent, length=30):
    filled = int(length * percent / 100)
    bar = "█" * filled + "░" * (length - filled)
    color = C.RED if percent < 30 else C.YELLOW if percent < 70 else C.GREEN
    return f"{color}{bar}{C.RESET} {C.BOLD}{percent:6.2f}%{C.RESET}"

def section(title, color=C.BLUE):
    print()
    print(f"{color}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{C.RESET}")
    print(f"{color}┃{C.RESET} {C.BOLD}{title}{C.RESET}")
    print(f"{color}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{C.RESET}")

# ─────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────

def clean_url(url, strip_query=False):
    url = url.replace("\\", "").strip()
    if strip_query:
        p = urlparse(url)
        url = f"{p.scheme}://{p.netloc}{p.path}"
    return url

def safe_filename(text):
    return re.sub(r'[\/:*?"<>|]', "", text).strip()

def remove_if_exists(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass

def wake_lock(on=True):
    cmd = "termux-wake-lock" if on else "termux-wake-unlock"
    if shutil.which(cmd):
        subprocess.run([cmd], check=False)

# ─────────────────────────────────────────────
# DETECCION DE PLATAFORMA POR URL
# ─────────────────────────────────────────────

PLATFORM_HOSTS = [
    ("spotify", ("spotify.com",)),
    ("youtubemusic", ("music.youtube.com",)),
    ("facebook", ("facebook.com", "fb.watch")),
    ("instagram", ("instagram.com",)),
    ("tiktok", ("tiktok.com",)),
    ("youtube", ("youtube.com", "youtu.be")),
    ("twitter", ("twitter.com", "x.com")),
    ("reddit", ("reddit.com",)),
    ("soundcloud", ("soundcloud.com",)),
    ("pinterest", ("pinterest.com", "pin.it")),
    ("vimeo", ("vimeo.com",)),
    ("twitch", ("twitch.tv",)),
]

def detect_platform(url):
    host = urlparse(url).netloc.lower()
    for name, hosts in PLATFORM_HOSTS:
        if any(host == h or host.endswith("." + h) for h in hosts):
            return name
    return "otros"

# ─────────────────────────────────────────────
# SPOTIFY (API + YT-DLP con barra de progreso)
# ─────────────────────────────────────────────

def download_spotify(url):
    mp3_path = None
    jpg_path = None
    try:
        section("Consultando Spotify API...", C.CYAN)

        r = requests.post(
            SPOTIFY_API,
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
            json={"url": url},
            timeout=30,
        )
        if r.status_code != 200:
            print(f"{C.RED}[ERROR] {r.status_code}: {r.text[:200]}{C.RESET}")
            return False

        metadata = r.json().get("data", {}).get("metadata", {})

        name = metadata.get("name", "Unknown")
        artist = metadata.get("artist", "Unknown")
        album = metadata.get("album", "")
        duration = metadata.get("duration", "")
        image_url = metadata.get("image", "")

        print()
        print(f"{C.BLUE}╭──────────────────────────────────────────────────────╮{C.RESET}")
        print(f"{C.BLUE}│{C.RESET}  {C.BOLD}Canción  :{C.RESET} {C.WHITE}{name}{C.RESET}")
        print(f"{C.BLUE}│{C.RESET}  {C.BOLD}Artista  :{C.RESET} {C.WHITE}{artist}{C.RESET}")
        print(f"{C.BLUE}│{C.RESET}  {C.BOLD}Álbum    :{C.RESET} {C.WHITE}{album or '—'}{C.RESET}")
        print(f"{C.BLUE}│{C.RESET}  {C.BOLD}Duración :{C.RESET} {C.WHITE}{duration or '—'}{C.RESET}")
        print(f"{C.BLUE}╰──────────────────────────────────────────────────────╯{C.RESET}")

        os.makedirs(PLATFORM_DIRS["spotify"], exist_ok=True)
        filename = safe_filename(f"{artist} - {name}")
        mp3_path = os.path.join(PLATFORM_DIRS["spotify"], filename + ".mp3")
        jpg_path = os.path.join(PLATFORM_DIRS["spotify"], filename + ".jpg")

        if image_url:
            section("Descargando portada...", C.CYAN)
            try:
                with requests.get(image_url, headers={"User-Agent": USER_AGENT}, timeout=30) as ir:
                    ir.raise_for_status()
                    with open(jpg_path, "wb") as f:
                        f.write(ir.content)
                print(f"{C.GREEN}[OK] Portada guardada.{C.RESET}")
            except requests.RequestException as e:
                remove_if_exists(jpg_path)
                print(f"{C.YELLOW}[AVISO] No se pudo descargar la portada: {e}{C.RESET}")

        section("Descargando canción (vía API)...", C.BLUE)

        def my_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = (downloaded / total) * 100
                    print(f"\r[INFO] {progress_bar(percent)}", end="", flush=True)
                else:
                    print(f"\r[INFO] {C.YELLOW}Descargando fragmentos... ({downloaded // 1024} KB){C.RESET}", end="", flush=True)
            elif d['status'] == 'finished':
                print(f"\r[INFO] {progress_bar(100.00)} - Procesando audio...", flush=True)

        search_query = f"ytsearch1:{artist} - {name}"
        outtmpl = os.path.join(PLATFORM_DIRS["spotify"], f"{filename}.%(ext)s")

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': outtmpl,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [my_hook],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_query])

        print(f"\n{C.GREEN}[OK] Audio completo descargado.{C.RESET}")

        try:
            section("Añadiendo metadatos...", C.YELLOW)
            if os.path.exists(mp3_path):
                audio = MP3(mp3_path)
                if audio.tags is None:
                    audio.add_tags()
                audio.tags.add(TIT2(encoding=3, text=name))
                audio.tags.add(TPE1(encoding=3, text=artist))
                if album:
                    audio.tags.add(TALB(encoding=3, text=album))
                year = metadata.get("release_year")
                if year:
                    audio.tags.add(TDRC(encoding=3, text=str(year)))
                if os.path.exists(jpg_path):
                    with open(jpg_path, "rb") as img:
                        audio.tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=img.read()))
                audio.save()
                print(f"{C.GREEN}[OK] Metadatos y portada añadidos.{C.RESET}")
        except Exception as e:
            print(f"{C.YELLOW}[AVISO] No se pudieron añadir metadatos: {e}{C.RESET}")

        resumen_final(mp3_path, jpg_path, "Spotify")
        return True

    except KeyboardInterrupt:
        remove_if_exists(mp3_path)
        remove_if_exists(jpg_path)
        raise
    except Exception as e:
        print(f"\n{C.RED}[ERROR] Error: {e}{C.RESET}")
        return False

# ─────────────────────────────────────────────
# YOUTUBE MUSIC Y AUDIO (yt-dlp)
# ─────────────────────────────────────────────

def download_ytdlp_audio(url, platform):
    out_dir = PLATFORM_DIRS.get(platform, PLATFORM_DIRS["otros"])
    os.makedirs(out_dir, exist_ok=True)
    template = os.path.join(out_dir, "%(title).100s.%(ext)s")

    section(f"Descargando audio ({platform.capitalize()})...", C.BLUE)
    
    def my_hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                percent = (downloaded / total) * 100
                print(f"\r[INFO] {progress_bar(percent)}", end="", flush=True)
            else:
                print(f"\r[INFO] {C.YELLOW}Descargando fragmentos... ({downloaded // 1024} KB){C.RESET}", end="", flush=True)
        elif d['status'] == 'finished':
            print(f"\r[INFO] {progress_bar(100.00)} - Procesando audio...", flush=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': template,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [my_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"\n{C.GREEN}[OK] Audio guardado en: {C.CYAN}{out_dir}{C.RESET}")
        return True
    except Exception as e:
        print(f"\n{C.RED}[ERROR] Falló la descarga: {e}{C.RESET}")
        return False

# ─────────────────────────────────────────────
# OTRAS PLATAFORMAS (Videos con yt-dlp)
# ─────────────────────────────────────────────

def download_ytdlp(url, platform):
    out_dir = PLATFORM_DIRS.get(platform, PLATFORM_DIRS["otros"])
    os.makedirs(out_dir, exist_ok=True)
    template = os.path.join(out_dir, "%(title).100s.%(ext)s")

    section(f"Descargando ({platform.capitalize()})...", C.BLUE)

    def my_hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                percent = (downloaded / total) * 100
                print(f"\r[INFO] {progress_bar(percent)}", end="", flush=True)
            else:
                print(f"\r[INFO] {C.YELLOW}Descargando fragmentos... ({downloaded // 1024} KB){C.RESET}", end="", flush=True)
        elif d['status'] == 'finished':
            print(f"\r[INFO] {progress_bar(100.00)}", flush=True)

    ydl_opts = {
        'outtmpl': template,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [my_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"\n{C.GREEN}[OK] Archivo guardado en: {C.CYAN}{out_dir}{C.RESET}")
        return True
    except Exception as e:
        print(f"\n{C.RED}[ERROR] Falló la descarga: {e}{C.RESET}")
        return False

# ─────────────────────────────────────────────
# RESUMEN FINAL
# ─────────────────────────────────────────────

def resumen_final(media_path, cover_path, platform_name):
    print()
    print(f"{C.GREEN}╔══════════════════════════════════════════════════════╗{C.RESET}")
    print(f"{C.GREEN}║{C.RESET}                [DESCARGA COMPLETADA]                 {C.GREEN}║{C.RESET}")
    print(f"{C.GREEN}╠══════════════════════════════════════════════════════╣{C.RESET}")
    print(f"{C.GREEN}║{C.RESET}  Plataforma : {C.CYAN}{platform_name}{C.RESET}")
    print(f"{C.GREEN}║{C.RESET}  Carpeta    : {C.CYAN}{os.path.dirname(media_path)}{C.RESET}")
    print(f"{C.GREEN}║{C.RESET}  Archivo    : {C.CYAN}{os.path.basename(media_path)}{C.RESET}")
    if cover_path and os.path.exists(cover_path):
        print(f"{C.GREEN}║{C.RESET}  Portada    : {C.CYAN}{os.path.basename(cover_path)}{C.RESET}")
    print(f"{C.GREEN}╠══════════════════════════════════════════════════════╣{C.RESET}")
    print(f"{C.GREEN}║{C.RESET}  {C.DIM}Hecho por {C.RESET}{C.WHITE}{C.BOLD}RB MODS{C.RESET} {C.DIM}· v{VERSION}{C.RESET}")
    print(f"{C.GREEN}╚══════════════════════════════════════════════════════╝{C.RESET}")

# ─────────────────────────────────────────────
# BUCLE PRINCIPAL
# ─────────────────────────────────────────────

def process(url):
    platform = detect_platform(url)
    print(f"{C.DIM}   Plataforma detectada: {C.RESET}{C.BOLD}{platform.capitalize()}{C.RESET}")

    if platform == "spotify":
        url = clean_url(url, strip_query=True)
        download_spotify(url)
    elif platform == "youtubemusic":
        download_ytdlp_audio(url, platform)
    elif platform == "soundcloud":
        download_ytdlp_audio(url, platform)
    else:
        download_ytdlp(url, platform)

def main():
    banner()
    wake_lock(True)

    try:
        run_loop()
    finally:
        wake_lock(False)

    print(f"\n{C.BLUE}¡Hasta luego!  {C.DIM}— RB MODS{C.RESET}\n")

def run_loop():
    while True:
        try:
            url = clean_url(input(f"{C.CYAN}Ingrese la URL (o 'q' para salir): {C.RESET} "))

            if url.lower() in ("q", "quit", "exit", "salir"):
                break

            if not url:
                print(f"{C.RED}[ERROR] No ingresó ninguna URL.{C.RESET}\n")
                continue

            process(url)

            print()
            again = input(f"{C.YELLOW}¿Descargar otra? (s/n): {C.RESET} ").strip().lower()
            if again not in ("s", "si", "sí", "y", "yes"):
                break

            clear()
            banner()

        except KeyboardInterrupt:
            print(f"\n{C.YELLOW}[AVISO] Descarga cancelada. Archivo incompleto eliminado.{C.RESET}\n")

if __name__ == "__main__":
    main()
