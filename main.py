"""
GlassPrinter - Aplicação para Geração de Etiquetas em PDF.

Aplicação Tkinter que permite adicionar registros manualmente ou importar
arquivos em lote (Excel/CSV) e gerar etiquetas em PDF com layouts específicos.

Uso:
    python main.py
"""


import logging
import json
import os
import pandas as pd
import sys
from pathlib import Path
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Optional, Any
from PIL import Image

from core.config import (
    APP_TITLE,
    APP_VERSION,
    APP_WINDOW_WIDTH,
    APP_WINDOW_HEIGHT,
    LAYOUT_ADM,
    LAYOUT_UNIDADE,
    LAYOUT_PAT_ID,
    LAYOUT_GATI,
    LABEL_SIZE,
    LABEL_SIZE_PAT_ID,
    PAT_ID_EQUIPMENT_TYPES,
    AVAILABLE_LAYOUTS,
    FORM_FIELDS,
    FORM_FIELDS_ADM,
    FORM_FIELDS_UNIDADE,
    FORM_FIELDS_PAT_ID,
    FORM_FIELDS_GATI,
    REQUIRED_FIELDS,
    COLOR_HEADER_ADM,
    COLOR_PRIMARY_BLUE,
    COLOR_SUPPORT_BLUE,
    COLOR_HEADER_UNIDADE,
    ICON_FILE,
    LOGO_FILE,
    ICONS_DIR,
    BACKGROUND_FILE,
    LOGO_TYPE_FILE,
    FONT_DEFAULT,
    FONT_BOLD,
    COLOR_SUCCESS,
    MESSAGES,
    HISTORY_FILES,
    SETTINGS_FILE,
    JIRA_BASE_URL,
    CSV_SEPARATOR,
    CSV_ENCODING,
)
from core.engine import PDFEngine, PrintEngine
from core.utils import get_resource_path, get_default_output_path, safe_get_dict_value, register_custom_fonts
from core.exceptions import ValidationError


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuração global do CustomTkinter
ctk.set_appearance_mode("System")  # "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class LogoInputDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: tk.Misc,
        title: str,
        text: str,
        logo_path: str,
        icon_path: str,
        options: Optional[List[str]] = None,
    ) -> None:
        super().__init__(master)
        self.title(title)

        self.transient(master)
        self.grab_set()
        self.resizable(False, False)
    
        try:
            self.iconbitmap(icon_path)
        except Exception:
            logger.debug("Falha ao setar iconbitmap em LogoInputDialog.", exc_info=True)

        self._input_value: Optional[str] = None

        container = ctk.CTkFrame(self, corner_radius=10)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 6))

        # Carrega logo (com suporte a fallback para a logo padrão)
        self._logo_photo = None
        try:
            try:
                img = Image.open(logo_path)
            except Exception:
                # Fallback para o arquivo de logo padrão se a abertura falhar
                img = Image.open(get_resource_path(LOGO_FILE))

            if img:
                max_h = 60  # Increased height for a larger logo
                if img.height > max_h:
                    ratio = max_h / float(img.height)
                    new_w = int(float(img.width) * ratio)
                    img = img.resize((new_w, max_h))

                self._logo_photo = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=img.size,
                )
                ctk.CTkLabel(header, image=self._logo_photo, text="").pack(pady=(0, 5))
        except Exception:
            logger.debug("Não foi possível carregar a logo no diálogo.", exc_info=True)
        ctk.CTkLabel(container, text=text, wraplength=320, justify="center").pack(pady=(0, 8))

        self.option_menu = None
        if options:
            self.option_menu = ctk.CTkOptionMenu(container, values=options, width=320)
            self.option_menu.pack(pady=(0, 10))
            self.entry = None
        else:
            self.entry = ctk.CTkEntry(container, width=320)
            self.entry.pack(pady=(0, 10))
            self.entry.focus_set()

        actions = ctk.CTkFrame(container, fg_color="transparent")
        actions.pack(pady=(5, 0))

        ok_btn = ctk.CTkButton(actions, text="OK", command=self._on_ok, width=100)
        ok_btn.pack(side="left", padx=5)
        cancel_btn = ctk.CTkButton(
            actions,
            text="Cancelar",
            command=self._on_cancel,
            width=100,
            fg_color="#b00020",
        )
        cancel_btn.pack(side="left", padx=5)

        self.bind("<Return>", lambda _e: self._on_ok())
        self.bind("<Escape>", lambda _e: self._on_cancel())

        self.update_idletasks()
        try:
            mw = master.winfo_width()
            mh = master.winfo_height()
            mx = master.winfo_rootx()
            my = master.winfo_rooty()
            w = self.winfo_width()
            h = self.winfo_height()
            self.geometry(f"+{mx + (mw - w) // 2}+{my + (mh - h) // 2}")
        except Exception:
            pass

    def _on_ok(self) -> None:
        if self.option_menu:
            value = self.option_menu.get()
        else:
            value = self.entry.get().strip()
        self._input_value = value if value else ""
        self.grab_release()
        self.destroy()

    def _on_cancel(self) -> None:
        self._input_value = None
        self.grab_release()
        self.destroy()

    def get_input(self) -> Optional[str]:
        """
        Abre o diálogo e aguarda fechamento.

        Returns:
            str | None: valor digitado ou None se cancelado.
        """
        self.wait_window()
        return self._input_value


