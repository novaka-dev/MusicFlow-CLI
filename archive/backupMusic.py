import random
import pygame
import os
import sys
import time

# ---------- Cross-platform non-blocking input ----------
def check_key():
    """Return karakter jika ada input, else None (non-blocking)."""
    if sys.platform == 'win32':
        import msvcrt
        if msvcrt.kbhit():
            return msvcrt.getch().decode('utf-8', errors='ignore').lower()
    else:
        import select
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1).lower()
    return None

# ---------- Double Linked List Node ----------
class Node:
    def __init__(self, title, file_path):
        self.title = title          # buat display
        self.file_path = file_path  # path fisik file
        self.prev = None
        self.next = None

class DoubleLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def append(self, title, file_path):
        new_node = Node(title, file_path)
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
        self.size += 1

    def remove_at(self, index):  # index 0-based
        if index < 0 or index >= self.size:
            return None
        current = self.head
        for i in range(index):
            current = current.next
        if current.prev:
            current.prev.next = current.next
        else:
            self.head = current.next
        if current.next:
            current.next.prev = current.prev
        else:
            self.tail = current.prev
        self.size -= 1
        return current

    def get_node_at(self, index):
        if index < 0 or index >= self.size:
            return None
        current = self.head
        for i in range(index):
            current = current.next
        return current

    def get_all_nodes(self):
        nodes = []
        current = self.head
        while current:
            nodes.append(current)
            current = current.next
        return nodes

    def get_all_titles(self):
        return [node.title for node in self.get_all_nodes()]

    def get_next_node(self, node):
        if node.next:
            return node.next
        else:
            return self.head  # sirkular

    def get_prev_node(self, node):
        if node.prev:
            return node.prev
        else:
            return self.tail  # sirkular

