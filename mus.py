from tkinter import filedialog
from tkinter import *
import pygame
import os
import json

root = Tk()
root.title("Music Player")
root.geometry("600x440")

pygame.mixer.init()

menubar = Menu(root)
root.config(menu=menubar)

# ============ DOUBLE LINKED LIST IMPLEMENTASI ============
class SongNode:
    """Node untuk double linked list"""
    def __init__(self, song_title):
        self.song_title = song_title  # Nama lagu
        self.prev = None  # Pointer ke lagu sebelumnya
        self.next = None  # Pointer ke lagu berikutnya

class Playlist:
    """Double Linked List buat manajemen playlist"""
    def __init__(self):
        self.head = None  # Node pertama (lagu pertama)
        self.tail = None  # Node terakhir (lagu terakhir)
        self.current = None  # Node yang sedang diputar
        self.size = 0  # Jumlah lagu
    
    def add_song(self, song_title):
        """Tambah lagu ke akhir playlist"""
        new_node = SongNode(song_title)
        
        if self.head is None:
            # Playlist masih kosong
            self.head = new_node
            self.tail = new_node
            self.current = new_node
        else:
            # Tambah di akhir
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
        
        self.size += 1
    
    def clear(self):
        """Hapus semua lagu dari playlist"""
        self.head = None
        self.tail = None
        self.current = None
        self.size = 0
    
    def get_current_song(self):
        """Dapatkan lagu yang sedang diputar"""
        if self.current:
            return self.current.song_title
        return ""
    
    def set_current_song(self, song_title):
        """Set lagu tertentu sebagai lagu yang sedang diputar (berdasarkan judul)"""
        current_node = self.head
        while current_node:
            if current_node.song_title == song_title:
                self.current = current_node
                return True
            current_node = current_node.next
        return False
    
    def next_song(self):
        """Pindah ke lagu berikutnya, return judul lagu"""
        if self.current and self.current.next:
            self.current = self.current.next
            return self.current.song_title
        return None
    
    def prev_song(self):
        """Pindah ke lagu sebelumnya, return judul lagu"""
        if self.current and self.current.prev:
            self.current = self.current.prev
            return self.current.song_title
        return None
    
    def get_all_songs(self):
        """Return list semua judul lagu (buat ditampilkan di listbox)"""
        songs_list = []
        current_node = self.head
        while current_node:
            songs_list.append(current_node.song_title)
            current_node = current_node.next
        return songs_list
    
    def get_current_index(self):
        """Dapatkan index lagu yang sedang diputar (buat selection di listbox)"""
        index = 0
        current_node = self.head
        while current_node:
            if current_node == self.current:
                return index
            current_node = current_node.next
            index += 1
        return -1

# Inisialisasi playlist pake double linked list
playlist = Playlist()
current_song = ""
paused = False
CONFIG_FILE = "music_player_config.json"

