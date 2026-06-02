import sys
sys.stdout.reconfigure(encoding='utf-8')

import tkinter as tk
from tkinter import filedialog
import pygame
import os
import json
from mutagen import File as MutagenFile

# ─────────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────────
BG_DEEP    = "#0d0d14"
BG_CARD    = "#13131f"
BG_SURFACE = "#1a1a2e"
ACCENT     = "#7c3aed"
ACCENT2    = "#a855f7"
ACCENT_HOV = "#9d5cf5"
DANGER     = "#ef4444"
GOLD       = "#fbbf24"
TEXT_PRI   = "#f0f0ff"
TEXT_SEC   = "#888aaa"
TEXT_DIM   = "#555575"
SEL_BG     = "#3b1fa8"
SEL_FG     = "#ffffff"

# ─────────────────────────────────────────────
#  DOUBLE LINKED LIST
# ─────────────────────────────────────────────
class SongNode:
    def __init__(self, song_title):
        self.song_title = song_title
        self.prev = None
        self.next = None

class Playlist:
    def __init__(self):
        self.head = None
        self.tail = None
        self.current = None
        self.size = 0

    def add_song(self, song_title):
        new_node = SongNode(song_title)
        if self.head is None:
            self.head = self.tail = self.current = new_node
        else:
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
        self.size += 1

    def clear(self):
        self.head = self.tail = self.current = None
        self.size = 0

    def get_current_song(self):
        return self.current.song_title if self.current else ""

    def set_current_song(self, song_title):
        node = self.head
        while node:
            if node.song_title == song_title:
                self.current = node
                return True
            node = node.next
        return False

    def next_song(self):
        if self.current and self.current.next:
            self.current = self.current.next
            return self.current.song_title
        return None

    def prev_song(self):
        if self.current and self.current.prev:
            self.current = self.current.prev
            return self.current.song_title
        return None

    def get_all_songs(self):
        songs, node = [], self.head
        while node:
            songs.append(node.song_title)
            node = node.next
        return songs

    def get_current_index(self):
        idx, node = 0, self.head
        while node:
            if node == self.current:
                return idx
            node = node.next
            idx += 1
        return -1

# ─────────────────────────────────────────────
#  ROOT WINDOW
# ─────────────────────────────────────────────
root = tk.Tk()
root.title("MusicFlow")
root.geometry("680x560")
root.configure(bg=BG_DEEP)
root.resizable(False, False)

# Init pygame mixer dengan buffer besar agar tidak patah-patah
pygame.mixer.pre_init(44100, -16, 2, 4096)
pygame.mixer.init()

# ─────────────────────────────────────────────
#  STATE
# ─────────────────────────────────────────────
playlist     = Playlist()
current_song = ""
paused       = False
is_playing   = False
CONFIG_FILE  = "music_player_config.json"

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
def save_config(directory):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"last_directory": directory}, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f).get("last_directory", "")
    return ""

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def trunc(text, maxlen=44):
    return text[:maxlen - 3] + "..." if len(text) > maxlen else text

# ─────────────────────────────────────────────
#  ALBUM ART (gradient vinyl)
# ─────────────────────────────────────────────
def draw_album_art(title=""):
    album_canvas.delete("all")
    w, h = 200, 200
    for i in range(38, 0, -1):
        r = i / 38
        cr = int(70 + 70 * r)
        cg = int(15 + 10 * r)
        cb = int(160 + 80 * r)
        col = f"#{cr:02x}{cg:02x}{cb:02x}"
        d = i * 5
        album_canvas.create_oval(w//2 - d, h//2 - d, w//2 + d, h//2 + d,
                                  fill=col, outline="")
    album_canvas.create_oval(60, 60, 140, 140, fill=BG_DEEP,
                              outline="#445", width=1)
    album_canvas.create_oval(95, 95, 105, 105, fill="#333355",
                              outline="#556", width=1)
    album_canvas.create_text(w//2, h//2 - 2, text="♫",
                              font=("Segoe UI", 28, "bold"),
                              fill="#ccccff", anchor="center")