# ---------- Music Player State ----------
class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.playlist = DoubleLinkedList()
        self.current_node = None
        self.repeat_one = False
        self.mode = "normal"
        self.shuffle_order = []   # list of Node objects
        self.shuffle_index = -1
        self.is_playing = False

    def rebuild_shuffle_order(self):
        all_nodes = self.playlist.get_all_nodes()
        random.shuffle(all_nodes)
        self.shuffle_order = all_nodes
        if self.current_node and self.current_node in self.shuffle_order:
            self.shuffle_index = self.shuffle_order.index(self.current_node)
        elif self.shuffle_order:
            self.shuffle_index = 0
            self.current_node = self.shuffle_order[0]
        else:
            self.shuffle_index = -1
            self.current_node = None

    def next_song(self, manual=True):
        """manual=False untuk next otomatis dari lagu selesai."""
        if self.playlist.size == 0:
            return None
        if manual:
            self.repeat_one = False
        if self.repeat_one:
            return self.current_node
        if self.mode == "normal":
            if self.current_node is None:
                self.current_node = self.playlist.head
            else:
                self.current_node = self.playlist.get_next_node(self.current_node)
            return self.current_node
        else:  # shuffle
            if self.shuffle_index == -1 or not self.shuffle_order:
                self.rebuild_shuffle_order()
            self.shuffle_index += 1
            if self.shuffle_index >= len(self.shuffle_order):
                self.rebuild_shuffle_order()
                self.shuffle_index = 0
            self.current_node = self.shuffle_order[self.shuffle_index]
            return self.current_node

    def prev_song(self):
        if self.playlist.size == 0:
            return None
        self.repeat_one = False
        if self.mode == "normal":
            if self.current_node is None:
                self.current_node = self.playlist.tail
            else:
                self.current_node = self.playlist.get_prev_node(self.current_node)
            return self.current_node
        else:
            if self.shuffle_index == -1 or not self.shuffle_order:
                self.rebuild_shuffle_order()
            self.shuffle_index -= 1
            if self.shuffle_index < 0:
                self.shuffle_index = len(self.shuffle_order) - 1
            self.current_node = self.shuffle_order[self.shuffle_index]
            return self.current_node

    def add_song(self, title, file_path):
        self.playlist.append(title, file_path)
        self.mode = "normal"
        self.shuffle_order = []
        self.shuffle_index = -1
        if self.playlist.size == 1 and self.current_node is None:
            self.current_node = self.playlist.head

    def remove_song(self, index_1based):
        idx = index_1based - 1
        if idx < 0 or idx >= self.playlist.size:
            return False
        node_to_remove = self.playlist.get_node_at(idx)
        if node_to_remove == self.current_node:
            pygame.mixer.music.stop()
            next_node = self.playlist.get_next_node(node_to_remove) if self.playlist.size > 1 else None
            self.playlist.remove_at(idx)
            if next_node:
                self.current_node = next_node
            else:
                self.current_node = self.playlist.head if self.playlist.size > 0 else None
            if self.current_node and self.is_playing:
                self.play_current_song()
        else:
            self.playlist.remove_at(idx)
        self.mode = "normal"
        self.shuffle_order = []
        self.shuffle_index = -1
        return True

    def play_current_song(self):
        if self.current_node and os.path.exists(self.current_node.file_path):
            pygame.mixer.music.load(self.current_node.file_path)
            pygame.mixer.music.play()
            self.is_playing = True
            return True
        else:
            print(f"❌ File tidak ditemukan: {self.current_node.file_path if self.current_node else 'None'}")
            return False

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False

    def pause(self):
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False

    def unpause(self):
        if not self.is_playing and self.current_node:
            pygame.mixer.music.unpause()
            self.is_playing = True

    def toggle_pause(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.is_playing = False
        else:
            pygame.mixer.music.unpause()
            self.is_playing = True

    def display_playlist(self):
        if self.playlist.size == 0:
            print("📭 Playlist kosong.")
            return
        titles = self.playlist.get_all_titles()
        for i, title in enumerate(titles, start=1):
            marker = ""
            if self.current_node and self.current_node.title == title:
                if self.repeat_one:
                    marker = " 🔁 (repeat)"
                elif pygame.mixer.music.get_busy() and self.is_playing:
                    marker = " 🔊"
                else:
                    marker = " ▶️"
            print(f"{i}. {title}{marker}")

# ---------- Playback Mode (real dengan pygame) ----------
def playback_mode(player):
    if player.playlist.size == 0:
        print("⚠️ Playlist kosong, gak bisa muter.")
        return
    if player.current_node is None:
        player.current_node = player.playlist.head
        if player.mode == "shuffle":
            player.rebuild_shuffle_order()
            player.current_node = player.shuffle_order[0] if player.shuffle_order else None
    if not player.play_current_song():
        return

    print("\n🎧 Playback dimulai. Tekan H (help) buat liat perintah.")
    last_busy = True
    while True:
        # Cek apakah lagu selesai (get_busy False dan is_playing True)
        busy = pygame.mixer.music.get_busy()
        if not busy and player.is_playing:
            # Lagu selesai alami -> next otomatis
            next_node = player.next_song(manual=False)
            if next_node:
                player.play_current_song()
                # tampilkan info lagu baru
                print(f"\n⏩ Otomatis next ke: {player.current_node.title}")
                continue
            else:
                print("\n⏹️ Playlist habis. Stop playback.")
                player.stop()
                break

        # Non-blocking input
        cmd = check_key()
        if cmd is not None:
            if cmd == 'h':
                print("\n=== PERINTAH PLAYBACK ===")
                print("  [SPASI]  Pause/Resume")
                print("  [N]      Next lagu")
                print("  [P]      Previous lagu")
                print("  [R]      Toggle repeat one")
                print("  [S]      Stop & kembali ke menu")
                print("  [Q]      Quit playback (tanpa stop musik)")
                print("==========================")
            elif cmd == ' ':
                player.toggle_pause()
                state = "Pause" if not player.is_playing else "Lanjut"
                print(f"⏸️ {state}")
            elif cmd == 'n':
                next_node = player.next_song(manual=True)
                if next_node:
                    player.play_current_song()
                    print(f"\n⏩ Next: {player.current_node.title}")
                else:
                    print("❌ Gagal next.")
            elif cmd == 'p':
                prev_node = player.prev_song()
                if prev_node:
                    player.play_current_song()
                    print(f"\n⏪ Previous: {player.current_node.title}")
                else:
                    print("❌ Gagal previous.")
            elif cmd == 'r':
                player.repeat_one = not player.repeat_one
                print(f"🔁 Repeat one {'AKTIF' if player.repeat_one else 'NONAKTIF'}")
            elif cmd == 's':
                player.stop()
                print("⏹️ Playback dihentikan.")
                break
            elif cmd == 'q':
                print("🔙 Kembali ke menu (musik tetap jalan di background, pakai 'Stop' nanti).")
                break
            else:
                # ignore
                pass
        time.sleep(0.1)  # biar gak boros CPU

# ---------- Menu Utama ----------
def main():
    player = MusicPlayer()

    # Contoh menambah lagu (ganti dengan file yang lo punya)
    # Biar gak error, kita kasih dummy dulu
    player.add_song("[Contoh] Lagu 1", "lagu1.mp3")
    player.add_song("[Contoh] Lagu 2", "lagu2.mp3")
    player.add_song("[Contoh] Lagu 3", "lagu3.mp3")

    while True:
        print("\n" + "="*50)
        print("🎧 MUSIC PLAYER TERMINAL (Double Linked List + Pygame Mixer)")
        print("="*50)
        player.display_playlist()
        print("\nMENU:")
        print("  1. Tampilkan daftar lagu")
        print("  2. Play lagu tertentu (pilih nomor)")
        print("  3. Stop semua playback")
        print("  4. Upload lagu dari file")
        print("  5. Hapus lagu")
        print("  6. Aktifkan mode SHUFFLE & play (infinite loop)")
        print("  7. Next lagu")
        print("  8. Previous lagu")
        print("  9. Toggle repeat one untuk lagu saat ini")
        print("  0. Keluar program")
        choice = input("Pilih menu: ").strip()

        if choice == '1':
            continue
        elif choice == '2':
            if player.playlist.size == 0:
                print("Playlist kosong.")
                continue
            try:
                idx = int(input("Nomor lagu: "))
                if idx < 1 or idx > player.playlist.size:
                    print("Nomor invalid.")
                    continue
                node = player.playlist.get_node_at(idx-1)
                rep = input("Ulang lagu ini terus? (y/n): ").strip().lower()
                player.repeat_one = (rep == 'y')
                player.current_node = node
                if player.mode == "shuffle":
                    player.rebuild_shuffle_order()
                    if player.current_node in player.shuffle_order:
                        player.shuffle_index = player.shuffle_order.index(player.current_node)
                print(f"Memutar: {node.title}")
                playback_mode(player)
            except ValueError:
                print("Input angka.")
        elif choice == '3':
            player.stop()
            print("Playback distop.")
        elif choice == '4':
            path = input("Masukkan PATH file lagu (mp3/wav/ogg): ").strip()
            if not os.path.exists(path):
                print("❌ File tidak ditemukan.")
                continue
            title = input("Judul lagu (kosong = nama file): ").strip()
            if not title:
                title = os.path.basename(path)
            player.add_song(title, path)
            print(f"✅ Lagu '{title}' berhasil di-upload & ditambah ke playlist.")
        elif choice == '5':
            if player.playlist.size == 0:
                print("Playlist kosong.")
                continue
            try:
                idx = int(input("Nomor lagu yang mau dihapus: "))
                if player.remove_song(idx):
                    print("Lagu berhasil dihapus.")
                else:
                    print("Nomor invalid.")
            except ValueError:
                print("Input angka.")
        elif choice == '6':
            if player.playlist.size == 0:
                print("Playlist kosong.")
                continue
            player.mode = "shuffle"
            player.rebuild_shuffle_order()
            player.current_node = player.shuffle_order[0] if player.shuffle_order else None
            player.repeat_one = False
            print("🔀 Mode SHUFFLE (infinite loop) diaktifkan. Memulai playback...")
            playback_mode(player)
        elif choice == '7':
            if player.playlist.size == 0:
                print("Playlist kosong.")
                continue
            next_node = player.next_song(manual=True)
            if next_node:
                player.play_current_song()
                print(f"⏩ Langsung next ke: {next_node.title}")
                # Optional: tanya mau langsung masuk playback?
                if input("Masuk mode playback? (y/n): ").lower() == 'y':
                    playback_mode(player)
            else:
                print("Gagal next.")
        elif choice == '8':
            if player.playlist.size == 0:
                print("Playlist kosong.")
                continue
            prev_node = player.prev_song()
            if prev_node:
                player.play_current_song()
                print(f"⏪ Langsung previous ke: {prev_node.title}")
                if input("Masuk mode playback? (y/n): ").lower() == 'y':
                    playback_mode(player)
            else:
                print("Gagal previous.")
        elif choice == '9':
            player.repeat_one = not player.repeat_one
            state = "AKTIF" if player.repeat_one else "NONAKTIF"
            print(f"🔁 Repeat one {state}.")
            if player.current_node:
                print(f"Lagu: {player.current_node.title}")
            else:
                print("Belum ada lagu dipilih.")
        elif choice == '0':
            pygame.mixer.quit()
            print("Makasih udah pake. Dadah bro! 🎵")
            break
        else:
            print("Pilihan gak ada. Coba 0-9.")

if __name__ == "__main__":
    main()
