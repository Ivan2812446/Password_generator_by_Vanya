import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import random
import string
import json
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import pyperclip

class PasswordManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Password Vault")
        self.root.geometry("800x700")
        self.root.configure(bg='#2c3e50')
        
        # Устанавливаем современную тему
        self.set_modern_theme()
        
        self.language = 'english'
        self.master_password = None
        self.fernet = None
        self.data_file = 'passwords.vault'
        
        self.translatable_widgets = {}
        self.language_buttons = {}
        self.vault_widgets = []  # Для хранения виджетов хранилища
        
        self.setup_ui()
        self.check_first_run()
        
    def set_modern_theme(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Настройка цветовой схемы с гладкими гранями
        style.configure('TFrame', background='#34495e')
        style.configure('TLabel', background='#34495e', foreground='#ecf0f1', 
                       font=('Segoe UI', 10))
        style.configure('TButton', background='#3498db', foreground='white', 
                       font=('Segoe UI', 10, 'normal'), borderwidth=0,
                       focuscolor='none', relief='flat')
        style.map('TButton', 
                 background=[('active', '#2980b9'), ('pressed', '#21618c')])
        
        style.configure('Language.TButton', background='#2c3e50', foreground='#bdc3c7',
                       font=('Segoe UI', 10, 'normal'))
        style.map('Language.TButton',
                 background=[('active', '#34495e'), ('selected', '#3498db')],
                 foreground=[('selected', 'white')])
        
        style.configure('Selected.TButton', background='#3498db', foreground='white')
        style.map('Selected.TButton',
                 background=[('active', '#2980b9')])
        
        style.configure('Accent.TButton', background='#e74c3c', foreground='white')
        style.map('Accent.TButton', background=[('active', '#c0392b')])
        
        style.configure('Header.TLabel', font=('Segoe UI', 18, 'bold'), 
                       foreground='#3498db', background='#34495e')
        style.configure('TCheckbutton', background='#34495e', foreground='#ecf0f1')
        style.configure('TEntry', fieldbackground='#ecf0f1', borderwidth=1,
                       relief='flat', font=('Segoe UI', 10))
        style.configure('TSpinbox', fieldbackground='#ecf0f1')
        style.configure('TNotebook', background='#34495e', borderwidth=0)
        style.configure('TNotebook.Tab', background='#2c3e50', foreground='#bdc3c7',
                       padding=[15, 5], font=('Segoe UI', 10, 'normal'))
        style.map('TNotebook.Tab', 
                 background=[('selected', '#3498db')], 
                 foreground=[('selected', 'white')])
        
        style.configure('Search.TEntry', font=('Segoe UI', 10))
        
        # Стиль для темного фона хранилища
        style.configure('Vault.TFrame', background='#2c3e50')
        style.configure('Vault.TLabel', background='#2c3e50', foreground='#ecf0f1')
        
    def check_first_run(self):
        """Проверяет первый запуск и предлагает установить мастер-пароль"""
        if not os.path.exists(self.data_file):
            self.show_first_run_dialog()
            
    def show_first_run_dialog(self):
        """Диалог первого запуска"""
        dialog = tk.Toplevel(self.root)
        dialog.title("First Run / Первый запуск")
        dialog.geometry("500x300")
        dialog.configure(bg='#34495e')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Центрируем диалог
        dialog.update_idletasks()
        x = (self.root.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        ttk.Label(dialog, text="🔐 Welcome to Password Vault\nДобро пожаловать в Password Vault", 
                 style='Header.TLabel', justify='center').pack(pady=20)
        
        ttk.Label(dialog, text="Please set a master password to secure your vault\n"
                 "Пожалуйста, установите мастер-пароль для защиты хранилища", 
                 justify='center').pack(pady=10)
        
        ttk.Label(dialog, text="Master Password / Мастер-пароль:").pack(pady=5)
        master_var = tk.StringVar()
        master_entry = ttk.Entry(dialog, textvariable=master_var, show='•', font=('Segoe UI', 12))
        master_entry.pack(pady=5, padx=50, fill='x')
        
        ttk.Label(dialog, text="Confirm Master Password / Подтвердите мастер-пароль:").pack(pady=5)
        confirm_var = tk.StringVar()
        confirm_entry = ttk.Entry(dialog, textvariable=confirm_var, show='•', font=('Segoe UI', 12))
        confirm_entry.pack(pady=5, padx=50, fill='x')
        
        def set_master_password():
            if master_var.get() != confirm_var.get():
                messagebox.showerror("Error / Ошибка", 
                                   "Passwords don't match / Пароли не совпадают")
                return
            if len(master_var.get()) < 4:
                messagebox.showerror("Error / Ошибка", 
                                   "Password too short / Пароль слишком короткий")
                return
                
            self.master_var.set(master_var.get())
            self.unlock_vault(initial_setup=True)
            dialog.destroy()
            
        ttk.Button(dialog, text="Set Master Password / Установить мастер-пароль", 
                  command=set_master_password, style='Accent.TButton').pack(pady=20)
        
        master_entry.focus()
        
    def setup_ui(self):
        # Header
        header_frame = ttk.Frame(self.root, style='TFrame')
        header_frame.pack(fill='x', pady=20)
        
        title_label = ttk.Label(header_frame, text="🔐 Password Vault", style='Header.TLabel')
        title_label.pack()
        self.translatable_widgets[title_label] = ('text', "🔐 Password Vault", "🔐 Хранилище Паролей")
        
        # Control buttons frame
        control_frame = ttk.Frame(self.root, style='TFrame')
        control_frame.pack(fill='x', pady=10)
        
        lang_frame = ttk.Frame(control_frame, style='TFrame')
        lang_frame.pack(side='left', padx=20)
        
        # Кнопки языка с индикацией выбора
        en_btn = ttk.Button(lang_frame, text="EN", 
                           command=lambda: self.set_language('english'),
                           style='Language.TButton')
        en_btn.pack(side='left', padx=2)
        self.language_buttons['english'] = en_btn
        
        ru_btn = ttk.Button(lang_frame, text="RU", 
                           command=lambda: self.set_language('russian'),
                           style='Language.TButton')
        ru_btn.pack(side='left', padx=2)
        self.language_buttons['russian'] = ru_btn
        
        about_btn = ttk.Button(control_frame, text="ℹ About", command=self.show_about)
        about_btn.pack(side='right', padx=20)
        self.translatable_widgets[about_btn] = ('text', "ℹ About", "ℹ О программе")
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Generator tab
        gen_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(gen_frame, text=self.tr("Generator"))
        
        self.setup_generator_tab(gen_frame)
        
        # Vault tab
        vault_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(vault_frame, text=self.tr("Vault"))
        
        self.setup_vault_tab(vault_frame)
        
        # Manual Entry tab
        manual_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(manual_frame, text=self.tr("Manual Entry"))
        
        self.setup_manual_tab(manual_frame)
        
        # Обновляем индикацию языка
        self.update_language_indicators()
        
    def setup_generator_tab(self, parent):
        # Length selection
        length_frame = ttk.Frame(parent, style='TFrame')
        length_frame.pack(fill='x', pady=15, padx=20)
        
        length_label = ttk.Label(length_frame, text=self.tr("Password Length:"))
        length_label.pack(side='left')
        self.translatable_widgets[length_label] = ('text', "Password Length:", "Длина пароля:")
        
        self.length_var = tk.IntVar(value=16)
        length_spin = ttk.Spinbox(length_frame, from_=8, to=50, textvariable=self.length_var, width=8)
        length_spin.pack(side='left', padx=10)
        
        # Character options
        options_frame = ttk.LabelFrame(parent, text=self.tr("Character Settings"), style='TFrame')
        options_frame.pack(fill='x', pady=15, padx=20)
        
        self.symbols_var = tk.BooleanVar(value=True)
        self.numbers_var = tk.BooleanVar(value=True)
        self.letters_var = tk.BooleanVar(value=True)
        self.ambiguous_var = tk.BooleanVar(value=False)
        
        symbols_cb = ttk.Checkbutton(options_frame, text=self.tr("Symbols (!@#$%)"), variable=self.symbols_var)
        symbols_cb.pack(anchor='w', pady=2)
        self.translatable_widgets[symbols_cb] = ('text', "Symbols (!@#$%)", "Символы (!@#$%)")
        
        numbers_cb = ttk.Checkbutton(options_frame, text=self.tr("Numbers (123)"), variable=self.numbers_var)
        numbers_cb.pack(anchor='w', pady=2)
        self.translatable_widgets[numbers_cb] = ('text', "Numbers (123)", "Цифры (123)")
        
        letters_cb = ttk.Checkbutton(options_frame, text=self.tr("Letters (ABC)"), variable=self.letters_var)
        letters_cb.pack(anchor='w', pady=2)
        self.translatable_widgets[letters_cb] = ('text', "Letters (ABC)", "Буквы (ABC)")
        
        ambiguous_cb = ttk.Checkbutton(options_frame, text=self.tr("Allow ambiguous characters (Il1O0)"), 
                                      variable=self.ambiguous_var)
        ambiguous_cb.pack(anchor='w', pady=2)
        self.translatable_widgets[ambiguous_cb] = ('text', "Allow ambiguous characters (Il1O0)", 
                                                 "Разрешить неоднозначные символы (Il1O0)")
        
        # Generate button
        generate_btn = ttk.Button(parent, text=self.tr("Generate Password"), 
                                 command=self.generate_password)
        generate_btn.pack(pady=20)
        self.translatable_widgets[generate_btn] = ('text', "Generate Password", "Сгенерировать пароль")
        
        # Password display
        password_frame = ttk.Frame(parent, style='TFrame')
        password_frame.pack(fill='x', pady=10, padx=20)
        
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(password_frame, textvariable=self.password_var, 
                                  font=('Consolas', 14), justify='center')
        password_entry.pack(fill='x', pady=5)
        
        # Save to vault section
        save_section = ttk.LabelFrame(parent, text=self.tr("Save Password"), style='TFrame')
        save_section.pack(fill='x', pady=15, padx=20)
        
        # Site
        site_frame = ttk.Frame(save_section, style='TFrame')
        site_frame.pack(fill='x', pady=8, padx=10)
        
        site_label = ttk.Label(site_frame, text=self.tr("Website:"))
        site_label.pack(side='left')
        self.translatable_widgets[site_label] = ('text', "Website:", "Сайт:")
        
        self.site_var = tk.StringVar()
        site_entry = ttk.Entry(site_frame, textvariable=self.site_var)
        site_entry.pack(side='left', padx=10, fill='x', expand=True)
        
        # Login
        login_frame = ttk.Frame(save_section, style='TFrame')
        login_frame.pack(fill='x', pady=8, padx=10)
        
        login_label = ttk.Label(login_frame, text=self.tr("Login:"))
        login_label.pack(side='left')
        self.translatable_widgets[login_label] = ('text', "Login:", "Логин:")
        
        self.login_var = tk.StringVar()
        login_entry = ttk.Entry(login_frame, textvariable=self.login_var)
        login_entry.pack(side='left', padx=10, fill='x', expand=True)
        
        save_btn = ttk.Button(save_section, text=self.tr("Save to Vault"), command=self.save_to_vault)
        save_btn.pack(pady=10)
        self.translatable_widgets[save_btn] = ('text', "Save to Vault", "Сохранить в хранилище")
        
    def setup_vault_tab(self, parent):
        # Master password protection
        self.master_frame = ttk.LabelFrame(parent, text=self.tr("Vault Security"), style='TFrame')
        self.master_frame.pack(fill='x', pady=15, padx=20)
        self.translatable_widgets[self.master_frame] = ('text', "Vault Security", "Безопасность хранилища")
        
        master_label = ttk.Label(self.master_frame, text=self.tr("Master Password:"))
        master_label.pack(side='left', padx=10)
        self.translatable_widgets[master_label] = ('text', "Master Password:", "Мастер-пароль:")
        
        self.master_var = tk.StringVar()
        master_entry = ttk.Entry(self.master_frame, textvariable=self.master_var, show='•')
        master_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        unlock_btn = ttk.Button(self.master_frame, text=self.tr("Unlock Vault"), command=self.unlock_vault)
        unlock_btn.pack(side='left', padx=10)
        self.translatable_widgets[unlock_btn] = ('text', "Unlock Vault", "Разблокировать хранилище")
        
        # Search frame
        search_frame = ttk.Frame(parent, style='TFrame')
        search_frame.pack(fill='x', pady=10, padx=20)
        
        search_label = ttk.Label(search_frame, text=self.tr("Search:"))
        search_label.pack(side='left')
        self.translatable_widgets[search_label] = ('text', "Search:", "Поиск:")
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, style='Search.TEntry')
        search_entry.pack(side='left', padx=10, fill='x', expand=True)
        search_entry.bind('<KeyRelease>', self.search_passwords)
        
        # Vault content
        self.vault_content_frame = ttk.LabelFrame(parent, text=self.tr("Stored Passwords"), style='TFrame')
        self.vault_content_frame.pack(fill='both', expand=True, pady=15, padx=20)
        self.translatable_widgets[self.vault_content_frame] = ('text', "Stored Passwords", "Сохраненные пароли")
        
        # Create a canvas and scrollbar for the vault with DARK background
        self.vault_canvas = tk.Canvas(self.vault_content_frame, bg='#2c3e50', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.vault_content_frame, orient="vertical", command=self.vault_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.vault_canvas, style='Vault.TFrame')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.vault_canvas.configure(scrollregion=self.vault_canvas.bbox("all"))
        )
        
        self.vault_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.vault_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.vault_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to scroll
        self.vault_canvas.bind("<MouseWheel>", self._on_mousewheel)
        
    def _on_mousewheel(self, event):
        self.vault_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def setup_manual_tab(self, parent):
        manual_frame = ttk.LabelFrame(parent, text=self.tr("Add Password Manually"), style='TFrame')
        manual_frame.pack(fill='both', expand=True, pady=20, padx=20)
        self.translatable_widgets[manual_frame] = ('text', "Add Password Manually", "Добавить пароль вручную")
        
        # Site
        site_frame = ttk.Frame(manual_frame, style='TFrame')
        site_frame.pack(fill='x', pady=10, padx=20)
        
        site_label = ttk.Label(site_frame, text=self.tr("Website:"))
        site_label.pack(anchor='w')
        self.translatable_widgets[site_label] = ('text', "Website:", "Сайт:")
        
        self.manual_site_var = tk.StringVar()
        site_entry = ttk.Entry(site_frame, textvariable=self.manual_site_var, font=('Segoe UI', 10))
        site_entry.pack(fill='x', pady=5)
        
        # Login
        login_frame = ttk.Frame(manual_frame, style='TFrame')
        login_frame.pack(fill='x', pady=10, padx=20)
        
        login_label = ttk.Label(login_frame, text=self.tr("Login:"))
        login_label.pack(anchor='w')
        self.translatable_widgets[login_label] = ('text', "Login:", "Логин:")
        
        self.manual_login_var = tk.StringVar()
        login_entry = ttk.Entry(login_frame, textvariable=self.manual_login_var, font=('Segoe UI', 10))
        login_entry.pack(fill='x', pady=5)
        
        # Password
        password_frame = ttk.Frame(manual_frame, style='TFrame')
        password_frame.pack(fill='x', pady=10, padx=20)
        
        password_label = ttk.Label(password_frame, text=self.tr("Password:"))
        password_label.pack(anchor='w')
        self.translatable_widgets[password_label] = ('text', "Password:", "Пароль:")
        
        self.manual_password_var = tk.StringVar()
        password_entry = ttk.Entry(password_frame, textvariable=self.manual_password_var, 
                                 font=('Segoe UI', 10), show='•')
        password_entry.pack(fill='x', pady=5)
        
        show_pass_var = tk.BooleanVar()
        show_pass_cb = ttk.Checkbutton(password_frame, text=self.tr("Show password"), 
                                      variable=show_pass_var,
                                      command=lambda: self.toggle_password_visibility(
                                          password_entry, show_pass_var.get()))
        show_pass_cb.pack(anchor='w', pady=5)
        self.translatable_widgets[show_pass_cb] = ('text', "Show password", "Показать пароль")
        
        # Buttons
        button_frame = ttk.Frame(manual_frame, style='TFrame')
        button_frame.pack(fill='x', pady=20, padx=20)
        
        save_manual_btn = ttk.Button(button_frame, text=self.tr("Save Password"), 
                                    command=self.save_manual_entry)
        save_manual_btn.pack(side='left', padx=5)
        self.translatable_widgets[save_manual_btn] = ('text', "Save Password", "Сохранить пароль")
        
        clear_btn = ttk.Button(button_frame, text=self.tr("Clear Fields"), 
                              command=self.clear_manual_fields)
        clear_btn.pack(side='left', padx=5)
        self.translatable_widgets[clear_btn] = ('text', "Clear Fields", "Очистить поля")
        
    def toggle_password_visibility(self, entry, show):
        entry.config(show='' if show else '•')
        
    def clear_manual_fields(self):
        self.manual_site_var.set('')
        self.manual_login_var.set('')
        self.manual_password_var.set('')
        
    def save_manual_entry(self):
        if not self.fernet:
            messagebox.showerror(self.tr("Error"), self.tr("Vault is locked!"))
            return
            
        site = self.manual_site_var.get()
        login = self.manual_login_var.get()
        password = self.manual_password_var.get()
        
        if not all([site, login, password]):
            messagebox.showwarning(self.tr("Warning"), self.tr("Please fill all fields"))
            return
            
        new_entry = {
            'site': site,
            'login': login,
            'password': password
        }
        
        self.vault_data.append(new_entry)
        self.save_data()
        messagebox.showinfo(self.tr("Success"), self.tr("Password saved successfully!"))
        self.clear_manual_fields()
        self.update_vault_display()
        
    def generate_password(self):
        length = self.length_var.get()
        characters = ""
        
        if self.symbols_var.get():
            characters += "!@#$%&*+-=?"
        if self.numbers_var.get():
            characters += string.digits
        if self.letters_var.get():
            characters += string.ascii_letters
        
        if not characters:
            messagebox.showwarning(self.tr("Warning"), self.tr("Please select at least one character set"))
            return
        
        if not self.ambiguous_var.get():
            ambiguous_chars = 'Il1O0'
            characters = ''.join(c for c in characters if c not in ambiguous_chars)
        
        password = ''.join(random.choice(characters) for _ in range(length))
        self.password_var.set(password)
        pyperclip.copy(password)
        messagebox.showinfo(self.tr("Success"), self.tr("Password generated and copied to clipboard!"))
        
    def save_to_vault(self):
        if not self.fernet:
            messagebox.showerror(self.tr("Error"), self.tr("Vault is locked!"))
            return
            
        site = self.site_var.get()
        login = self.login_var.get()
        password = self.password_var.get()
        
        if not all([site, login, password]):
            messagebox.showwarning(self.tr("Warning"), self.tr("Please fill all fields"))
            return
            
        new_entry = {
            'site': site,
            'login': login,
            'password': password
        }
        
        self.vault_data.append(new_entry)
        self.save_data()
        messagebox.showinfo(self.tr("Success"), self.tr("Password saved successfully!"))
        self.update_vault_display()
        
    def unlock_vault(self, initial_setup=False):
        master_password = self.master_var.get().encode()
        if not master_password:
            if not initial_setup:
                messagebox.showwarning(self.tr("Warning"), self.tr("Please enter master password"))
            return
            
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'fixed_salt_consider_random',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_password))
            self.fernet = Fernet(key)
            
            # Загружаем данные после установки fernet
            self.load_data()
            
            # Test decryption or create new vault
            if os.path.exists(self.data_file):
                with open(self.data_file, 'rb') as f:
                    encrypted = f.read()
                if encrypted:
                    self.fernet.decrypt(encrypted)
            else:
                # Create new vault
                self.vault_data = []
                self.save_data()
            
            self.master_frame.pack_forget()
            self.update_vault_display()
            if not initial_setup:
                messagebox.showinfo(self.tr("Success"), self.tr("Vault unlocked successfully!"))
        except Exception as e:
            messagebox.showerror(self.tr("Error"), self.tr("Wrong master password or corrupted vault!"))
            
    def search_passwords(self, event=None):
        search_term = self.search_var.get().lower()
        if not search_term:
            self.update_vault_display()
            return
            
        filtered_data = [
            entry for entry in self.vault_data 
            if (search_term in entry['site'].lower() or 
                search_term in entry['login'].lower() or
                search_term in entry['password'].lower())
        ]
        self.update_vault_display(filtered_data)
        
    def update_vault_display(self, data=None):
        # Clear the scrollable frame and vault widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.vault_widgets.clear()
            
        display_data = data if data is not None else self.vault_data
        
        if not display_data:
            no_data_label = ttk.Label(self.scrollable_frame, 
                                    text=self.tr("No passwords stored yet"),
                                    style='Vault.TLabel')
            no_data_label.pack(pady=20)
            self.vault_widgets.append(no_data_label)
            return
            
        for i, entry in enumerate(display_data):
            # Create a frame for each password entry with DARK background
            entry_frame = ttk.Frame(self.scrollable_frame, style='Vault.TFrame')
            entry_frame.pack(fill='x', pady=8, padx=10)
            self.vault_widgets.append(entry_frame)
            
            # Configure grid weights for proper alignment
            entry_frame.columnconfigure(1, weight=1)
            
            # Site row
            site_label = ttk.Label(entry_frame, text=f"{self.tr('Site')}:", 
                                  font=('Segoe UI', 9, 'bold'), style='Vault.TLabel')
            site_label.grid(row=0, column=0, sticky='w', padx=(0, 5))
            self.vault_widgets.append(site_label)
            
            site_value = ttk.Label(entry_frame, text=entry['site'], 
                                  font=('Segoe UI', 9), style='Vault.TLabel')
            site_value.grid(row=0, column=1, sticky='w')
            self.vault_widgets.append(site_value)
            
            site_copy_btn = ttk.Button(entry_frame, text="📋", 
                                      command=lambda s=entry['site']: self.copy_to_clipboard(s),
                                      width=3)
            site_copy_btn.grid(row=0, column=2, padx=(5, 0))
            self.vault_widgets.append(site_copy_btn)
            
            # Login row
            login_label = ttk.Label(entry_frame, text=f"{self.tr('Login')}:", 
                                   font=('Segoe UI', 9, 'bold'), style='Vault.TLabel')
            login_label.grid(row=1, column=0, sticky='w', padx=(0, 5))
            self.vault_widgets.append(login_label)
            
            login_value = ttk.Label(entry_frame, text=entry['login'], 
                                   font=('Segoe UI', 9), style='Vault.TLabel')
            login_value.grid(row=1, column=1, sticky='w')
            self.vault_widgets.append(login_value)
            
            login_copy_btn = ttk.Button(entry_frame, text="📋", 
                                       command=lambda l=entry['login']: self.copy_to_clipboard(l),
                                       width=3)
            login_copy_btn.grid(row=1, column=2, padx=(5, 0))
            self.vault_widgets.append(login_copy_btn)
            
            # Password row
            password_label = ttk.Label(entry_frame, text=f"{self.tr('Password')}:", 
                                      font=('Segoe UI', 9, 'bold'), style='Vault.TLabel')
            password_label.grid(row=2, column=0, sticky='w', padx=(0, 5))
            self.vault_widgets.append(password_label)
            
            password_value = ttk.Label(entry_frame, text="•" * len(entry['password']), 
                                      font=('Consolas', 9), style='Vault.TLabel')
            password_value.grid(row=2, column=1, sticky='w')
            self.vault_widgets.append(password_value)
            
            # Show/hide password functionality
            def toggle_password_display(label, password, button):
                if label.cget('text').startswith('•'):
                    label.config(text=password)
                    button.config(text="👁")
                else:
                    label.config(text="•" * len(password))
                    button.config(text="📋")
            
            password_copy_btn = ttk.Button(entry_frame, text="📋", 
                                          command=lambda p=entry['password']: self.copy_to_clipboard(p),
                                          width=3)
            password_copy_btn.grid(row=2, column=2, padx=(5, 0))
            self.vault_widgets.append(password_copy_btn)
            
            # Add show/hide button
            show_hide_btn = ttk.Button(entry_frame, text="👁",
                                      command=lambda l=password_value, p=entry['password'], b=password_copy_btn: 
                                      toggle_password_display(l, p, b),
                                      width=3)
            show_hide_btn.grid(row=2, column=3, padx=(2, 0))
            self.vault_widgets.append(show_hide_btn)
            
            # Copy all button
            copy_all_text = f"{self.tr('Site')}: {entry['site']}\n{self.tr('Login')}: {entry['login']}\n{self.tr('Password')}: {entry['password']}"
            copy_all_btn = ttk.Button(entry_frame, text=self.tr("Copy All"),
                                     command=lambda t=copy_all_text: self.copy_to_clipboard(t))
            copy_all_btn.grid(row=3, column=0, columnspan=4, pady=(5, 0), sticky='we')
            self.vault_widgets.append(copy_all_btn)
            
            # Separator
            separator = ttk.Separator(entry_frame, orient='horizontal')
            separator.grid(row=4, column=0, columnspan=4, sticky='we', pady=(8, 0))
            self.vault_widgets.append(separator)
            
        # Update scroll region
        self.scrollable_frame.update_idletasks()
        self.vault_canvas.configure(scrollregion=self.vault_canvas.bbox("all"))
        
    def copy_to_clipboard(self, text):
        pyperclip.copy(text)
        messagebox.showinfo(self.tr("Success"), self.tr("Copied to clipboard!"))
        
    def load_data(self):
        """Загружает данные из зашифрованного файла"""
        self.vault_data = []
        if os.path.exists(self.data_file) and self.fernet:
            try:
                with open(self.data_file, 'rb') as f:
                    encrypted = f.read()
                if encrypted:
                    decrypted = self.fernet.decrypt(encrypted)
                    self.vault_data = json.loads(decrypted)
            except Exception as e:
                print(f"Error loading data: {e}")
                self.vault_data = []
                
    def save_data(self):
        """Сохраняет данные в зашифрованный файл"""
        if self.fernet:
            try:
                data_json = json.dumps(self.vault_data).encode()
                encrypted = self.fernet.encrypt(data_json)
                with open(self.data_file, 'wb') as f:
                    f.write(encrypted)
            except Exception as e:
                print(f"Error saving data: {e}")
                
    def set_language(self, lang):
        self.language = lang
        self.update_ui_language()
        self.update_language_indicators()
        messagebox.showinfo(self.tr("Info"), self.tr("Language changed successfully!"))
        
    def update_language_indicators(self):
        """Обновляет индикацию выбранного языка"""
        for lang, button in self.language_buttons.items():
            if lang == self.language:
                button.configure(style='Selected.TButton')  # Выбранный язык - голубой
            else:
                button.configure(style='Language.TButton')  # Невыбранный - темный
        
    def update_ui_language(self):
        # Update notebook tabs
        tabs = ["Generator", "Vault", "Manual Entry"]
        ru_tabs = ["Генератор", "Хранилище", "Ручной ввод"]
        
        for i, tab in enumerate(tabs):
            self.notebook.tab(i, text=ru_tabs[i] if self.language == 'russian' else tab)
        
        # Update all registered widgets
        widgets_to_remove = []
        for widget, (attribute, en_text, ru_text) in self.translatable_widgets.items():
            try:
                new_text = ru_text if self.language == 'russian' else en_text
                if attribute == 'text':
                    widget.config(text=new_text)
            except tk.TclError:
                # Если виджет больше не существует, помечаем для удаления
                widgets_to_remove.append(widget)
        
        # Удаляем несуществующие виджеты
        for widget in widgets_to_remove:
            if widget in self.translatable_widgets:
                del self.translatable_widgets[widget]
                
        # Force update of vault display if it's visible
        if hasattr(self, 'vault_canvas') and self.fernet:
            self.update_vault_display()
                
    def show_about(self):
        about_text_en = """Password Vault v1.0

Secure and minimalistic password manager:
• Password generation with settings
• Secure encrypted storage
• Master password protection
• Copy to clipboard
• Search function
• Multi-language support

The author is Vanek:
GitHub - https://github.com/Ivan2812446/
Telegram - https://t.me/Ivans_Tech_Notes

Your passwords are encrypted using military-grade encryption."""
        
        about_text_ru = """Password Vault v1.0

Безопасный и минималистичный менеджер паролей:
• Генерация паролей с настройками
• Безопасное зашифрованное хранилище
• Защита мастер-паролем
• Копирование в буфер обмена
• Функция поиска
• Поддержка нескольких языков

Автор - Ванек:
GitHub - https://github.com/Ivan2812446/
Telegram - https://t.me/Ivans_Tech_Notes

Ваши пароли шифруются с использованием военного уровня шифрования."""
        
        messagebox.showinfo(self.tr("About"), 
                          about_text_ru if self.language == 'russian' else about_text_en)
        
    def tr(self, text):
        translations = {
            'Generator': {'english': 'Generator', 'russian': 'Генератор'},
            'Vault': {'english': 'Vault', 'russian': 'Хранилище'},
            'Manual Entry': {'english': 'Manual Entry', 'russian': 'Ручной ввод'},
            'Password Length:': {'english': 'Password Length:', 'russian': 'Длина пароля:'},
            'Character Settings': {'english': 'Character Settings', 'russian': 'Настройки символов'},
            'Symbols (!@#$%)': {'english': 'Symbols (!@#$%)', 'russian': 'Символы (!@#$%)'},
            'Numbers (123)': {'english': 'Numbers (123)', 'russian': 'Цифры (123)'},
            'Letters (ABC)': {'english': 'Letters (ABC)', 'russian': 'Буквы (ABC)'},
            'Allow ambiguous characters (Il1O0)': {'english': 'Allow ambiguous characters (Il1O0)', 
                                                 'russian': 'Разрешить неоднозначные символы (Il1O0)'},
            'Generate Password': {'english': 'Generate Password', 'russian': 'Сгенерировать пароль'},
            'Save Password': {'english': 'Save Password', 'russian': 'Сохранить пароль'},
            'Website:': {'english': 'Website:', 'russian': 'Сайт:'},
            'Login:': {'english': 'Login:', 'russian': 'Логин:'},
            'Password:': {'english': 'Password:', 'russian': 'Пароль:'},
            'Save to Vault': {'english': 'Save to Vault', 'russian': 'Сохранить в хранилище'},
            'Vault Security': {'english': 'Vault Security', 'russian': 'Безопасность хранилища'},
            'Master Password:': {'english': 'Master Password:', 'russian': 'Мастер-пароль:'},
            'Unlock Vault': {'english': 'Unlock Vault', 'russian': 'Разблокировать хранилище'},
            'Stored Passwords': {'english': 'Stored Passwords', 'russian': 'Сохраненные пароли'},
            'Add Password Manually': {'english': 'Add Password Manually', 'russian': 'Добавить пароль вручную'},
            'Show password': {'english': 'Show password', 'russian': 'Показать пароль'},
            'Clear Fields': {'english': 'Clear Fields', 'russian': 'Очистить поля'},
            'Error': {'english': 'Error', 'russian': 'Ошибка'},
            'Warning': {'english': 'Warning', 'russian': 'Предупреждение'},
            'Success': {'english': 'Success', 'russian': 'Успех'},
            'Info': {'english': 'Info', 'russian': 'Информация'},
            'Vault is locked!': {'english': 'Vault is locked!', 'russian': 'Хранилище заблокировано!'},
            'Please fill all fields': {'english': 'Please fill all fields', 'russian': 'Пожалуйста, заполните все поля'},
            'Please select at least one character set': {'english': 'Please select at least one character set', 
                                                       'russian': 'Пожалуйста, выберите хотя бы один набор символов'},
            'Password generated and copied to clipboard!': {'english': 'Password generated and copied to clipboard!', 
                                                          'russian': 'Пароль сгенерирован и скопирован в буфер обмена!'},
            'Password saved successfully!': {'english': 'Password saved successfully!', 
                                           'russian': 'Пароль успешно сохранен!'},
            'Please enter master password': {'english': 'Please enter master password', 
                                           'russian': 'Пожалуйста, введите мастер-пароль'},
            'Vault unlocked successfully!': {'english': 'Vault unlocked successfully!', 
                                           'russian': 'Хранилище успешно разблокировано!'},
            'Wrong master password or corrupted vault!': {'english': 'Wrong master password or corrupted vault!', 
                                                        'russian': 'Неверный мастер-пароль или поврежденное хранилище!'},
            'No passwords stored yet': {'english': 'No passwords stored yet', 'russian': 'Пароли еще не сохранены'},
            'Copy': {'english': 'Copy', 'russian': 'Копировать'},
            'Copy All': {'english': 'Copy All', 'russian': 'Копировать всё'},
            'Copied to clipboard!': {'english': 'Copied to clipboard!', 'russian': 'Скопировано в буфер обмена!'},
            'Language changed successfully!': {'english': 'Language changed successfully!', 
                                             'russian': 'Язык успешно изменен!'},
            'About': {'english': 'About', 'russian': 'О программе'},
            'Search:': {'english': 'Search:', 'russian': 'Поиск:'},
            'Site': {'english': 'Site', 'russian': 'Сайт'},
        }
        return translations.get(text, {}).get(self.language, text)

if __name__ == "__main__":
    app = PasswordManager()
    app.root.mainloop()