# ─────────────────────────────────────────────
#  UPDATE NOW-PLAYING
# ─────────────────────────────────────────────
def update_now_playing():
    if not current_song:
        lbl_title.config(text="Pilih lagu untuk diputar", fg=TEXT_DIM)
        lbl_artist.config(text="—", fg=TEXT_DIM)
        lbl_status.config(text="⏹  Stopped", fg=TEXT_DIM)
        draw_album_art()
        return

    name = os.path.splitext(current_song)[0]
    
    artist = ""
    title = ""
    try:
        audio = MutagenFile(os.path.join(root.directory, current_song))
        if audio and audio.tags:
            # MP3 (ID3)
            if 'TPE1' in audio.tags: artist = str(audio.tags['TPE1'].text[0])
            if 'TIT2' in audio.tags: title = str(audio.tags['TIT2'].text[0])
            # FLAC / OGG / M4A
            if not artist and 'artist' in audio.tags: artist = str(audio.tags['artist'][0])
            if not artist and '\xa9ART' in audio.tags: artist = str(audio.tags['\xa9ART'][0])
            if not title and 'title' in audio.tags: title = str(audio.tags['title'][0])
            if not title and '\xa9nam' in audio.tags: title = str(audio.tags['\xa9nam'][0])
    except Exception:
        pass
        
    if not title:
        if " - " in name:
            artist_split, title_split = name.split(" - ", 1)
            title = title_split
            if not artist:
                artist = artist_split
        else:
            title = name
            
    if not artist:
        artist = "Unknown Artist"

    lbl_title.config(text=trunc(title), fg=TEXT_PRI)
    lbl_artist.config(text=trunc(artist), fg=TEXT_SEC)

    draw_album_art(current_song)

    if is_playing:
        lbl_status.config(text="▶  Now Playing", fg=ACCENT2)
        btn_play.config(text="⏸")
    elif paused:
        lbl_status.config(text="⏸  Paused", fg=GOLD)
        btn_play.config(text="▶")
    else:
        lbl_status.config(text="⏹  Stopped", fg=TEXT_DIM)
        btn_play.config(text="▶")

# ─────────────────────────────────────────────
#  REFRESH PLAYLIST BOX
# ─────────────────────────────────────────────
def refresh_playlist_box():
    songlist.delete(0, tk.END)
    for song in playlist.get_all_songs():
        name = os.path.splitext(song)[0]
        songlist.insert(tk.END, f"  {name}")
    idx = playlist.get_current_index()
    if idx >= 0:
        songlist.selection_clear(0, tk.END)
        songlist.selection_set(idx)
        songlist.see(idx)

# ─────────────────────────────────────────────
#  LOAD SONGS
# ─────────────────────────────────────────────
def load_songs_from_directory(directory):
    global current_song
    if not directory or not os.path.exists(directory):
        return False
    playlist.clear()
    audio_ext = {".mp3", ".wav", ".ogg", ".m4a", ".flac"}
    for f in sorted(os.listdir(directory)):
        if os.path.splitext(f)[1].lower() in audio_ext:
            playlist.add_song(f)
    refresh_playlist_box()
    if playlist.size > 0:
        current_song = playlist.get_current_song()
        root.directory = directory
        lbl_count.config(text=f"{playlist.size} songs")
        update_now_playing()
        print(f"✅ Loaded {playlist.size} lagu ke DLL")
        return True
    return False

# ─────────────────────────────────────────────
#  AUTO-PLAY NEXT  (polling ringan, 1 detik)
# ─────────────────────────────────────────────
def check_song_end():
    global current_song, paused, is_playing
    if is_playing and not pygame.mixer.music.get_busy():
        next_t = playlist.next_song()
        if next_t:
            current_song = next_t
            refresh_playlist_box()
            paused = False
            play_music()
        else:
            is_playing = False
            update_now_playing()
            print("⏹️ Playlist selesai!")
    root.after(1000, check_song_end)