class GlassPrinterApp:
    """
    Aplicativo principal para gerar etiquetas GlassPrinter em PDF.

    Responsabilidades:
    - Gerenciar a interface gráfica (GUI)
    - Coletar dados do usuário (manual ou importação)
    - Validar e normalizar dados
    - Coordenar geração de PDF e backup
    - Controlar impressão

    Attributes:
        root (ctk.CTk): Widget raiz da aplicação.
        dados_fila (List[Dict]): Lista de registros a processar.
        layout_ativo (Optional[str]): Layout selecionado (adm/unidade).
        pdf_engine (PDFEngine): Engine de geração de PDF.
        print_engine (PrintEngine): Engine de impressão.
    """

    def __init__(self, root: ctk.CTk) -> None:
        """
        Inicializa a aplicação.

        Args:
            root: Widget Tk raiz da aplicação.
        """
        self.root = root
        register_custom_fonts() # Registra as fontes no ReportLab
        self._carregar_configuracoes()
        self._load_sidebar_icons()
        self._configure_window()
        # Registra um callback para atualizar o estilo da tabela se o tema mudar
        self.root.bind("<<ThemeChanged>>", lambda e: self._setup_styles())
        self._initialize_engines()
        self._initialize_data_structures()
        self._load_icon()
        self._setup_sidebar()
        self._setup_styles()
        self._show_view("welcome")

    def _load_sidebar_icons(self) -> None:
        """Carrega os ícones modernos da pasta assets/icons."""
        icon_size = (20, 20)
        self.icons: Dict[str, ctk.CTkImage] = {}
        
        icon_files = {
            "printer": ("printer.png", "🖨️"),
            "history": ("history.png", "📜"),
            "settings": ("settings.png", "⚙️"),
            "menu": ("menu.png", "☰")
        }

        # Armazenamos os fallbacks para usar se a imagem falhar
        self.icon_fallbacks = {k: v[1] for k, v in icon_files.items()}

        for key, (filename, _) in icon_files.items():
            path = get_resource_path(os.path.join(ICONS_DIR, filename))
            try:
                img = Image.open(path)
                self.icons[key] = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=icon_size
                )
            except Exception:
                logger.warning(f"Ícone {filename} não encontrado. Usando fallback.")
                self.icons[key] = None

    def _load_background(self) -> None:
        """Carrega a imagem de fundo responsiva ao tema."""
        try:
            light_path = get_resource_path(BACKGROUND_LIGHT)
            dark_path = get_resource_path(BACKGROUND_DARK)
            
            img_light = Image.open(light_path)
            img_dark = Image.open(dark_path)
            
            # Define o tamanho baseado na resolução da tela para preenchimento total
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            
            self.bg_image = ctk.CTkImage(
                light_image=img_light,
                dark_image=img_dark,
                size=(screen_w, screen_h)
            )
            logger.info("Imagens de fundo carregadas com sucesso.")
        except Exception as e:
            logger.warning(f"Erro ao carregar imagens de fundo: {e}")
            self.bg_image = None

    def _configure_window(self) -> None:
        """Configura propriedades da janela principal."""
        self.root.title(APP_TITLE)
        self.root.state('zoomed') # Abre a janela maximizada
        ctk.set_appearance_mode(self.config_data.get("appearance_mode", "System"))

        # Sidebar frame
        self.sidebar_width = 220
        self.sidebar_collapsed_width = 60
        self.sidebar_expanded = True
        self.submenu_open = False  # usado no toggle/layout

        # Cores de fundo estilo VS Code (Dark: #252526, Light: #f3f3f3)
        self.sidebar_frame = ctk.CTkFrame(self.root, width=self.sidebar_width, corner_radius=0, fg_color=("#f3f3f3", "#333333"))
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)
        
        # Bindings para expansão responsiva no hover
        self.sidebar_frame.bind("<Enter>", lambda e: self._handle_sidebar_hover(True))
        self.sidebar_frame.bind("<Leave>", lambda e: self._handle_sidebar_hover(False))

        # Conteúdo Principal
        self.main_container = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        self.main_container.pack(side="right", fill="both", expand=True)

    def _setup_sidebar(self) -> None:
        """Configura o menu lateral esquerdo."""
        # Cabeçalho com Botão Sanduíche
        header = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        header.pack(fill="x", pady=10, padx=10)
        
        self.btn_menu = ctk.CTkButton(header, text="☰", width=40, fg_color="transparent", 
                                    image=self.icons.get("menu"),
                                    text_color=("#616161", "#cccccc"),
                                    command=self._toggle_sidebar)
        self.btn_menu.pack(side="left")
        
        self.lbl_logo_text = ctk.CTkLabel(header, text="GlassPrinter", font=(FONT_BOLD, 16))
        self.lbl_logo_text.pack(side="left", padx=10)

        # Container para Ferramentas (Base)
        self.bottom_nav_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.bottom_nav_frame.pack(side="bottom", fill="x", pady=10)

        # Container para Funções (Topo)
        self.top_nav_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.top_nav_frame.pack(side="top", fill="x", pady=(20, 0))

        # Botões Principais
        self._nav_buttons = []
        
        # --- FUNÇÕES (Topo) ---
        self.submenu_open = False
        self.btn_impressao = self._create_nav_button(
            "Gerar Etiquetas",
            self.icons.get("printer"),
            self._toggle_layout_submenu,
            icon_key="printer",
            parent=self.top_nav_frame,
        )
        self.submenu_frame = ctk.CTkFrame(self.top_nav_frame, fg_color="transparent")
        # Os botões do submenu são criados mas não 'pack'ados ainda
        self.btn_adm = self._create_nav_button(
            "Layout ADM",
            None,
            lambda: self._show_view("layout", LAYOUT_ADM),
            icon_key="submenu-adm",
            parent=self.submenu_frame,
        )
        self.btn_unidade = self._create_nav_button(
            "Layout Unidade",
            None,
            lambda: self._show_view("layout", LAYOUT_UNIDADE),
            icon_key="submenu-unidade",
            parent=self.submenu_frame,
        )
        self.btn_pat_id = self._create_nav_button(
            "PAT ID (Caixas)",
            None,
            lambda: self._show_view("layout", LAYOUT_PAT_ID),
            icon_key="submenu-pat",
            parent=self.submenu_frame,
        )
        self.btn_gati = self._create_nav_button(
            "Gerador GATI",
            None,
            lambda: self._show_view("layout", LAYOUT_GATI),
            icon_key="submenu-gati",
            parent=self.submenu_frame,
        )
        
        # Garante que passar o mouse sobre os botões não feche o menu
        self._bind_hover_recursive(self.sidebar_frame)

        # --- FERRAMENTAS (Base) ---
        self.btn_history = self._create_nav_button(
            "Histórico",
            self.icons.get("history"),
            lambda: self._show_view("history"),
            icon_key="history",
            parent=self.bottom_nav_frame,
        )
        self.btn_settings = self._create_nav_button(
            "Configurações",
            self.icons.get("settings"),
            lambda: self._show_view("settings"),
            icon_key="settings",
            parent=self.bottom_nav_frame,
        )

    def _bind_hover_recursive(self, widget):
        """Aplica o evento de hover a todos os filhos para evitar que o menu feche ao tocar em botões."""
        widget.bind("<Enter>", lambda e: self._handle_sidebar_hover(True), add="+")
        widget.bind("<Leave>", lambda e: self._handle_sidebar_hover(False), add="+")
        for child in widget.winfo_children():
            self._bind_hover_recursive(child)

    def _create_nav_button(
        self,
        text: str,
        icon_img: Optional[ctk.CTkImage],
        command: Any,
        icon_key: str,
        parent: Optional[Any] = None,
    ) -> ctk.CTkButton:
        p = parent if parent else self.sidebar_frame
        
        # Container para o botão e o indicador (VS Code Style)
        btn_container = ctk.CTkFrame(p, fg_color="transparent", corner_radius=0)
        btn_container.pack(fill="x", padx=0, pady=1)

        # Barrinha vertical de seleção (2px de largura, encostada na esquerda)
        indicator = ctk.CTkFrame(btn_container, width=2, height=35, fg_color="transparent", corner_radius=0)
        indicator.pack(side="left")

        fallback_symbol = self.icon_fallbacks.get(icon_key, "•")

        btn = ctk.CTkButton(btn_container, text=text, image=icon_img, anchor="w", fg_color="transparent",
                            text_color=("#616161", "#858585"), hover_color=("#e8e8e8", "#2a2d2e"),
                            command=command, height=38, corner_radius=0, font=(FONT_DEFAULT, 13), compound="left")
        btn.pack(side="left", fill="x", expand=True)

        btn._base_text = text
        btn._full_text = text
        btn._icon_key = icon_key
        btn._indicator = indicator
        self._nav_buttons.append(btn)
        return btn

    def _handle_sidebar_hover(self, expand: bool) -> None:
        """Gerencia a expansão e contração baseado na posição do mouse."""
        if expand and not self.sidebar_expanded:
            self._toggle_sidebar(force_expand=True)
        elif not expand and self.sidebar_expanded:
            # Pequeno delay para conferir se o mouse realmente saiu da área da sidebar
            self.root.after(100, self._check_sidebar_leave)

    def _check_sidebar_leave(self) -> None:
        """Verifica se o mouse ainda está sobre a área da sidebar antes de fechar."""
        try:
            px, py = self.root.winfo_pointerxy()
            sx = self.sidebar_frame.winfo_rootx()
            sy = self.sidebar_frame.winfo_rooty()
            sw = self.sidebar_frame.winfo_width()
            sh = self.sidebar_frame.winfo_height()

            # Se o mouse não estiver mais dentro dos limites da barra lateral
            if not (sx <= px <= sx + sw and sy <= py <= sy + sh):
                if self.sidebar_expanded:
                    self._toggle_sidebar(force_expand=False)
        except Exception:
            # Evita erros caso a janela seja fechada durante a verificação
            pass

    def _toggle_sidebar(self, force_expand: Optional[bool] = None) -> None:
        new_state = force_expand if force_expand is not None else not self.sidebar_expanded
        
        if not new_state: # Recolher
            self.sidebar_frame.configure(width=self.sidebar_collapsed_width)
            self.lbl_logo_text.pack_forget()
            for btn in self._nav_buttons:
                # Verifica se o botão tem uma imagem válida carregada
                has_image = btn.cget("image") is not None
                if not has_image:
                    fallback = self.icon_fallbacks.get(btn._icon_key, "•")
                    btn.configure(text=fallback, anchor="center")
                else:
                    btn.configure(text="", anchor="center")

            if self.submenu_open:
                self.submenu_frame.pack_forget()
        else: # Expandir
            self.sidebar_frame.configure(width=self.sidebar_width)
            for btn in self._nav_buttons:
                display_text = btn._full_text
                if btn == self.btn_impressao:
                    arrow = " ▼" if self.submenu_open else " ▶"
                    display_text = f"{btn._base_text}{arrow}"
                btn.configure(text=display_text, anchor="w")
            if self.submenu_open:
                self.submenu_frame.pack(fill="x")
        
        self.sidebar_expanded = new_state

    def _toggle_layout_submenu(self) -> None:
        """Alterna a visibilidade das opções de layout e atualiza a seta."""
        if self.submenu_open:
            self.submenu_frame.pack_forget()
            self.submenu_open = False
            arrow = " ▶"
        else:
            self.submenu_frame.pack(fill="x")
            self.submenu_open = True
            arrow = " ▼"
            if not self.sidebar_expanded:
                self._toggle_sidebar(force_expand=True)
        
        self.btn_impressao._full_text = f"{self.btn_impressao._base_text}{arrow}"
        if self.sidebar_expanded:
            self.btn_impressao.configure(text=self.btn_impressao._full_text)

    def _carregar_configuracoes(self) -> None:
        """Carrega configurações do arquivo JSON ou define padrões."""
        # Define o caminho base (diretório do script ou do executável)
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        self.settings_path = os.path.join(self.base_dir, SETTINGS_FILE)

        self.config_data = {
            "appearance_mode": "System",
            "jira_url": JIRA_BASE_URL,
            "auto_abrir_pdf": True,
            "output_dir": str(get_default_output_path()),
            "auto_imprimir": False
        }
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    file_configs = json.load(f)
                    
                    # Migração automática: Se o caminho salvo for o antigo padrão no Desktop,
                    # ignoramos para que o sistema use o novo padrão portátil (ao lado do executável)
                    old_desktop_default = str(Path.home() / "Desktop" / "Etiquetas_GlassPrinter")
                    if file_configs.get("output_dir") == old_desktop_default:
                        file_configs.pop("output_dir", None)
                        logger.info("Antigo caminho do Desktop detectado. Migrando para modo portátil.")
                        
                    self.config_data.update(file_configs)
            except Exception as e:
                logger.error(f"Erro ao carregar settings.json: {e}")

    def _aplicar_configuracoes(self, novas_configs: Dict[str, Any]) -> None:
        """Aplica as novas configurações e atualiza a interface."""
        self.config_data = novas_configs
        ctk.set_appearance_mode(self.config_data["appearance_mode"])
        # Atualiza o diretório do engine
        self.pdf_engine.output_dir = Path(self.config_data.get("output_dir", str(get_default_output_path())))
        
        self._setup_styles()
        messagebox.showinfo("Sucesso", "Configurações aplicadas!")

    def _setup_styles(self) -> None:
        """Configura o estilo do Treeview para combinar com o CustomTkinter."""
        style = ttk.Style()
        
        # Melhora a detecção para sincronizar o Treeview (TTK) com o CustomTkinter
        # Se estiver em 'System', verifica se o tema atual é escuro
        mode = ctk.get_appearance_mode()
        is_dark = mode == "Dark" or (mode == "System" and ctk.ThemeManager.theme["CTk"]["fg_color"][1].startswith("#"))
        
        bg_color = "#2b2b2b" if is_dark else "#ffffff"
        fg_color = "#ffffff" if is_dark else "#000000"
        selected_color = "#1f538d"
        row_alt_color = "#323232" if is_dark else "#f9f9f9"

        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=bg_color,
            foreground=fg_color,
            fieldbackground=bg_color,
            borderwidth=1,
            relief="solid",
            font=(FONT_DEFAULT, 9),
            rowheight=30
        )
        style.map("Treeview", background=[('selected', selected_color)])
        
        # Estilo Excel: Cabeçalho com fonte em negrito e bordas visíveis
        style.configure("Treeview.Heading", 
                        background="#3b3b3b" if is_dark else "#d0d0d0", 
                        foreground=fg_color,
                        font=(FONT_DEFAULT, 10, "bold"),
                        borderwidth=1,
                        relief="solid")

        if self.tree and self.tree.winfo_exists(): # For layout UI
            self.tree.tag_configure('oddrow', background=bg_color)
            self.tree.tag_configure('evenrow', background=row_alt_color)
        if hasattr(self, 'history_tree') and self.history_tree and self.history_tree.winfo_exists(): # For history UI
            self.history_tree.tag_configure('oddrow', background=bg_color)
            self.history_tree.tag_configure('evenrow', background=row_alt_color)

    def _initialize_engines(self) -> None:
        """Inicializa os engines de PDF e impressão."""
        self.pdf_engine = PDFEngine(output_dir=Path(self.config_data.get("output_dir", str(get_default_output_path()))))
        self.print_engine = PrintEngine()

    def _initialize_data_structures(self) -> None:
        """Inicializa estruturas de dados."""
        self.dados_fila: List[Dict[str, str]] = []
        self.layout_ativo: Optional[str] = None
        self.vars_man: Dict[str, tk.StringVar] = {}
        self.vars_seq: Dict[str, tk.StringVar] = {}
        self.tree: Optional[ttk.Treeview] = None # Treeview para a tela de layout
        self.preview_label: Optional[ctk.CTkLabel] = None
        self.lbl_contador: Optional[ctk.CTkLabel] = None

        # Atributos para o histórico
        self._df_historico = pd.DataFrame()
        self._coluna_foco = None
        self._drag_source = None
        self._ghost_label = None
        self.history_tree: Optional[ttk.Treeview] = None
        self.history_lbl_col_ativa: Optional[ctk.CTkLabel] = None
        self.history_opt_layout: Optional[ctk.CTkOptionMenu] = None
        self.history_configs: Dict[str, Dict[str, List[str]]] = {}
        self.history_visible_cols: List[str] = []
        self.history_ent_busca: Optional[ctk.CTkEntry] = None
        self.history_context_menu: Optional[tk.Menu] = None

        # Atributos para as configurações
        self.settings_opt_appearance: Optional[ctk.CTkOptionMenu] = None
        self.settings_ent_jira: Optional[ctk.CTkEntry] = None
        self.settings_ent_output: Optional[ctk.CTkEntry] = None
        self.settings_sw_abrir: Optional[ctk.CTkSwitch] = None
        self.settings_sw_imprimir: Optional[ctk.CTkSwitch] = None
        self.settings_sw_overwrite: Optional[ctk.CTkSwitch] = None

    def _load_icon(self) -> None:
        """Carrega o ícone da aplicação."""
        try:
            icon_path = get_resource_path(ICON_FILE)
            self.root.iconbitmap(icon_path)
        except Exception as e:
            logger.warning(f"Erro ao carregar ícone .ico: {e}")
            try:
                logo_path = get_resource_path(LOGO_FILE)
                self.img_icon = tk.PhotoImage(file=logo_path)
                self.root.iconphoto(False, self.img_icon)
            except Exception as inner_e:
                logger.warning(f"Erro ao carregar ícone PNG: {inner_e}")

    # ========================================================================
    # SCREEN MANAGEMENT
    # ========================================================================

    def _show_view(self, view_name: str, layout: Optional[str] = None) -> None:
        """
        Limpa o container principal e exibe a view especificada.
        """
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        if view_name == "welcome":
            self._setup_welcome_ui()
        elif view_name == "settings":
            self._setup_settings_ui()
        elif view_name == "history":
            self._setup_history_ui()
        elif view_name == "layout" and layout:
            self._setup_layout_ui(layout)
        else:
            logger.warning(f"View desconhecida ou layout ausente: {view_name}, {layout}")

        self._update_sidebar_selection(view_name, layout)

    def _update_sidebar_selection(self, view_name: str, layout: Optional[str] = None) -> None:
        """
        Atualiza o estado visual dos botões do menu lateral para refletir a view atual.
        """
        # Reseta botões e indicadores
        for btn in self._nav_buttons:
            btn.configure(fg_color="transparent", text_color=("#616161", "#858585"))
            btn._indicator.configure(fg_color="transparent")

        target = None
        if view_name == "settings":
            target = self.btn_settings
        elif view_name == "history":
            target = self.btn_history
        elif view_name == "layout":
            if layout == LAYOUT_ADM:
                target = self.btn_adm
            elif layout == LAYOUT_UNIDADE:
                target = self.btn_unidade
            elif layout == LAYOUT_PAT_ID:
                target = self.btn_pat_id
            elif layout == LAYOUT_GATI:
                target = self.btn_gati

        # Aplica o estilo VS Code ao selecionado
        if target:
            # Cores exatas do VS Code: Azul #007acc e fundo levemente mais claro no dark mode
            target.configure(fg_color=("transparent"), text_color=("#000000", "#ffffff"))
            target._indicator.configure(fg_color="#007ACC")

    def _setup_welcome_ui(self) -> None:
        """Tela de boas-vindas exibida ao abrir o app."""
        welcome_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        welcome_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(welcome_frame, text="Bem-vindo ao GlassPrinter", font=(FONT_BOLD, 24)).pack(pady=10)
        ctk.CTkLabel(welcome_frame, text="Selecione um layout no menu lateral para começar.", font=(FONT_DEFAULT, 16)).pack()
        
        # Logo central
        try:
            logo_path = get_resource_path(LOGO_FILE)
            img = Image.open(logo_path)
            # Calcula a largura proporcional para manter o aspecto original (não esticar)
            altura_alvo = 100
            largura_alvo = int(float(img.width) * (altura_alvo / float(img.height)))
            
            self.welcome_logo = ctk.CTkImage(light_image=img, dark_image=img, size=(largura_alvo, altura_alvo))
            ctk.CTkLabel(welcome_frame, image=self.welcome_logo, text="").pack(pady=30)
        except: pass

    def _setup_layout_ui(self, layout: str) -> None:
        """
        Configura a tela principal para o layout selecionado.

        Args:
            layout: Nome do layout ('adm' ou 'unidade').
        """
        if layout not in AVAILABLE_LAYOUTS:
            messagebox.showerror(
                "Erro",
                f"Layout inválido: {layout}",
            )
            return

        if layout == LAYOUT_ADM:
            self.campos_ativos = FORM_FIELDS_ADM
        elif layout == LAYOUT_UNIDADE:
            self.campos_ativos = FORM_FIELDS_UNIDADE
        elif layout == LAYOUT_PAT_ID:
            self.campos_ativos = FORM_FIELDS_PAT_ID
        elif layout == LAYOUT_GATI:
            self.campos_ativos = FORM_FIELDS_GATI
            
        self.layout_ativo = layout

        # Cores e Títulos do Header
        header_color = COLOR_HEADER_ADM if layout == LAYOUT_ADM else COLOR_HEADER_UNIDADE
        barra = ctk.CTkFrame(self.main_container, fg_color=header_color, height=40, corner_radius=0)
        barra.pack(fill="x")
        
        titulos = {
            LAYOUT_ADM: "MÓDULO ADM",
            LAYOUT_UNIDADE: "MÓDULO UNIDADE",
            LAYOUT_PAT_ID: "IDENTIFICAÇÃO DE PATRIMÔNIO (CAIXAS)",
            LAYOUT_GATI: "GERADOR DE ETIQUETAS GATI"
        }
        ctk.CTkLabel(barra, text=titulos.get(layout, "LAYOUT"), font=(FONT_BOLD, 14), 
                     text_color="white" if layout == LAYOUT_ADM else "black").pack(side="left", padx=20)

        # Container Superior (Split 50/50: Entrada vs Preview)
        top_split = ctk.CTkFrame(self.main_container, fg_color="transparent")
        top_split.pack(fill="x", padx=15, pady=(5, 0))

        # Lado Esquerdo: Abas de Entrada
        self.abas = ctk.CTkTabview(top_split, height=380)
        self.abas.pack(side="left", expand=True, fill="both", padx=(0, 5))

        if layout not in [LAYOUT_PAT_ID, LAYOUT_GATI]:
            self.tab_manual = self.abas.add(" Entrada Manual ")
            self._construir_formulario_manual()

        self.tab_lote = self.abas.add(" Importar Planilhas ")
        self._construir_area_lote()

        if layout == LAYOUT_PAT_ID:
            self.tab_sequencial = self.abas.add(" Entrada Sequencial ")
            self._construir_area_sequencial_pat_id()
        elif layout == LAYOUT_GATI:
            self.tab_gati = self.abas.add(" Sequencial GATI ")
            self._construir_area_sequencial_gati()

        # Lado Direito: Preview Panel (acima da tabela)
        self._construir_painel_preview(top_split)

        # Constrói componentes
        self._construir_tabela_resumo()
        self._construir_rodape()

    def _construir_rodape(self) -> None:
        """Cria o rodapé informativo de forma segura."""
        ctk.CTkLabel(
            self.main_container,
            text=f"GlassPrinter v{APP_VERSION} - Autoglass | Estoque: TI Corporativa",
            font=(FONT_DEFAULT, 9, "italic"),
            text_color="gray",
            fg_color="transparent"
        ).pack(side="bottom", pady=5)

    def _clear_main_container(self) -> None:
        """Limpa todos os widgets do container principal."""
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def _abrir_configuracoes(self) -> None:
        """Abre a janela de configurações independente."""
        self._show_view("settings")

    def _abrir_visualizador_historico(self) -> None:
        """Abre a janela de visualização do histórico."""
        self._show_view("history")

    # ========================================================================
    # UI CONSTRUCTION - SETTINGS
    # ========================================================================

    def _setup_settings_ui(self) -> None:
        """Constrói a interface de configurações."""
        container = ctk.CTkFrame(self.main_container, corner_radius=15)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Seção Aparência
        ctk.CTkLabel(scroll, text="Personalização", font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 5))
        
        self.settings_opt_appearance = ctk.CTkOptionMenu(scroll, values=["System", "Light", "Dark"], width=200)
        self.settings_opt_appearance.set(self.config_data.get("appearance_mode", "System"))
        ctk.CTkLabel(scroll, text="Modo de Aparência:").pack(anchor="w")
        self.settings_opt_appearance.pack(anchor="w", pady=(0, 15))

        # Seção Dados Padrão
        ctk.CTkLabel(scroll, text="Dados Padrão", font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 5))
        
        ctk.CTkLabel(scroll, text="URL Base do Jira:").pack(anchor="w")
        self.settings_ent_jira = ctk.CTkEntry(scroll, width=400)
        self.settings_ent_jira.insert(0, self.config_data.get("jira_url", JIRA_BASE_URL))
        self.settings_ent_jira.pack(anchor="w", pady=(0, 15))

        ctk.CTkLabel(scroll, text="Pasta de Saída (PDF/Histórico):").pack(anchor="w")
        path_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        path_frame.pack(fill="x", pady=(0, 15))
        
        self.settings_ent_output = ctk.CTkEntry(path_frame, width=330)
        self.settings_ent_output.insert(0, self.config_data.get("output_dir", str(get_default_output_path())))
        self.settings_ent_output.pack(side="left")
        
        ctk.CTkButton(
            path_frame, 
            text="...", 
            width=60, 
            command=self._browse_path
        ).pack(side="left", padx=5)

        # Seção Manutenção
        ctk.CTkLabel(scroll, text="Manutenção", font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 5))
        ctk.CTkButton(scroll, text="Limpar Arquivo de Histórico", fg_color="#b00020", hover_color="#800000", command=self._clear_history).pack(anchor="w", pady=5)
        ctk.CTkButton(scroll, text="Limpar PDFs 🗑️", fg_color="#b00020", hover_color="#800000", command=self._clear_pdfs).pack(anchor="w", pady=5)

        # Seção Comportamento
        ctk.CTkLabel(scroll, text="Comportamento", font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 5))
        
        self.settings_sw_abrir = ctk.CTkSwitch(scroll, text="Abrir PDF automaticamente após gerar")
        if self.config_data.get("auto_abrir_pdf", True):
            self.settings_sw_abrir.select()
        self.settings_sw_abrir.pack(anchor="w", pady=5)

        self.settings_sw_imprimir = ctk.CTkSwitch(scroll, text="Imprimir automaticamente (sem perguntar)")
        if self.config_data.get("auto_imprimir", False):
            self.settings_sw_imprimir.select()
        self.settings_sw_imprimir.pack(anchor="w", pady=5)

        self.settings_sw_overwrite = ctk.CTkSwitch(scroll, text="Sobrescrever último PDF (evita acúmulo de arquivos)")
        if self.config_data.get("overwrite_pdf", False):
            self.settings_sw_overwrite.select()
        self.settings_sw_overwrite.pack(anchor="w", pady=5)

        # Rodapé com Botões
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20, padx=10)

        ctk.CTkButton(
            btn_frame, 
            text="Salvar Alterações", 
            command=self._save_settings,
            fg_color="#1f538d",
            height=40
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            btn_frame, 
            text="Cancelar", 
            command=lambda: self._show_view("welcome"), # Volta para a tela inicial
            fg_color="#606060",
            hover_color="#454545",
            height=40
        ).pack(side="right", padx=5)

    def _save_settings(self) -> None:
        """Coleta dados da UI e salva no arquivo JSON."""
        # Carrega o arquivo atual para não perder chaves como 'history_column_order'
        current_config = {}
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    current_config = json.load(f)
            except: pass

        updates = {
            "appearance_mode": self.settings_opt_appearance.get(),
            "jira_url": self.settings_ent_jira.get(),
            "auto_abrir_pdf": self.settings_sw_abrir.get(),
            "output_dir": self.settings_ent_output.get(),
            "auto_imprimir": self.settings_sw_imprimir.get(),
            "overwrite_pdf": self.settings_sw_overwrite.get()
        }
        
        current_config.update(updates)

        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(current_config, f, indent=4, ensure_ascii=False)
            self._aplicar_configuracoes(current_config)
            self._show_view("welcome") # Volta para a tela inicial após salvar
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}")

    def _clear_history(self) -> None:
        if messagebox.askyesno("Confirmar", "Deseja realmente apagar todo o histórico de etiquetas?"):
            try:
                h_file = Path(self.settings_ent_output.get()) / HISTORY_FILE
                if h_file.exists():
                    h_file.unlink()
                    messagebox.showinfo("Sucesso", "Histórico removido!")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível limpar: {e}")

    def _browse_path(self) -> None:
        """Abre o seletor de diretórios para a pasta de saída."""
        path = filedialog.askdirectory()
        if path:
            self.settings_ent_output.delete(0, tk.END)
            self.settings_ent_output.insert(0, path)

    def _clear_pdfs(self) -> None:
        """Remove todos os arquivos PDF da pasta de saída configurada."""
        if messagebox.askyesno("Confirmar", "Deseja realmente apagar todos os arquivos PDF da pasta de saída?"):
            try:
                out_dir = Path(self.settings_ent_output.get())
                if out_dir.exists() and out_dir.is_dir():
                    pdf_files = list(out_dir.glob("*.pdf"))
                    if not pdf_files:
                        messagebox.showinfo("Aviso", "Nenhum arquivo PDF encontrado na pasta.")
                        return
                    
                    for pdf in pdf_files:
                        pdf.unlink()
                    messagebox.showinfo("Sucesso", f"{len(pdf_files)} arquivos PDF removidos!")
                else:
                    messagebox.showerror("Erro", "Pasta de saída não encontrada ou inválida.")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível limpar os PDFs: {e}")

    # ========================================================================
    # UI CONSTRUCTION - HISTORY
    # ========================================================================

    def _setup_history_ui(self) -> None:
        """Constrói a interface do visualizador de histórico."""
        # Toolbar superior
        toolbar = ctk.CTkFrame(self.main_container, height=50, corner_radius=0)
        toolbar.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(toolbar, text="Filtrar Chamado/Beneficiário:").pack(side="left", padx=(10, 5))
        self.history_ent_busca = ctk.CTkEntry(toolbar, width=200, placeholder_text="Digite para buscar...")
        self.history_ent_busca.pack(side="left", padx=5)
        self.history_ent_busca.bind("<KeyRelease>", lambda e: self._filtrar_dados_historico())

        ctk.CTkLabel(toolbar, text="Filtrar Layout:").pack(side="left", padx=(10, 5))
        self.history_opt_layout = ctk.CTkOptionMenu(
            toolbar, values=["Todos", "ADM", "UNIDADE", "PAT_ID"], width=120, command=lambda v: self._filtrar_dados_historico()
        )
        self.history_opt_layout.pack(side="left", padx=5)

        # Controles de Layout de Coluna
        ctk.CTkLabel(toolbar, text="Layout:").pack(side="left", padx=(15, 2))
        
        ctk.CTkButton(
            toolbar, text="⬅️", width=35, command=lambda: self._mover_coluna_historico(-1),
            fg_color="transparent", border_width=1
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            toolbar, text="➡️", width=35, command=lambda: self._mover_coluna_historico(1),
            fg_color="transparent", border_width=1
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            toolbar,
            text="Colunas ⚙️",
            width=100,
            command=self._abrir_seletor_colunas_historico,
            fg_color="transparent", border_width=1
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            toolbar, 
            text="Salvar Layout 💾", 
            width=110,
            command=self._salvar_layout_colunas_historico,
            fg_color="#1f538d"
        ).pack(side="left", padx=10)

        self.history_lbl_col_ativa = ctk.CTkLabel(
            toolbar, 
            text="Selecione uma coluna", 
            text_color="gray",
            font=(FONT_DEFAULT, 11, "italic")
        )
        self.history_lbl_col_ativa.pack(side="left", padx=5)

        ctk.CTkButton(
            toolbar, 
            text="Copiar p/ Excel Web", 
            fg_color=COLOR_SUCCESS,
            command=self._copiar_historico_para_clipboard,
            width=150
        ).pack(side="right", padx=10)

        ctk.CTkButton(
            toolbar, 
            text="Abrir Pasta", 
            fg_color="transparent",
            border_width=1,
            command=self._abrir_pasta_historico,
            width=100
        ).pack(side="right", padx=5)

        # Container da Tabela
        history_frame_tab = ctk.CTkFrame(self.main_container)
        history_frame_tab.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Estilo para o Treeview
        style = ttk.Style()
        style.theme_use("clam")
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#2b2b2b" if is_dark else "#ffffff"
        fg_color = "#ffffff" if is_dark else "#000000"

        style.configure("History.Treeview", 
                        background=bg_color, 
                        foreground=fg_color, 
                        fieldbackground=bg_color, 
                        rowheight=25,
                        borderwidth=1,
                        relief="solid")
        
        style.configure("Treeview.Heading", 
                        background="#3b3b3b" if is_dark else "#d0d0d0", 
                        foreground=fg_color,
                        font=(FONT_DEFAULT, 10, "bold"),
                        borderwidth=1,
                        relief="solid")

        # Colunas baseadas no save_backup do engine.py (para o histórico)
        self.colunas = [
            "layout", "chamado", "data_retirada", "patrimonio", "tecnico", 
            "beneficiario", "destino", "setor", "produto", "quantidade", 
            "forma_envio", "origem", "data_processamento"
        ]

        # Carrega ordem salva se existir
        saved_order = self.config_data.get("history_column_order")
        if saved_order and isinstance(saved_order, list):
            # Reconstrução resiliente: mantém colunas válidas e adiciona novas (se houver) no fim
            validas = [c for c in saved_order if c in self.colunas]
            faltantes = [c for c in self.colunas if c not in validas]
            self.display_cols = validas + faltantes
        else:
            self.display_cols = list(self.colunas)

        self.history_tree = ttk.Treeview(history_frame_tab, columns=self.colunas, show="headings", style="History.Treeview")
        self.history_tree["displaycolumns"] = self.display_cols

        vsb = ctk.CTkScrollbar(history_frame_tab, orientation="vertical", command=self.history_tree.yview)
        hsb = ctk.CTkScrollbar(history_frame_tab, orientation="horizontal", command=self.history_tree.xview)
        self.history_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        for col in self.colunas:
            self.history_tree.heading(col, text=col.replace("_", " ").title(),
                               command=lambda c=col: self._on_header_click_historico(c))
            self.history_tree.column(col, width=160, minwidth=120, anchor="center", stretch=False)

        self.history_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        history_frame_tab.grid_rowconfigure(0, weight=1)
        history_frame_tab.grid_columnconfigure(0, weight=1)

        # Cores para o efeito zebra no histórico
        row_alt_color = "#323232" if is_dark else "#f9f9f9"
        self.history_tree.tag_configure('oddrow', background=bg_color)
        self.history_tree.tag_configure('evenrow', background=row_alt_color)

        # Eventos para arrastar e soltar colunas
        self.history_tree.bind("<ButtonPress-1>", self._on_drag_start_historico, add="+")
        self.history_tree.bind("<ButtonRelease-1>", self._on_drag_stop_historico, add="+")
        self.history_tree.bind("<B1-Motion>", self._on_drag_motion_historico, add="+")
        
        # Menu de contexto (botão direito) para re-impressão
        self.history_context_menu = tk.Menu(self.history_tree, tearoff=0)
        self.history_context_menu.add_command(
            label="Re-imprimir Selecionados 🖨️",
            command=self._reimprimir_selecionados_historico
        )
        self.history_tree.bind("<Button-3>", self._show_context_menu_historico)

        self._carregar_dados_historico()

    def _on_drag_start_historico(self, event: tk.Event) -> None:
        """Detecta o início do arraste de uma coluna."""
        region = self.history_tree.identify_region(event.x, event.y)
        if region == "heading":
            col_id = self.history_tree.identify_column(event.x)  # Retorna algo como "#1"
            try:
                logical_idx = int(col_id[1:]) - 1
                self._drag_source = self.display_cols[logical_idx]
                
                # Efeito visual de "desprender": cria um label flutuante
                header_text = self.history_tree.heading(self._drag_source, "text")
                self._ghost_label = ctk.CTkLabel(
                    self.main_container, # Coloca no main_container para flutuar sobre tudo
                    text=header_text,
                    fg_color=COLOR_PRIMARY_BLUE,
                    text_color="white",
                    corner_radius=6,
                    font=(FONT_DEFAULT, 10, "bold"),
                    width=120,
                    height=28
                )
                # Ajusta a posição para ser relativa à janela principal
                x_root = self.history_tree.winfo_rootx() + event.x
                y_root = self.history_tree.winfo_rooty() + event.y
                self._ghost_label.place(x=x_root - self.root.winfo_rootx(), y=y_root - self.root.winfo_rooty() - 20)
                self.history_tree.configure(cursor="hand2")
                
            except (ValueError, IndexError):
                self._drag_source = None

    def _on_drag_motion_historico(self, event: tk.Event) -> None:
        """Atualiza a posição do elemento flutuante enquanto o mouse se move."""
        if self._ghost_label:
            # Faz o label seguir o mouse com um pequeno offset para não ficar sob o cursor
            x_root = self.history_tree.winfo_rootx() + event.x
            y_root = self.history_tree.winfo_rooty() + event.y
            self._ghost_label.place(x=x_root - self.root.winfo_rootx(), y=y_root - self.root.winfo_rooty() - 20)

    def _on_drag_stop_historico(self, event: tk.Event) -> None:
        """Finaliza o arraste e reposiciona a coluna."""
        if self._ghost_label:
            self._ghost_label.destroy()
            self._ghost_label = None
            self.history_tree.configure(cursor="")

        if not self._drag_source:
            return

        region = self.history_tree.identify_region(event.x, event.y)
        if region == "heading":
            col_id = self.history_tree.identify_column(event.x)
            try:
                # Identifica a coluna correta baseada no que está visível na tela no momento
                visiveis = list(self.history_tree["displaycolumns"])
                logical_idx = int(col_id[1:]) - 1
                target_col = visiveis[logical_idx]

                if target_col != self._drag_source:
                    # Atualiza a visualização imediata
                    visiveis.insert(visiveis.index(target_col), visiveis.pop(visiveis.index(self._drag_source)))
                    self.history_tree["displaycolumns"] = visiveis
                    
                    # Atualiza a ordem na lista global mantendo as colunas ocultas em suas posições
                    self.display_cols.insert(self.display_cols.index(target_col), self.display_cols.pop(self.display_cols.index(self._drag_source)))
                    
                    # Sincroniza a visibilidade global com a nova ordem master
                    self.history_visible_cols = [c for c in self.display_cols if c in self.history_visible_cols]
                    self._on_header_click_historico(self._drag_source)  # Atualiza o foco visual
            except (ValueError, IndexError, ValueError):
                pass
        
        self._drag_source = None

    def _on_header_click_historico(self, col: str) -> None:
        """Define a coluna em foco e executa a ordenação."""
        self._coluna_foco = col
        nome_limpo = col.replace("_", " ").title()
        self.history_lbl_col_ativa.configure(text=f"Coluna: {nome_limpo}", text_color=COLOR_PRIMARY_BLUE)
        self._sort_column_historico(self.history_tree, col, False)

    def _mover_coluna_historico(self, direcao: int) -> None:
        """Move a coluna selecionada para esquerda (-1) ou direita (1)."""
        if not self._coluna_foco:
            messagebox.showinfo("Aviso", "Clique no título de uma coluna para selecioná-la primeiro.")
            return

        cols = list(self.history_tree["displaycolumns"])
        try:
            idx = cols.index(self._coluna_foco)
            new_idx = idx + direcao

            if 0 <= new_idx < len(cols):
                alvo = cols[new_idx]
                # Move visualmente
                cols[idx], cols[new_idx] = cols[new_idx], cols[idx]
                self.history_tree["displaycolumns"] = cols
                # Move na lista global para persistir
                self.display_cols.insert(self.display_cols.index(alvo), self.display_cols.pop(self.display_cols.index(self._coluna_foco)))
        except ValueError: pass

    def _salvar_layout_colunas_historico(self) -> None:
        """Salva a ordem atual das colunas no arquivo de configurações."""
        try:
            # 1. Identifica qual filtro está ativo
            active_filter = self.history_opt_layout.get().lower() if self.history_opt_layout else "todos"
            
            # 2. Atualiza a configuração do layout ATUAL (ordem e visibilidade)
            visiveis = list(self.history_tree["displaycolumns"])
            total_permitidas = self.keys_by_layout.get(active_filter, self.colunas)
            ocultas = [c for c in total_permitidas if c not in visiveis]
            
            # A ordem salva será: primeiro as que o usuário deixou visíveis, depois as ocultas
            nova_ordem = visiveis + ocultas
            self.history_configs[active_filter] = {
                "order": nova_ordem,
                "visible": visiveis
            }

            # 3. Prepara o dicionário completo para salvar no JSON
            self.config_data["history_layouts_config"] = self.history_configs

            # 4. Salva larguras das colunas
            widths = {col: self.history_tree.column(col, "width") for col in self.colunas}
            self.config_data["history_column_widths"] = widths
            
            # Localiza o caminho do settings.json
            if getattr(sys, 'frozen', False):
                base = os.path.dirname(sys.executable)
            else:
                base = os.path.dirname(os.path.abspath(__file__))
            
            path = os.path.join(base, SETTINGS_FILE)
            
            # Abre as configurações atuais para não sobrescrever outros campos alterados fora da main
            current_config = {}
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    current_config = json.load(f)
            
            current_config["history_layouts_config"] = self.history_configs
            current_config["history_column_widths"] = self.config_data["history_column_widths"]
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(current_config, f, indent=4, ensure_ascii=False)
                
            messagebox.showinfo("Sucesso", "Layout de colunas salvo com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao salvar layout de colunas: {e}")
            messagebox.showerror("Erro", f"Não foi possível salvar o layout:\n{e}")

    def _abrir_seletor_colunas_historico(self) -> None:
        """Abre uma janela flutuante com checkboxes para ocultar/exibir colunas (Estilo JSM)."""
        top = ctk.CTkToplevel(self.root)
        top.title("Configurar Colunas")
        top.attributes("-topmost", True)
        top.geometry("350x550")
        top.resizable(False, False)
        
        # Centraliza o popup em relação à janela principal
        top.update_idletasks()
        rw, rh = self.root.winfo_width(), self.root.winfo_height()
        rx, ry = self.root.winfo_rootx(), self.root.winfo_rooty()
        top.geometry(f"+{rx + (rw-350)//2}+{ry + (rh-550)//2}")

        ctk.CTkLabel(top, text="Selecione as colunas visíveis:", font=(FONT_BOLD, 14)).pack(pady=15)
        active_filter = self.history_opt_layout.get().lower() if self.history_opt_layout else "todos"
        config = self.history_configs.get(active_filter, self.history_configs.get("todos", {}))

        # Frame para botões de atalho (Marcar/Desmarcar Tudo)
        shortcut_frame = ctk.CTkFrame(top, fg_color="transparent")
        shortcut_frame.pack(fill="x", padx=20, pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(top)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        # Pega o que está visível na Treeview agora
        visiveis_agora = list(self.history_tree["displaycolumns"])
        
        vars_checkbox = {}
        for col in config.get("order", []):
            label = col.replace("_", " ").title()
            var = tk.BooleanVar(value=col in visiveis_agora)
            cb = ctk.CTkCheckBox(scroll, text=label, variable=var, font=(FONT_DEFAULT, 12))
            cb.pack(anchor="w", pady=4, padx=10)
            vars_checkbox[col] = var

        def toggle_all(state: bool):
            for var in vars_checkbox.values():
                var.set(state)

        # Adiciona botões de atalho no topo da lista
        ctk.CTkButton(shortcut_frame, text="Marcar Tudo", command=lambda: toggle_all(True), width=100, height=24, font=(FONT_DEFAULT, 11)).pack(side="left")
        ctk.CTkButton(shortcut_frame, text="Desmarcar Tudo", command=lambda: toggle_all(False), width=110, height=24, font=(FONT_DEFAULT, 11), fg_color="#606060").pack(side="left", padx=10)

        def aplicar():
            # Atualiza apenas o layout ativo
            order = config.get("order") or self.colunas
            selecionadas = [c for c in order if vars_checkbox.get(c) and vars_checkbox[c].get()]
            
            if not selecionadas:
                messagebox.showwarning("Aviso", "Pelo menos uma coluna deve estar visível.")
                return
            
            self.history_configs[active_filter]["visible"] = selecionadas
            self.history_tree["displaycolumns"] = selecionadas
            top.destroy()

        btn_frame = ctk.CTkFrame(top, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(btn_frame, text="Confirmar", command=aplicar, width=120).pack(side="right", padx=20)
        ctk.CTkButton(btn_frame, text="Cancelar", command=top.destroy, fg_color="#606060", width=100).pack(side="right")

    def _show_context_menu_historico(self, event: tk.Event) -> None:
        """Exibe o menu de contexto ao clicar com o botão direito."""
        self.history_context_menu.post(event.x_root, event.y_root)

    def _reimprimir_selecionados_historico(self) -> None:
        """Gera um PDF temporário e imprime os registros selecionados no histórico."""
        items = self.history_tree.selection()
        if not items:
            messagebox.showwarning("Aviso", "Selecione as etiquetas que deseja re-imprimir.")
            return

        # 1. Tenta identificar o layout automaticamente a partir da seleção
        layouts_encontrados = set()
        for item in items:
            l = str(self.history_tree.set(item, "layout")).lower()
            if l in [LAYOUT_ADM, LAYOUT_UNIDADE, LAYOUT_PAT_ID]:
                layouts_encontrados.add(l)
        
        # 2. Determina o layout a ser usado (Auto ou Diálogo)
        if len(layouts_encontrados) == 1:
            layout_nome = list(layouts_encontrados)[0]
        else:
            # Se houver layouts mistos ou não identificados, pergunta ao usuário
            dialog = LogoInputDialog(
                master=self.root,
                title="Selecionar Layout",
                text="Qual modelo de etiqueta deve ser usado para re-impressão?",
                logo_path=get_resource_path(LOGO_TYPE_FILE),
                icon_path=get_resource_path(ICON_FILE),
                options=["ADM", "UNIDADE", "PAT ID"]
            )
            layout_sel = dialog.get_input()
            if not layout_sel: return
            
            if "ADM" in layout_sel: layout_nome = LAYOUT_ADM
            elif "UNIDADE" in layout_sel: layout_nome = LAYOUT_UNIDADE
            else: layout_nome = LAYOUT_PAT_ID

        records_to_print = []
        for item in items:
            row_data = {}
            for col_id in self.colunas: # type: ignore
                val = self.history_tree.set(item, col_id)
                # Mapeia de volta beneficiario -> solicitante para compatibilidade com o engine
                key = "solicitante" if col_id == "beneficiario" else col_id
                row_data[key] = val
            records_to_print.append(row_data)

        try:
            # Gera PDF no diretório configurado
            pdf_path = self.pdf_engine.generate_pdf(
                records_to_print, # type: ignore
                layout_nome, 
                overwrite=self.config_data.get("overwrite_pdf", False)
            )
            
            # Envia para impressão
            if self.print_engine.print_file(pdf_path):
                messagebox.showinfo("Sucesso", f"Enviado {len(records_to_print)} etiquetas para a impressora padrão.")
            else:
                self.print_engine.open_file(pdf_path)
        except Exception as e:
            logger.error(f"Erro ao re-imprimir do histórico: {e}")
            messagebox.showerror("Erro", f"Falha ao gerar re-impressão:\n{e}")

    def _sort_column_historico(self, tv: ttk.Treeview, col: str, reverse: bool) -> None:
        """Ordena o conteúdo da Treeview ao clicar no cabeçalho."""
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        
        try:
            l.sort(key=lambda t: float(t[0]) if t[0] else 0, reverse=reverse)
        except ValueError:
            l.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)

        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            tv.item(k, tags=(tag,))

        # Atualiza o comando para permitir alternar reverse no próximo clique (para o histórico)
        tv.heading(col, command=lambda: (self._on_header_click_historico(col), self._sort_column_historico(tv, col, not reverse)))

    def _carregar_dados_historico(self) -> None:
        """Lê o arquivo CSV e carrega na tabela."""
        output_dir = Path(self.config_data.get("output_dir", str(get_default_output_path())))
        layout_filtro = self.history_opt_layout.get().lower() if self.history_opt_layout else "todos"
        
        try:
            dfs = []
            
            # 1. Sempre tenta carregar o arquivo legado para não perder dados antigos
            legacy_path = output_dir / "historico_etiquetas.csv"
            if legacy_path.exists():
                df_legacy = pd.read_csv(legacy_path, sep=CSV_SEPARATOR, encoding=CSV_ENCODING, dtype=str)
                dfs.append(df_legacy)

            # 2. Determina quais arquivos novos carregar baseado no filtro
            if layout_filtro == "todos":
                files_to_load = list(HISTORY_FILES.values())
            else:
                files_to_load = [HISTORY_FILES.get(layout_filtro, "")]

            for filename in files_to_load:
                f_path = output_dir / filename
                if f_path.exists():
                    df_temp = pd.read_csv(f_path, sep=CSV_SEPARATOR, encoding=CSV_ENCODING, dtype=str)
                    dfs.append(df_temp)
            
            if not dfs:
                self._df_historico = pd.DataFrame(columns=self.colunas)
            else:
                # 3. Une todos os arquivos e padroniza as colunas (solicitante -> beneficiario)
                self._df_historico = pd.concat(dfs, ignore_index=True)
                
                if "solicitante" in self._df_historico.columns:
                    # Preenche beneficiario com dados de solicitante onde estiver vazio
                    if "beneficiario" not in self._df_historico.columns:
                        self._df_historico["beneficiario"] = ""
                    
                    self._df_historico["beneficiario"] = self._df_historico["beneficiario"].fillna(self._df_historico["solicitante"])
                
                # Garante a ordem correta das colunas definida em self.colunas
                self._df_historico = self._df_historico.reindex(columns=self.colunas, fill_value="")
            
            # 4. Aplica os filtros de visualização
            self._filtrar_dados_historico()
            
        except Exception as e:
            logger.error(f"Erro ao carregar arquivos de histórico: {e}")

    def _atualizar_view_historico(self, df: pd.DataFrame) -> None:
        if not self.history_tree or not self.history_tree.winfo_exists():
            return
            
        self.history_tree.delete(*self.history_tree.get_children())

        # Pegamos a definição interna de colunas do Treeview para garantir o mapeamento nominal
        identificadores_colunas = self.history_tree["columns"]

        # Iteramos pelo DataFrame (invertido para os mais recentes aparecerem no topo)
        for i, (_, row) in enumerate(df.iloc[::-1].iterrows()):
            # Busca inteligente: criamos a lista de valores baseada no NOME da coluna
            # Se a coluna não existir no registro atual, preenchemos com vazio
            valores_mapeados = [str(row.get(col_id, "")) for col_id in identificadores_colunas]
            
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.history_tree.insert("", "end", values=valores_mapeados, tags=(tag,))

    def _filtrar_dados_historico(self) -> None:
        if self._df_historico.empty:
            return

        termo = self.history_ent_busca.get().lower()
        layout_filtro = self.history_opt_layout.get().lower()

        # 1. Ajustar colunas visíveis de acordo com o layout selecionado
        if self.history_tree:
            # Busca a configuração independente para este filtro
            config = (
                self.history_configs.get(layout_filtro)
                or self.history_configs.get("todos")
                or {}
            )
            
            # Aplica a ordem e visibilidade salva especificamente para este modo
            visible = config.get("visible") or config.get("order") or self.display_cols
            self.history_tree["displaycolumns"] = visible

        # 2. Filtrar os dados no DataFrame
        df_filtrado = self._df_historico.copy()

        # Filtro por layout
        if layout_filtro != "todos":
            if 'layout' in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado['layout'].fillna("").str.lower() == layout_filtro]

        # Filtro por texto de busca
        if termo != "":
            mask = (
                df_filtrado['chamado'].fillna("").str.lower().str.contains(termo, na=False) |
                df_filtrado['beneficiario'].fillna("").str.lower().str.contains(termo, na=False) |
                df_filtrado['patrimonio'].fillna("").str.lower().str.contains(termo, na=False) |
                df_filtrado['produto'].fillna("").str.lower().str.contains(termo, na=False)
            )
            df_filtrado = df_filtrado[mask]

        self._atualizar_view_historico(df_filtrado)

    def _copiar_historico_para_clipboard(self) -> None:
        """Copia os dados selecionados na tabela no formato aceito pelo Excel Web."""
        if self._df_historico.empty or not self.history_tree:
            return

        # Pega apenas os itens que o usuário selecionou manualmente (IDs)
        items = self.history_tree.selection()
        
        if not items:
            messagebox.showwarning("Aviso", "Selecione os itens que deseja copiar no Histórico.")
            return

        linhas = []
        # Obtém a ordem VISUAL das colunas
        ordem_visual = list(self.history_tree["displaycolumns"])
        
        # Dados
        for item in items:
            # Pega o dicionário de valores da linha (mapeado pelo ID da coluna) # type: ignore
            item_values = []
            for col_id in ordem_visual:
                val = self.history_tree.set(item, col_id) # type: ignore
                item_values.append(str(val))
            
            linhas.append("\t".join(item_values))

        corpo_texto = "\n".join(linhas)
        
        self.root.clipboard_clear()
        self.root.clipboard_append(corpo_texto)
        messagebox.showinfo("Copiado", f"{len(items)} registros copiados para a área de transferência.\n\nAgora basta colar (Ctrl+V) no Excel Web.")
    def _abrir_pasta_historico(self) -> None:
        path = self.config_data.get("output_dir", str(get_default_output_path()))
        if os.path.exists(path):
            os.startfile(path)

    # ========================================================================
    # UI CONSTRUCTION
    # ========================================================================

    def _construir_area_sequencial_gati(self) -> None:
        """Cria a interface para entrada sequencial GATI."""
        container = ctk.CTkFrame(self.tab_gati, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        frame = ctk.CTkFrame(container)
        frame.pack(padx=20, pady=10)
        
        self.vars_gati = {"inicio": tk.StringVar(), "fim": tk.StringVar()}
        ctk.CTkLabel(frame, text="GATI Inicial (Ex: N123456):").grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkEntry(frame, textvariable=self.vars_gati["inicio"], width=200).grid(row=0, column=1, padx=10, pady=10)
        ctk.CTkLabel(frame, text="GATI Final (Ex: N123459):").grid(row=1, column=0, padx=10, pady=10)
        ctk.CTkEntry(frame, textvariable=self.vars_gati["fim"], width=200).grid(row=1, column=1, padx=10, pady=10)
        
        ctk.CTkButton(container, text="Gerar Sequência GATI", command=self._adicionar_sequencia_gati, fg_color=COLOR_SUCCESS).pack(pady=10)

    def _adicionar_sequencia_gati(self) -> None:
        import re
        inicio_raw = self.vars_gati["inicio"].get().strip().upper()
        fim_raw = self.vars_gati["fim"].get().strip().upper()
        
        pattern = r"^([^0-9]+)([0-9]+)$"
        match_i, match_f = re.match(pattern, inicio_raw), re.match(pattern, fim_raw)
        
        if not match_i or not match_f or match_i.group(1) != match_f.group(1):
            messagebox.showerror("Erro", "Formato inválido ou prefixos diferentes.")
            return
            
        prefix, start_num, end_num = match_i.group(1), int(match_i.group(2)), int(match_f.group(2))
        padding = len(match_i.group(2))
        
        for i in range(start_num, end_num + 1):
            reg = {"produto": "GATI", "patrimonio": f"{prefix}{str(i).zfill(padding)}", "origem": "Gerador GATI"}
            self.dados_fila.append(reg)
            self._adicionar_na_tabela(reg)
        self._atualizar_contador()
        self.vars_gati["inicio"].set(""); self.vars_gati["fim"].set("")

    def _construir_formulario_manual(self) -> None:
        """Cria os widgets manuais centralizados e sem o campo arquivo."""
        container_central = ctk.CTkFrame(self.tab_manual, fg_color="transparent")
        container_central.place(relx=0.5, rely=0.5, anchor="center")

        frame_manual = ctk.CTkFrame(container_central)
        frame_manual.pack(fill="x", padx=15, pady=10)

        # Filtra o campo 'origem' (Arquivo)
        campos_para_exibir = [c for c in self.campos_ativos if c[1] != "origem"]

        self.vars_man = {}
        for index, (label, chave) in enumerate(campos_para_exibir):
            row, col = divmod(index, 2)
            ctk.CTkLabel(frame_manual, text=f"{label}:").grid(
                row=row,
                column=col * 2,
                padx=5,
                pady=5,
            )

            valor_inicial = "1" if chave == "quantidade" else ""
            variavel = tk.StringVar(value=valor_inicial)
            ctk.CTkEntry(frame_manual, textvariable=variavel, width=250).grid(
                row=row,
                column=col * 2 + 1,
                padx=5,
                pady=5,
            )
            self.vars_man[chave] = variavel

        ctk.CTkButton(
            container_central,
            text="Adicionar",
            command=self.add_manual,
        ).pack(pady=5)

    def _construir_area_lote(self) -> None:
        """Desenha o painel de importação por planilha."""
        frame_lote = ctk.CTkFrame(self.tab_lote)
        frame_lote.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkButton(
            frame_lote,
            text="Selecionar Múltiplas Planilhas",
            command=self.importar_lote,
            width=300,
            height=50,
        ).pack(pady=20)

    def _construir_tabela_resumo(self) -> None:
        """Monta a tabela de conferência de registros antes de gerar o PDF."""
        colunas = [campo for _, campo in self.campos_ativos]

        # Frame da Tabela
        frame_tabela = ctk.CTkFrame(self.main_container)
        frame_tabela.pack(fill="both", expand=True, padx=15, pady=10)

        vsb = ctk.CTkScrollbar(frame_tabela, orientation="vertical")
        hsb = ctk.CTkScrollbar(frame_tabela, orientation="horizontal")

        self.tree = ttk.Treeview(
            frame_tabela,
            columns=colunas,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        # Atalho para edição rápida do patrimônio ao clicar duas vezes
        self.tree.bind("<Double-1>", self._editar_registro_rapido)
        self.tree.bind("<<TreeviewSelect>>", self._atualizar_preview_evento)

        vsb.configure(command=self.tree.yview)
        hsb.configure(command=self.tree.xview)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        frame_tabela.grid_rowconfigure(0, weight=1)
        frame_tabela.grid_columnconfigure(0, weight=1)

        # Cores para o efeito zebra (demarcação horizontal)
        is_dark = ctk.get_appearance_mode() == "Dark" or (ctk.get_appearance_mode() == "System" and ctk.ThemeManager.theme["CTk"]["fg_color"][1].startswith("#"))
        bg_color = "#2b2b2b" if is_dark else "#ffffff"
        row_alt_color = "#323232" if is_dark else "#f9f9f9"
        self.tree.tag_configure('oddrow', background=bg_color)
        self.tree.tag_configure('evenrow', background=row_alt_color)

        for nome, campo in self.campos_ativos:
            # Cabeçalhos sempre centralizados (Padrão Excel)
            self.tree.heading(campo, text=nome, anchor="center",
                            command=lambda c=campo: self._sort_column(self.tree, c, False))
            
            # Alinhamento: Centralizado para dados curtos/números, esquerda para textos longos
            align = "center" if campo in ["chamado", "quantidade", "patrimonio", "destino"] else "w"
            # stretch=False permite que as colunas mantenham o tamanho e a rolagem lateral funcione
            self.tree.column(campo, width=160, minwidth=120, anchor=align, stretch=False)

        # Contador de itens na lista
        self.lbl_contador = ctk.CTkLabel(
            self.main_container,
            text="Total de itens na lista: 0",
            font=(FONT_DEFAULT, 12, "bold"),
            text_color=COLOR_PRIMARY_BLUE
        )
        self.lbl_contador.pack(pady=(2, 0))

        # Frame para os botões de ação (Exportar e Limpar Lista)
        button_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        button_frame.pack(pady=10)

        ctk.CTkButton(
            button_frame,
            text="Limpar Lista",
            fg_color="#b00020", # Cor vermelha para indicar ação de limpeza/perigo
            hover_color="#800000",
            font=(FONT_DEFAULT, 12, "bold"),
            command=self._limpar_lista_confirmacao,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Exportar",
            fg_color=COLOR_SUCCESS,
            font=(FONT_DEFAULT, 12, "bold"),
            command=self.gerar_pdf,
        ).pack(side="left", padx=5)

    def _construir_painel_preview(self, parent: ctk.CTkFrame) -> None:
        """Constrói o painel de visualização 1:1 ao lado das abas."""
        preview_container = ctk.CTkFrame(parent, height=380)
        preview_container.pack(side="left", expand=True, fill="both", padx=(5, 0), pady=(10, 0))
        preview_container.pack_propagate(False)

        ctk.CTkLabel(preview_container, text="PRÉ-VISUALIZAÇÃO", font=(FONT_BOLD, 12)).pack(pady=10)
        
        self.preview_canvas_frame = ctk.CTkFrame(preview_container, fg_color=("#dbdbdb", "#1a1a1a"), corner_radius=8)
        self.preview_canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.preview_label = ctk.CTkLabel(self.preview_canvas_frame, text="Selecione um item\npara visualizar", text_color="gray")
        self.preview_label.place(relx=0.5, rely=0.5, anchor="center")

    def _atualizar_preview_evento(self, event: Optional[tk.Event] = None) -> None:
        """Captura o evento de seleção e atualiza a imagem de preview."""
        if not self.tree: return
        
        selected = self.tree.selection()
        if not selected: return
        
        # Pega os dados do primeiro item selecionado
        item_id = selected[0]
        index = self.tree.index(item_id)
        
        if index < len(self.dados_fila):
            registro = self.dados_fila[index]
            self._renderizar_preview(registro)

    def _renderizar_preview(self, registro: Dict[str, str]) -> None:
        """Renderiza a imagem técnica da etiqueta no painel lateral."""
        if not self.layout_ativo: return
        img = self.pdf_engine.get_preview_image(registro, self.layout_ativo)
        if img and self.preview_label:
            # Escala Real 1:1 baseada em 96 DPI
            size_pts = LABEL_SIZE_PAT_ID if self.layout_ativo in [LAYOUT_PAT_ID, LAYOUT_GATI] else LABEL_SIZE
            px_w = int(size_pts[0] * (96 / 72))
            px_h = int(size_pts[1] * (96 / 72))
            
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(px_w, px_h))
            self.preview_label.configure(image=ctk_img, text="")
            self.preview_label.image = ctk_img # Keep reference

    def _construir_area_sequencial_pat_id(self) -> None:
        """Cria a interface para entrada sequencial de patrimônios."""
        # Container centralizado para alinhar com o padrão do app
        container_central = ctk.CTkFrame(self.tab_sequencial, fg_color="transparent")
        container_central.place(relx=0.5, rely=0.5, anchor="center")

        frame_seq = ctk.CTkFrame(container_central)
        frame_seq.pack(fill="x", padx=15, pady=10)

        self.vars_seq = {
            "produto": tk.StringVar(value=PAT_ID_EQUIPMENT_TYPES[0]),
            "inicio": tk.StringVar(),
            "fim": tk.StringVar()
        }

        # Grid layout para os campos de sequência
        ctk.CTkLabel(frame_seq, text="Produto:").grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkEntry(frame_seq, textvariable=self.vars_seq["produto"], width=300, placeholder_text="Digite o nome do equipamento...").grid(row=0, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(frame_seq, text="Patrimônio Inicial:").grid(row=1, column=0, padx=5, pady=5)
        ctk.CTkEntry(frame_seq, textvariable=self.vars_seq["inicio"], width=180, placeholder_text="Ex: 175010").grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_seq, text="Patrimônio Final:").grid(row=1, column=2, padx=5, pady=5)
        ctk.CTkEntry(frame_seq, textvariable=self.vars_seq["fim"], width=180, placeholder_text="Ex: 175020").grid(row=1, column=3, padx=5, pady=5)

        ctk.CTkButton(
            container_central,
            text="Gerar e Adicionar Sequência à Lista",
            command=self._adicionar_sequencia_pat_id,
            fg_color=COLOR_PRIMARY_BLUE
        ).pack(pady=10)

    def _adicionar_sequencia_pat_id(self) -> None:
        """Gera a sequência de patrimônios e adiciona à fila de impressão."""
        produto = self.vars_seq["produto"].get().strip()
        inicio_str = self.vars_seq["inicio"].get().strip()
        fim_str = self.vars_seq["fim"].get().strip()

        if not produto or not inicio_str or not fim_str:
            messagebox.showwarning("Aviso", "Produto e o intervalo de patrimônio são obrigatórios.")
            return

        try:
            inicio_val = int(inicio_str)
            fim_val = int(fim_str)
            
            if inicio_val > fim_val:
                messagebox.showwarning("Aviso", "O patrimônio inicial não pode ser maior que o final.")
                return

            # Preservar o formato de zeros à esquerda se o usuário digitou (ex: 00123)
            padding = len(inicio_str)
            
            count = 0
            for i in range(inicio_val, fim_val + 1):
                pat_str = str(i).zfill(padding)
                registro = {
                    "produto": produto,
                    "patrimonio": pat_str,
                    "origem": "Entrada Sequencial"
                }
                self.dados_fila.append(registro)
                self._adicionar_na_tabela(registro)
                count += 1
            
            self._atualizar_contador()
            messagebox.showinfo("Sucesso", f"{count} etiquetas de {produto} adicionadas com sucesso!")
            
            # Limpa campos de patrimônio para facilitar a próxima sequência
            self.vars_seq["inicio"].set("")
            self.vars_seq["fim"].set("")
            
        except ValueError:
            messagebox.showerror("Erro", "Os campos de patrimônio devem conter apenas números para gerar a sequência.")

    def _limpar_lista_confirmacao(self) -> None:
        """Pede confirmação antes de limpar a lista de registros importados."""
        if messagebox.askyesno("Confirmar Limpeza", "Tem certeza que deseja limpar a lista de registros? Todos os itens serão removidos da tabela."):
            self._limpar_dados_layout()
    def _sort_column(self, tv: ttk.Treeview, col: str, reverse: bool) -> None:
        """Ordena o conteúdo da Treeview ao clicar no cabeçalho."""
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        
        try:
            l.sort(key=lambda t: float(t[0]) if t[0] else 0, reverse=reverse)
        except ValueError:
            l.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)

        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            tv.item(k, tags=(tag,))

        tv.heading(col, command=lambda: self._sort_column(tv, col, not reverse))

    # ========================================================================
    # DATA ENTRY AND VALIDATION
    # ========================================================================

    def add_manual(self) -> None:
        """
        Adiciona um registro manual à lista e limpa os campos de entrada.

        Valida campos obrigatórios antes de adicionar.
        """
        registro = {campo: variavel.get() for campo, variavel in self.vars_man.items()}

        try:
            self._validate_record(registro)
            self.dados_fila.append(registro)
            self._adicionar_na_tabela(registro)
            self._atualizar_contador()
            self._reset_manual_form()
            logger.info(f"Registro manual adicionado: {registro.get('chamado')}")
        except ValidationError as e:
            messagebox.showwarning(MESSAGES["incomplete_data"], str(e))

    def _validate_record(self, registro: Dict[str, str]) -> None:
        """
        Valida um registro.

        Args:
            registro: Dicionário com os dados do registro.

        Raises:
            ValidationError: Se o registro não passar na validação.
        """
        # Obtém apenas as chaves dos campos que estão ativos no formulário atual
        chaves_ativas = [campo[1] for campo in self.campos_ativos]
        
        for field in REQUIRED_FIELDS:
            # Só valida se o campo obrigatório for um dos campos visíveis no layout atual
            if field in chaves_ativas and (not registro.get(field) or not str(registro.get(field)).strip()):
                raise ValidationError(MESSAGES["incomplete_data_msg"])

    def _adicionar_na_tabela(self, registro: Dict[str, str]) -> None:
        """
        Insere um registro na TreeView de conferência.

        Args:
            registro: Dicionário com os dados do registro.
        """
        if self.tree is None:
            return

        valores = [registro.get(campo, "") for _, campo in self.campos_ativos]
        
        # Aplica tags alternadas para efeito de demarcação de linhas
        count = len(self.tree.get_children())
        tag = 'evenrow' if count % 2 == 0 else 'oddrow'
        self.tree.insert("", "end", values=valores, tags=(tag,))

    def _editar_registro_rapido(self, event) -> None:
        """Abre um diálogo para editar campos permitidos ao dar duplo clique em uma célula."""
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item_id or not column:
            return

        index = self.tree.index(item_id)
        if index >= len(self.dados_fila):
            return

        # Mapeia a coluna clicada para a chave do campo
        try:
            col_idx = int(column.replace("#", "")) - 1
            label_campo, chave = self.campos_ativos[col_idx]
        except (ValueError, IndexError):
            return

        registro_atual = self.dados_fila[index]
        chamado = registro_atual.get("chamado", "Desconhecido")
        options = None

        if chave == "forma_envio":
            options = ["LOGÍSTICA / CARRETA", "SEDEX"]
            text = f"Selecione a Forma de Envio para {chamado}:"
        else:
            text = f"Digite o novo valor para {label_campo} (Chamado {chamado}):"

        dialog = LogoInputDialog(
            master=self.root,
            title="Edição Rápida",
            text=text,
            logo_path=get_resource_path(LOGO_TYPE_FILE),
            icon_path=get_resource_path(ICON_FILE),
            options=options
        )
        novo_valor = dialog.get_input()

        if novo_valor is not None:
            self.dados_fila[index][chave] = novo_valor.strip()
            
            valores = list(self.tree.item(item_id, "values"))
            valores[col_idx] = novo_valor.strip()
            
            self.tree.item(item_id, values=valores)
            logger.info(f"Campo {chave} do chamado {chamado} atualizado: {novo_valor}")

    def _reset_manual_form(self) -> None:
        """Reseta os campos do formulário manual."""
        for chave, variavel in self.vars_man.items():
            if chave == "quantidade":
                variavel.set("1")
            elif chave == "forma_envio":
                variavel.set("LOGÍSTICA / CARRETA")
            else:
                variavel.set("")

    # ========================================================================
    # BATCH IMPORT (AGORA AUTOMÁTICO)
    # ========================================================================

    def importar_lote(self) -> None:
        """
        Importa planilhas automaticamente usando o motor de mapeamento interno,
        eliminando a necessidade de intervenção do usuário.
        
        Modo Power Query: arquivos de Kit Promovido, Kit Novo ou Solicitar Equipamento
        são processados pelo novo transformador, mesmo que apenas um ou dois arquivos
        sejam selecionados. Arquivos genéricos também são aceitos.
        """
        arquivos = filedialog.askopenfilenames(
            title="Selecionar Planilhas (Power Query ou genéricos)",
            filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv"), ("Excel", "*.xlsx *.xls"), ("CSV", "*.csv")]
        )

        if not arquivos:
            return

        try:
            # 1. Chama o motor automático que já contém o SMART_MAPPING e as regras de TI
            # O engine.importar_e_consolidar já retorna a lista de dicionários pronta
            novos_registros = self.pdf_engine.importar_e_consolidar(list(arquivos))
            
            if not novos_registros:
                messagebox.showwarning("Aviso", "Nenhum dado válido encontrado após os filtros (Azular/MG09).")
                return

            # 2. Adiciona os novos registros à fila global e atualiza a tabela na tela
            for registro in novos_registros:
                # Opcional: Validar se o registro já existe para evitar duplicatas
                self.dados_fila.append(registro)
                self._adicionar_na_tabela(registro)
            self._atualizar_contador()

            logger.info(f"Importação concluída: {len(novos_registros)} registros adicionados.")
            messagebox.showinfo("Sucesso", f"{len(novos_registros)} registros importados com sucesso!")

        except Exception as e:
            logger.error(f"Erro na importação automática: {e}")
            messagebox.showerror("Erro Crítico", f"Falha ao processar arquivos:\n{str(e)}")

    # Você pode REMOVER ou COMENTAR os métodos abaixo, pois não serão mais usados:
    # - _load_files
    # - janela_mapeamento
    # - _auto_map_field
    # - _apply_mapping

    # ========================================================================
    # PDF GENERATION AND PRINTING
    # ========================================================================

    def gerar_pdf(self) -> None:
        """
        Gera o arquivo PDF, faz backup e aciona a impressão automática.

        Fluxo:
        1. Validação de dados
        2. Backup dos registros
        3. Geração do PDF
        4. Impressão (opcional)
        5. Limpeza da tela
        """
        try:
            # Validação
            if not self.layout_ativo:
                messagebox.showwarning(
                    MESSAGES["no_layout"],
                    MESSAGES["no_layout_msg"],
                )
                return

            if not self.dados_fila:
                messagebox.showwarning(
                    MESSAGES["empty_queue"],
                    MESSAGES["empty_queue_msg"],
                )
                return

            # Backup
            try:
                self.pdf_engine.save_backup(self.dados_fila, self.layout_ativo)
            except PermissionError as e:
                messagebox.showwarning(
                    MESSAGES["file_open_warning"],
                    MESSAGES["file_open_msg"],
                )
                logger.error(f"Erro ao salvar backup: {e}")
                return

            # Geração PDF
            pdf_path = self.pdf_engine.generate_pdf(
                self.dados_fila, 
                self.layout_ativo, 
                overwrite=self.config_data.get("overwrite_pdf", False)
            )

            # Impressão
            auto = self.config_data.get("auto_imprimir", False)
            if auto or messagebox.askyesno(
                MESSAGES["pdf_generated"],
                MESSAGES["pdf_generated_msg"],
            ):
                if not self.print_engine.print_file(pdf_path):
                    # Fallback: abrir arquivo
                    self.print_engine.open_file(pdf_path)

            # Limpeza
            self._limpar_dados_layout()
            messagebox.showinfo(
                MESSAGES["success"],
                MESSAGES["success_msg"],
            )
            logger.info("PDF gerado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {e}")
            messagebox.showerror(
                MESSAGES["critical_error"],
                MESSAGES["critical_error_msg"].format(error=str(e)),
            )

    def _limpar_dados_layout(self) -> None:
        """Limpa a fila de registros e o conteúdo exibido na TreeView."""
        self.dados_fila = []
        if self.tree is not None:
            self.tree.delete(*self.tree.get_children())
        self._atualizar_contador()
        logger.info("Dados limpos")

    def _atualizar_contador(self) -> None:
        """Atualiza o label contador de itens na lista."""
        if self.lbl_contador:
            total = len(self.dados_fila)
            self.lbl_contador.configure(text=f"Total de itens na lista: {total}")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    root = ctk.CTk()
    app = GlassPrinterApp(root)
    root.mainloop()
