import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkhtmlview import HTMLLabel
import markdown2
import json, os
from datetime import datetime

DATA_FILE = os.path.join(os.path.expanduser("~"), ".modern_notlar.json")


class ModernNotesApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Not Defteri 📝")
        self.geometry("950x600")
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.notes = {}
        self.current_id = None
        self.note_buttons = {}
        self.export_buttons_visible = False

        self.create_ui()
        self.load_notes()
        self.bind("<Delete>", lambda e: self.delete_note())

    # ---------------- UI ----------------
    def create_ui(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Sol panel
        self.left_panel = ctk.CTkFrame(self.main_frame, width=250)
        self.left_panel.pack(side="left", fill="y", padx=(0, 10), pady=5)
        self.left_panel.pack_propagate(False)

        self.search_entry = ctk.CTkEntry(self.left_panel, placeholder_text="Ara...")
        self.search_entry.pack(fill="x", padx=10, pady=(10, 5))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_list())

        self.note_list = ctk.CTkScrollableFrame(self.left_panel, label_text="Notlar")
        self.note_list.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self.delete_button = ctk.CTkButton(
            self.left_panel, text="🗑️ Seçili Notu Sil", command=self.delete_note
        )
        self.delete_button.pack(fill="x", padx=10, pady=(0, 10))

        # Sağ panel
        self.right_panel = ctk.CTkFrame(self.main_frame)
        self.right_panel.pack(side="left", fill="both", expand=True, pady=5)

        # Üst çubuk: başlık + sağda içe aktar ve dışa aktar
        self.title_bar = ctk.CTkFrame(self.right_panel)
        self.title_bar.pack(fill="x", padx=10, pady=(10, 5))

        self.title_entry = ctk.CTkEntry(
            self.title_bar, placeholder_text="Not Başlığı", height=40
        )
        self.title_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.title_entry.bind("<KeyRelease>", lambda e: self.mark_dirty())

        # 📤 Dışa Aktar butonu
        self.export_main_button = ctk.CTkButton(
            self.title_bar,
            text="📤 Dışa Aktar",
            width=130,
            command=self.toggle_export_buttons,
        )
        self.export_main_button.pack(side="right", padx=(0, 2))  # 2px boşluk sola

        # 📂 İçe Aktar butonu
        self.import_button = ctk.CTkButton(
            self.title_bar, text="📂 İçe Aktar", width=120, command=self.import_json
        )
        self.import_button.pack(side="right", padx=(2, 10))  # 2px boşluk sağa

        # Dışa aktar alt menüsü (başta gizli)
        self.export_frame = ctk.CTkFrame(self.right_panel)
        self.export_frame.pack(fill="x", padx=10)
        self.export_frame.pack_forget()

        self.export_selected_button = ctk.CTkButton(
            self.export_frame,
            text="🗂️ Seçili Notu Kaydet (JSON)",
            command=self.export_selected_json,
        )
        self.export_selected_button.pack(side="left", padx=5, pady=5)

        self.export_all_button = ctk.CTkButton(
            self.export_frame,
            text="📁 Tüm Notları Kaydet (JSON)",
            command=self.export_all_json,
        )
        self.export_all_button.pack(side="left", padx=5, pady=5)

        # Metin alanı
        self.textbox = ctk.CTkTextbox(self.right_panel, wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        self.textbox.bind("<KeyRelease>", lambda e: self.mark_dirty())

        # Alt bar
        self.bottom_bar = ctk.CTkFrame(self.right_panel)
        self.bottom_bar.pack(fill="x", padx=10, pady=(0, 10))

        self.new_button = ctk.CTkButton(
            self.bottom_bar, text="➕ Yeni Not", command=self.new_note
        )
        self.new_button.pack(side="left", padx=5)

        self.save_button = ctk.CTkButton(
            self.bottom_bar, text="💾 Kaydet", command=self.save_current
        )
        self.save_button.pack(side="left", padx=5)

        self.copy_button = ctk.CTkButton(
            self.bottom_bar, text="📄 Dosyayı Kopyala", command=self.save_as_copy
        )
        self.copy_button.pack(side="left", padx=5)

        self.preview_button = ctk.CTkButton(
            self.bottom_bar, text="👁️ Notu Önizle", command=self.preview_markdown
        )
        self.preview_button.pack(side="right", padx=5)

    # ---------------- Veri ----------------
    def load_notes(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.notes = json.load(f)
            except:
                self.notes = {}
        else:
            self.notes = {}
        self.refresh_list()

    def save_notes(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=2)

    def refresh_list(self):
        for widget in self.note_list.winfo_children():
            widget.destroy()
        self.note_buttons.clear()

        query = self.search_entry.get().lower().strip()
        sorted_notes = sorted(
            self.notes.items(), key=lambda x: x[1].get("updated", ""), reverse=True
        )

        for nid, note in sorted_notes:
            if query and query not in note["title"].lower():
                continue

            btn = ctk.CTkButton(
                self.note_list,
                text=note["title"],
                corner_radius=10,
                fg_color=("#3a7ebf" if nid == self.current_id else "transparent"),
                hover_color="#1f538d",
                anchor="w",
                command=lambda n=nid: self.load_note_to_editor(n),
            )
            btn.pack(fill="x", pady=3, padx=5)
            self.note_buttons[nid] = btn

    def highlight_selected(self):
        for nid, btn in self.note_buttons.items():
            btn.configure(fg_color="#3a7ebf" if nid == self.current_id else "transparent")

    def load_note_to_editor(self, nid):
        note = self.notes.get(nid)
        if not note:
            return
        self.current_id = nid
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, note["title"])
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", note["body"])
        self.highlight_selected()

    def mark_dirty(self):
        if self.current_id:
            n = self.notes.get(self.current_id)
            if n:
                n["title"] = self.title_entry.get().strip() or "Başlıksız"
                n["body"] = self.textbox.get("1.0", "end").rstrip()
                n["updated"] = datetime.now().isoformat()
                self.notes[self.current_id] = n
        self.save_notes()
        self.refresh_list()
        self.highlight_selected()

    # ---------------- CRUD ----------------
    def new_note(self):
        nid = datetime.now().isoformat()
        self.notes[nid] = {"title": "Yeni Not", "body": "", "updated": nid}
        self.current_id = nid
        self.load_note_to_editor(nid)
        self.save_notes()
        self.refresh_list()

    def save_current(self):
        if not self.current_id:
            self.new_note()
        else:
            n = self.notes[self.current_id]
            n["title"] = self.title_entry.get().strip() or "Başlıksız"
            n["body"] = self.textbox.get("1.0", "end").rstrip()
            n["updated"] = datetime.now().isoformat()
            self.notes[self.current_id] = n
        self.save_notes()
        self.refresh_list()
        self.highlight_selected()

    def save_as_copy(self):
        if not self.current_id:
            messagebox.showinfo("Uyarı", "Kaydedilecek bir not yok.")
            return
        old_note = self.notes[self.current_id]
        new_id = datetime.now().isoformat()
        new_title = old_note["title"] + " (Kopya)"
        self.notes[new_id] = {
            "title": new_title,
            "body": old_note["body"],
            "updated": datetime.now().isoformat(),
        }
        self.save_notes()
        self.refresh_list()
        self.load_note_to_editor(new_id)
        messagebox.showinfo("Kopyalandı", f"'{old_note['title']}' adlı not başarıyla kopyalandı.")

    def delete_note(self):
        if not self.current_id:
            messagebox.showinfo("Uyarı", "Silinecek bir not seçmedin.")
            return
        sure = messagebox.askyesno("Sil", "Bu notu silmek istediğine emin misin?")
        if not sure:
            return
        try:
            del self.notes[self.current_id]
            self.current_id = None
            self.textbox.delete("1.0", "end")
            self.title_entry.delete("1.0", "end")
            self.save_notes()
            self.refresh_list()
        except:
            messagebox.showerror("Hata", "Silme sırasında hata oluştu.")

    # ---------------- Dışa Aktar ----------------
    def toggle_export_buttons(self):
        if self.export_buttons_visible:
            self.export_frame.pack_forget()
        else:
            self.export_frame.pack(fill="x", padx=10)
        self.export_buttons_visible = not self.export_buttons_visible

    def export_selected_json(self):
        if not self.current_id:
            messagebox.showinfo("Uyarı", "Kaydedilecek bir not yok.")
            return
        note = self.notes[self.current_id]
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON dosyaları", "*.json")],
            title="Seçili Notu Kaydet",
            initialfile=f"{note['title']}.json",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(note, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Başarılı", f"Not kaydedildi:\n{path}")

    def export_all_json(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON dosyaları", "*.json")],
            title="Tüm Notları Kaydet",
            initialfile="tum_notlar.json",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Başarılı", f"Tüm notlar kaydedildi:\n{path}")

    # ---------------- İçe Aktar ----------------
    def import_json(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON dosyaları", "*.json")],
            title="JSON Dosyası Seç",
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Tek not mu tüm notlar mı?
            if "title" in data and "body" in data:
                new_id = datetime.now().isoformat()
                data["updated"] = datetime.now().isoformat()
                self.notes[new_id] = data
                messagebox.showinfo("İçe Aktarıldı", f"'{data['title']}' notu eklendi.")
            else:
                count = 0
                for key, note in data.items():
                    new_id = datetime.now().isoformat() + str(count)
                    note["updated"] = datetime.now().isoformat()
                    self.notes[new_id] = note
                    count += 1
                messagebox.showinfo("İçe Aktarıldı", f"{count} not içe aktarıldı.")

            self.save_notes()
            self.refresh_list()
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya okunamadı:\n{e}")

    # ---------------- Markdown ----------------
    def preview_markdown(self):
        if not self.current_id:
            messagebox.showinfo("Uyarı", "Önizlenecek bir not yok.")
            return

        content = self.textbox.get("1.0", "end").rstrip()
        safe_content = (
            content.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
            .replace("\n", "<br>")
        )
        html_content = markdown2.markdown(safe_content, extras=["fenced-code-blocks"])

        preview_window = ctk.CTkToplevel(self)
        preview_window.title("Notu Önizle 👁️")
        preview_window.geometry("700x500")

        frame = ctk.CTkFrame(preview_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        html_label = HTMLLabel(frame, html=html_content, background="white")
        html_label.pack(fill="both", expand=True)


# ---------------- Çalıştır ----------------
if __name__ == "__main__":
    app = ModernNotesApp()
    app.mainloop()