# ─────────────────────────────────────────────
#  CONTROLS
# ─────────────────────────────────────────────
def load_music():
    directory = filedialog.askdirectory()
    if directory:
        if load_songs_from_directory(directory):
            save_config(directory)

def play_music():
    global current_song, paused, is_playing
    if not current_song:
        return
    if paused:
        pygame.mixer.music.unpause()
        paused = False
        is_playing = True
        update_now_playing()
        return
    try:
        pygame.mixer.music.load(os.path.join(root.directory, current_song))
        pygame.mixer.music.play()
        is_playing = True
        paused = False
        update_now_playing()
    except AttributeError:
        print("❌ Belum ada folder!")
    except Exception as e:
        print(f"❌ {e}")

def pause_music():
    global paused, is_playing
    if is_playing and pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
        paused = True
        is_playing = False
        update_now_playing()

def toggle_play():
    if is_playing:
        pause_music()
    else:
        play_music()

def stop_music():
    global paused, is_playing
    pygame.mixer.music.stop()
    paused = False
    is_playing = False
    update_now_playing()

def next_music():
    global current_song, paused
    t = playlist.next_song()
    if t:
        current_song = t
        refresh_playlist_box()
        paused = False
        play_music()
    else:
        print("⛔ Sudah lagu terakhir (node tail DLL)")

def prev_music():
    global current_song, paused
    t = playlist.prev_song()
    if t:
        current_song = t
        refresh_playlist_box()
        paused = False
        play_music()
    else:
        print("⛔ Sudah lagu pertama (node head DLL)")

def on_song_select(event):
    global current_song
    try:
        idx = songlist.curselection()[0]
        songs = playlist.get_all_songs()
        if idx < len(songs):
            playlist.set_current_song(songs[idx])
            current_song = playlist.get_current_song()
            update_now_playing()
    except IndexError:
        pass

def on_song_double(event):
    on_song_select(event)
    play_music()

# ─────────────────────────────────────────────
#  BUTTON FACTORY
# ─────────────────────────────────────────────
def make_btn(parent, text, cmd, bg=BG_SURFACE, fs=15, w=3, pad=8):
    b = tk.Button(parent, text=text, command=cmd,
                  font=("Segoe UI", fs, "bold"),
                  bg=bg, fg=TEXT_PRI,
                  activebackground=ACCENT_HOV, activeforeground=TEXT_PRI,
                  relief="flat", bd=0, cursor="hand2",
                  width=w, pady=pad,
                  highlightthickness=0)
    return b

# ─────────────────────────────────────────────
#  ══  UI LAYOUT  ══
# ─────────────────────────────────────────────

# ── TOP BAR ─────────────────────────────────
top_bar = tk.Frame(root, bg=BG_CARD, height=46)
top_bar.pack(fill="x")
top_bar.pack_propagate(False)

tk.Label(top_bar, text="🎵 MusicFlow", font=("Segoe UI", 13, "bold"),
         bg=BG_CARD, fg=ACCENT2).pack(side="left", padx=16)

lbl_count = tk.Label(top_bar, text="0 songs", font=("Segoe UI", 9),
                     bg=BG_CARD, fg=TEXT_SEC)
lbl_count.pack(side="right", padx=6)

btn_folder = tk.Button(top_bar, text="＋  Open Folder",
                       command=load_music,
                       font=("Segoe UI", 9, "bold"),
                       bg=ACCENT, fg=TEXT_PRI,
                       activebackground=ACCENT_HOV, activeforeground=TEXT_PRI,
                       relief="flat", bd=0, cursor="hand2",
                       padx=12, pady=4)
btn_folder.pack(side="right", padx=10, pady=8)