def save_config(directory):
    """Nyimpen path folder ke file config"""
    config = {"last_directory": directory}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def load_config():
    """Load path folder dari file config"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config.get("last_directory", "")
    return ""

def load_songs_from_directory(directory):
    """Load lagu dari folder dan update playlist (double linked list)"""
    global current_song
    
    if not directory or not os.path.exists(directory):
        return False
    
    # Kosongkan playlist dulu
    playlist.clear()
    songlist.delete(0, END)
    
    # Support berbagai format audio bro
    audio_extensions = [".mp3", ".wav", ".ogg", ".m4a", ".flac"]
    
    # Tambahin lagu ke double linked list
    for song in os.listdir(directory):
        name, ext = os.path.splitext(song)
        if ext.lower() in audio_extensions:
            playlist.add_song(song)
    
    # Tampilin di listbox
    all_songs = playlist.get_all_songs()
    for song in all_songs:
        songlist.insert("end", song)
    
    if playlist.size > 0:
        songlist.selection_set(0)
        current_song = playlist.get_current_song()
        root.directory = directory
        print(f"✅ Load {playlist.size} lagu pake Double Linked List!")
        print(f"🎵 Lagu pertama: {current_song}")
        return True
    return False

def on_song_select(event):
    """Fungsi ini dipanggil ketika user klik lagu di listbox"""
    global current_song
    try:
        selected_index = songlist.curselection()[0]
        all_songs = playlist.get_all_songs()
        if selected_index < len(all_songs):
            selected_song = all_songs[selected_index]
            # Set current node di double linked list
            playlist.set_current_song(selected_song)
            current_song = playlist.get_current_song()
            print(f"🎵 Lagu dipilih: {current_song}")
            print(f"📊 Current index: {playlist.get_current_index()}")
    except IndexError:
        pass

def load_music():
    global current_song
    directory = filedialog.askdirectory()
    
    if directory:
        if load_songs_from_directory(directory):
            save_config(directory)

def play_music():
    global current_song, paused

    if not current_song:
        print("❌ Gak ada lagu yang dipilih bro!")
        return
    
    # Kalo paused, lanjutin pause
    if paused:
        pygame.mixer.music.unpause()
        paused = False
        return
        
    # Kalo gak paused, play lagu yang lagi dipilih
    try:
        pygame.mixer.music.load(os.path.join(root.directory, current_song))
        pygame.mixer.music.play()
        print(f"🎶 Sedang memutar: {current_song}")
        print(f"📍 Posisi di playlist: {playlist.get_current_index() + 1}/{playlist.size}")
    except Exception as e:
        print(f"❌ Error pas muter lagu: {e}")

def pause_music():
    global paused
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
        paused = True
        print("⏸️ Lagu di-pause")

def next_music():
    global current_song, paused

    try:
        # Pake double linked list buat next
        next_song_title = playlist.next_song()
        
        if next_song_title:
            current_song = next_song_title
            
            # Update selection di listbox
            current_index = playlist.get_current_index()
            songlist.selection_clear(0, END)
            songlist.selection_set(current_index)
            songlist.see(current_index)  # Scroll ke lagu yang diputar
            
            # Reset paused state dan play
            paused = False
            play_music()
            print(f"⏭️ Next lagu: {current_song}")
        else:
            print("⛔ Udah lagu terakhir bro!")
    except Exception as e:
        print(f"❌ Error pas next lagu: {e}")

def prev_music():
    global current_song, paused
    try:
        # Pake double linked list buat prev
        prev_song_title = playlist.prev_song()
        
        if prev_song_title:
            current_song = prev_song_title
            
            # Update selection di listbox
            current_index = playlist.get_current_index()
            songlist.selection_clear(0, END)
            songlist.selection_set(current_index)
            songlist.see(current_index)  # Scroll ke lagu yang diputar
            
            # Reset paused state dan play
            paused = False
            play_music()
            print(f"⏮️ Prev lagu: {current_song}")
        else:
            print("⛔ Udah lagu pertama bro!")
    except Exception as e:
        print(f"❌ Error pas prev lagu: {e}")

# Menu
organise_menu = Menu(menubar, tearoff=False)
organise_menu.add_command(label="Pilih Folder", command=load_music)
menubar.add_cascade(label="Menu", menu=organise_menu)

# Listbox
songlist = Listbox(root, bg="black", fg="white", width=100, height=15)
songlist.pack()

# Binding event klik listbox
songlist.bind('<<ListboxSelect>>', on_song_select)

# Load gambar (pastikan file gambarnya ada)
try:
    play_btn_image = PhotoImage(file="play.png")
    pause_btn_image = PhotoImage(file="pause.png")
    next_btn_image = PhotoImage(file="next.png")
    prev_btn_image = PhotoImage(file="prev.png")
    use_images = True
except:
    print("⚠️ Warning: File gambar button gak ditemuin, pake teks aja bro")
    use_images = False

control_frame = Frame(root)
control_frame.pack() 

if use_images:
    play_btn = Button(control_frame, image=play_btn_image, borderwidth=0, command=play_music)
    pause_btn = Button(control_frame, image=pause_btn_image, borderwidth=0, command=pause_music)
    next_btn = Button(control_frame, image=next_btn_image, borderwidth=0, command=next_music)
    prev_btn = Button(control_frame, image=prev_btn_image, borderwidth=0, command=prev_music)
else:
    # Fallback pake teks
    play_btn = Button(control_frame, text="Play", command=play_music, width=10)
    pause_btn = Button(control_frame, text="Pause", command=pause_music, width=10)
    next_btn = Button(control_frame, text="Next", command=next_music, width=10)
    prev_btn = Button(control_frame, text="Prev", command=prev_music, width=10)

play_btn.grid(row=0, column=2, padx=7, pady=10)
pause_btn.grid(row=0, column=1, padx=7, pady=10)
next_btn.grid(row=0, column=3, padx=7, pady=10)
prev_btn.grid(row=0, column=0, padx=7, pady=10)

# Auto load folder terakhir
last_folder = load_config()
if last_folder and os.path.exists(last_folder):
    load_songs_from_directory(last_folder)
    print(f"📂 Auto-load folder: {last_folder}")
else:
    print("📂 Belum ada folder tersimpan, silakan pilih folder lewat menu")

root.mainloop()