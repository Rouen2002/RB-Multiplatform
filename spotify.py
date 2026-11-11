import os
import re
import shutil
import subprocess
import time
from urllib.parse import urlparse

import requests
from mutagen.id3 import APIC, TIT2, TPE1, TALB, TDRC
from mutagen.mp3 import MP3

# ─────────────────────────────────────────────
# ⚙️  CONFIGURACIÓN (edita aquí)
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
# 🎨  COLORES ANSI
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
# 🔵  BANNER
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
{C.WHITE}{C.BOLD}       🎬  RB MODS  ·  MULTI-DOWNLOADER v{VERSION}  🎵{C.RESET}
{C.DIM} Spotify · YT Music · YouTube · TikTok · Instagram{C.RESET}
"""
    print(art)
    print(f"{C.BLUE}╔══════════════════════════════════════════════════════╗{C.RESET}")
    print(f"{C.BLUE}║{C.RESET}  {C.CYAN}▸ Autor   :{C.RESET} {C.WHITE}RB MODS{C.RESET}")
    print(f"{C.BLUE}║{C.RESET}  {C.CYAN}▸ Versión :{C.RESET} {C.WHITE}{VERSION}{C.RESET}")
    print(f"{C.BLUE}╚══════════════════════════════════════════════════════╝{C.RESET}")
    print()

# ─────────────────────────────────────────────
# 📊  BARRA DE PROGRESO Y MARCOS
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
# 🧹  UTILIDADES
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

def download_stream(url, path, timeout=60):
    try:
        with requests.get(url, headers={"User-Agent": USER_AGENT}, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 128):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            print(f"\r{C.CYAN}📥{C.RESET} {progress_bar(downloaded * 100 / total)}", end="", flush=True)
        print()
    except BaseException:
        remove_if_exists(path)
        raise

def wake_lock(on=True):
    cmd = "termux-wake-lock" if on else "termux-wake-unlock"
    if shutil.which(cmd):
        subprocess.run([cmd], check=False)

# ─────────────────────────────────────────────
# 🎯  DETECCIÓN DE PLATAFORMA POR URL
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
# 🎵  SPOTIFY (API + YT-DLP para canción completa)
# ─────────────────────────────────────────────

def download_spotify(url):
    mp3_path = None
    jpg_path = None
    try:
        section("🔎  Consultando Spotify API...", C.CYAN)

        r = requests.post(
            SPOTIFY_API,
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
            json={"url": url},
            timeout=30,
        )
        if r.status_code != 200:
            print(f"{C.RED}❌ {r.status_code}: {r.text[:200]}{C.RESET}")
            return False

        metadata = r.json().get("data", {}).get("metadata", {})

        name = metadata.get("name", "Unknown")
        artist = metadata.get("artist", "Unknown")
        album = metadata.get("album", "")
        duration = metadata.get("duration", "")
        image_url = metadata.get("image", "")

        print()
        print(f"{C.BLUE}╭──────────────────────────────────────────────────────╮{C.RESET}")
        print(f"{C.BLUE}│{C.RESET}  {C.BOLD}🎵 Canción  :{C.RESET} {C.WHITE}{name}{C.RESET}")
        print(f"{C.BLUE}│{C.RESET}  {C.BOLD}👤 Artista  :{C.RESET} {C.WHITE}{artist}{C.RESET}")
        print(f"{C.BLUE}│{C.RESET}  {C.BOLD}💿 Álbum    :{C.RESET} {C.WHITE}{album or '—'}{C.RESET}")
        print(f"{C.BLUE}│{C.RESET}  {C.BOLD}⏱️  Duración :{C.RESET} {C.WHITE}{duration or '—'}{C.RESET}")
        print(f"{C.BLUE}╰──────────────────────────────────────────────────────╯{C.RESET}")

        os.makedirs(PLATFORM_DIRS["spotify"], exist_ok=True)
        filename = safe_filename(f"{artist} - {name}")
        mp3_path = os.path.join(PLATFORM_DIRS["spotify"], filename + ".mp3")
        jpg_path = os.path.join(PLATFORM_DIRS["spotify"], filename + ".jpg")

        if image_url:
            section("🖼️  Descargando portada...", C.CYAN)
            try:
                with requests.get(image_url, headers={"User-Agent": USER_AGENT}, timeout=30) as ir:
                    ir.raise_for_status()
                    with open(jpg_path, "wb") as f:
                        f.write(ir.content)
                print(f"{C.GREEN}✅ Portada guardada.{C.RESET}")
            except requests.RequestException as e:
                remove_if_exists(jpg_path)
                print(f"{C.YELLOW}⚠️  No se pudo bajar la portada: {e}{C.RESET}")

        section("⬇️  Descargando canción completa (vía yt-dlp)...", C.BLUE)
        if not shutil.which("yt-dlp"):
            print(f"{C.RED}❌ yt-dlp no está instalado. Instálalo con: pip install yt-dlp{C.RESET}")
            return False

        search_query = f"ytsearch1:{artist} - {name}"
        template = os.path.join(PLATFORM_DIRS["spotify"], f"{filename}.%(ext)s")
        
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--no-playlist",
            "-o", template,
            search_query
        ]
        
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"\n{C.RED}❌ Falló la descarga de audio para '{artist} - {name}'.{C.RESET}")
            return False

        print(f"{C.GREEN}✅ Audio completo descargado.{C.RESET}")

        try:
            section("🏷️  Añadiendo metadatos...", C.YELLOW)
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
                print(f"{C.GREEN}✅ Metadatos y portada añadidos.{C.RESET}")
        except Exception as e:
            print(f"{C.YELLOW}⚠️  No se pudieron añadir metadatos: {e}{C.RESET}")

        resumen_final(mp3_path, jpg_path, "Spotify")
        return True

    except KeyboardInterrupt:
        remove_if_exists(mp3_path)
        remove_if_exists(jpg_path)
        raise
    except requests.RequestException as e:
        print(f"\n{C.RED}❌ Error de conexión: {e}{C.RESET}")
        return False
    except Exception as e:
        print(f"\n{C.RED}❌ Error: {e}{C.RESET}")
        return False

# ─────────────────────────────────────────────
# 🎶  YOUTUBE MUSIC Y AUDIO (yt-dlp)
# ─────────────────────────────────────────────

def download_ytdlp_audio(url, platform):
    if not shutil.which("yt-dlp"):
        print(f"{C.RED}❌ yt-dlp no está instalado. Instálalo con: pip install yt-dlp{C.RESET}")
        return False

    out_dir = PLATFORM_DIRS.get(platform, PLATFORM_DIRS["otros"])
    os.makedirs(out_dir, exist_ok=True)
    template = os.path.join(out_dir, "%(title).100s.%(ext)s")

    section(f"⬇️  Descargando audio ({platform.capitalize()})...", C.BLUE)
    cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "--no-playlist", "-o", template, url]
    result = subprocess.run(cmd, check=False)

    if result.returncode == 0:
        print(f"\n{C.GREEN}✅ Audio guardado en: {C.CYAN}{out_dir}{C.RESET}")
        return True

    print(f"\n{C.RED}❌ yt-dlp falló (código {result.returncode}).{C.RESET}")
    return False

# ─────────────────────────────────────────────
# 🎬  OTRAS PLATAFORMAS (Videos con yt-dlp)
# ─────────────────────────────────────────────

def download_ytdlp(url, platform):
    if not shutil.which("yt-dlp"):
        print(f"{C.RED}❌ yt-dlp no está instalado. Instálalo con: pip install yt-dlp{C.RESET}")
        return False

    out_dir = PLATFORM_DIRS.get(platform, PLATFORM_DIRS["otros"])
    os.makedirs(out_dir, exist_ok=True)
    template = os.path.join(out_dir, "%(title).100s.%(ext)s")

    section(f"⬇️  Descargando ({platform.capitalize()})...", C.BLUE)
    result = subprocess.run(["yt-dlp", "--no-playlist", "-o", template, url], check=False)

    if result.returncode == 0:
        print(f"\n{C.GREEN}✅ Archivo guardado en: {C.CYAN}{out_dir}{C.RESET}")
        return True

    print(f"\n{C.RED}❌ yt-dlp falló (código {result.returncode}).{C.RESET}")
    return False

# ─────────────────────────────────────────────
# 🎉  RESUMEN FINAL
# ─────────────────────────────────────────────

def resumen_final(media_path, cover_path, platform_name):
    print()
    print(f"{C.GREEN}╔══════════════════════════════════════════════════════╗{C.RESET}")
    print(f"{C.GREEN}║{C.RESET}            {C.BOLD}🎉  ¡DESCARGA COMPLETADA!{C.RESET}")
    print(f"{C.GREEN}╠══════════════════════════════════════════════════════╣{C.RESET}")
    print(f"{C.GREEN}║{C.RESET}  🌐 Plataforma : {C.CYAN}{platform_name}{C.RESET}")
    print(f"{C.GREEN}║{C.RESET}  📁 Carpeta    : {C.CYAN}{os.path.dirname(media_path)}{C.RESET}")
    print(f"{C.GREEN}║{C.RESET}  📄 Archivo    : {C.CYAN}{os.path.basename(media_path)}{C.RESET}")
    if cover_path and os.path.exists(cover_path):
        print(f"{C.GREEN}║{C.RESET}  🖼️  Portada    : {C.CYAN}{os.path.basename(cover_path)}{C.RESET}")
    print(f"{C.GREEN}╠══════════════════════════════════════════════════════╣{C.RESET}")
    print(f"{C.GREEN}║{C.RESET}  {C.DIM}Hecho por {C.RESET}{C.WHITE}{C.BOLD}RB MODS{C.RESET} {C.DIM}· v{VERSION}{C.RESET}")
    print(f"{C.GREEN}╚══════════════════════════════════════════════════════╝{C.RESET}")

# ─────────────────────────────────────────────
# 🔁  BUCLE PRINCIPAL
# ─────────────────────────────────────────────

def process(url):
    platform = detect_platform(url)
    print(f"{C.DIM}   ↪ Plataforma detectada: {C.RESET}{C.BOLD}{platform.capitalize()}{C.RESET}")

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

    print(f"\n{C.BLUE}👋 ¡Hasta luego!  {C.DIM}— RB MODS{C.RESET}\n")

def run_loop():
    while True:
        try:
            url = clean_url(input(f"{C.CYAN}🔗 Pega la URL (o 'q' para salir):{C.RESET} "))

            if url.lower() in ("q", "quit", "exit", "salir"):
                break

            if not url:
                print(f"{C.RED}❌ No ingresaste ninguna URL.{C.RESET}\n")
                continue

            process(url)

            print()
            again = input(f"{C.YELLOW}🔁 ¿Descargar otra? (s/n):{C.RESET} ").strip().lower()
            if again not in ("s", "si", "sí", "y", "yes"):
                break

            clear()
            banner()

        except KeyboardInterrupt:
            print(f"\n{C.YELLOW}⚠️  Descarga cancelada. Archivo incompleto eliminado.{C.RESET}\n")

if __name__ == "__main__":
    main()