# ── CONTENT ──────────────────────────────────
content = tk.Frame(root, bg=BG_DEEP)
content.pack(fill="both", expand=True)

# LEFT PANEL (album art + info)
left = tk.Frame(content, bg=BG_DEEP, width=240)
left.pack(side="left", fill="y", padx=(14, 6), pady=14)
left.pack_propagate(False)

album_canvas = tk.Canvas(left, width=200, height=200,
                          bg=BG_CARD, highlightthickness=0)
album_canvas.pack(pady=(0, 10))
draw_album_art()

lbl_status = tk.Label(left, text="⏹  Stopped",
                       font=("Segoe UI", 9), bg=BG_DEEP, fg=TEXT_DIM)
lbl_status.pack()

lbl_title = tk.Label(left, text="Pilih lagu untuk diputar",
                      font=("Segoe UI", 11, "bold"), bg=BG_DEEP, fg=TEXT_DIM,
                      wraplength=200, justify="center")
lbl_title.pack(pady=(6, 2))

lbl_artist = tk.Label(left, text="—",
                       font=("Segoe UI", 9), bg=BG_DEEP, fg=TEXT_SEC)
lbl_artist.pack()

# RIGHT PANEL (playlist)
right = tk.Frame(content, bg=BG_DEEP)
right.pack(side="left", fill="both", expand=True, padx=(0, 14), pady=14)

tk.Label(right, text="PLAYLIST", font=("Segoe UI", 8, "bold"),
         bg=BG_DEEP, fg=TEXT_DIM).pack(anchor="w", padx=4)

list_frame = tk.Frame(right, bg=BG_CARD,
                       highlightbackground=BG_SURFACE, highlightthickness=1)
list_frame.pack(fill="both", expand=True, pady=(4, 0))

scrollbar = tk.Scrollbar(list_frame, orient="vertical",
                          bg=BG_SURFACE, troughcolor=BG_CARD, width=8)
songlist = tk.Listbox(
    list_frame,
    bg=BG_CARD, fg=TEXT_SEC,
    selectbackground=SEL_BG, selectforeground=SEL_FG,
    font=("Segoe UI", 10),
    borderwidth=0, highlightthickness=0,
    activestyle="none", relief="flat", cursor="hand2",
    yscrollcommand=scrollbar.set
)
scrollbar.config(command=songlist.yview)
scrollbar.pack(side="right", fill="y")
songlist.pack(fill="both", expand=True)

songlist.bind("<<ListboxSelect>>", on_song_select)
songlist.bind("<Double-Button-1>",  on_song_double)

# ── BOTTOM CONTROLS ──────────────────────────
bottom = tk.Frame(root, bg=BG_CARD)
bottom.pack(fill="x", side="bottom")

tk.Frame(bottom, bg=ACCENT, height=2).pack(fill="x")

ctrl_row = tk.Frame(bottom, bg=BG_CARD)
ctrl_row.pack(pady=14)

btn_prev = make_btn(ctrl_row, "⏮", prev_music, BG_SURFACE, 14, 3, 6)
btn_play = make_btn(ctrl_row, "▶", toggle_play, ACCENT,    22, 4, 8)
btn_next = make_btn(ctrl_row, "⏭", next_music, BG_SURFACE, 14, 3, 6)
btn_stop = make_btn(ctrl_row, "⏹", stop_music, DANGER,     14, 3, 6)

btn_prev.pack(side="left", padx=6)
btn_play.pack(side="left", padx=6)
btn_next.pack(side="left", padx=6)
btn_stop.pack(side="left", padx=6)

# ─────────────────────────────────────────────
#  STARTUP
# ─────────────────────────────────────────────
last_folder = load_config()
if last_folder and os.path.exists(last_folder):
    load_songs_from_directory(last_folder)
    print(f"📂 Auto-load: {last_folder}")
else:
    print("📂 Pilih folder via '＋ Open Folder'.")

root.after(1000, check_song_end)

root.mainloop()
