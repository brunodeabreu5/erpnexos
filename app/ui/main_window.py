import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from datetime import datetime, timedelta
from app.config import setup_logging, SESSION_TIMEOUT_MINUTES
from app.services.auth_service import authenticate_user
from app.services.dashboard_service import get_dashboard_data, get_low_stock_products
from app.services.product_service import list_products
from app.reports.pdf_reports import generate_pdf
from app.ui.customers_window import CustomersWindow
from app.ui.categories_window import CategoriesWindow
from app.ui.sales_window import SalesWindow, SalesListWindow
from app.ui.reports_window import ReportsWindow
from app.ui.users_window import UsersWindow
from app.ui.suppliers_window import SuppliersWindow
from app.ui.financial_window import FinancialWindow

logger = logging.getLogger(__name__)


class App:
    """Main application class for ERP Paraguay.

    Manages the root window and login flow for the desktop application.
    Implements session management with automatic expiration.
    """

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the application.

        Args:
            root: The root Tkinter window
        """
        self.root = root
        self.session_start_time = None
        self.last_activity_time = None
        self.session_check_timer = None
        self.login()

    def login(self) -> None:
        """Create and display the login interface."""
        self.login_frame = ttk.Frame(self.root, padding=20)
        self.login_frame.pack()

        ttk.Label(self.login_frame, text="Usuario").pack()
        self.user = ttk.Entry(self.login_frame, width=30)
        self.user.pack(pady=5)
        self.user.focus()  # Set focus on username field

        ttk.Label(self.login_frame, text="Senha").pack()
        self.password = ttk.Entry(self.login_frame, show="*", width=30)
        self.password.pack(pady=5)

        # Bind Enter key to login for better UX
        self.password.bind('<Return>', lambda event: self.check())

        ttk.Button(self.login_frame, text="Entrar", command=self.check).pack(pady=10)

    def _start_session_checker(self) -> None:
        """Start the session timeout checker.

        Runs every minute to check if the session has expired.
        """
        if self.session_check_timer:
            self.root.after_cancel(self.session_check_timer)

        # Check every 60 seconds (60000 milliseconds)
        self.session_check_timer = self.root.after(60000, self._check_session_timeout)

    def _check_session_timeout(self) -> None:
        """Check if the session has timed out and logout if needed.

        Compares the last activity time with the configured session timeout.
        Logs the user out if the session has expired.
        """
        if not self.last_activity_time:
            return

        # Calculate time since last activity
        inactive_time = datetime.now() - self.last_activity_time
        timeout_duration = timedelta(minutes=SESSION_TIMEOUT_MINUTES)

        if inactive_time > timeout_duration:
            # Session has expired
            logger.warning(
                f"Session expired for user '{self.current_username}'. "
                f"Inactive for {inactive_time}"
            )
            messagebox.showwarning(
                "Sesión Expirada",
                f"Su sesión ha expirado por inactividad (más de {SESSION_TIMEOUT_MINUTES} minutos).\n"
                "Por favor, inicie sesión nuevamente."
            )
            self._logout()
            return

        # Reschedule the next check
        self.session_check_timer = self.root.after(60000, self._check_session_timeout)

    def _update_activity(self) -> None:
        """Update the last activity timestamp.

        Should be called on any user action to keep the session alive.
        """
        self.last_activity_time = datetime.now()

    def check(self) -> None:
        """Validate user credentials and handle login.

        Retrieves username and password from input fields, authenticates
        against the database, and shows appropriate messages.
        """
        username = self.user.get().strip()
        password = self.password.get()

        if not username or not password:
            messagebox.showwarning("Aviso", "Por favor ingrese usuario y contraseña")
            return

        try:
            success, error, user_info = authenticate_user(username, password)

            if success:
                logger.info(f"User '{username}' logged in successfully")
                self._open_dashboard(username, user_info)
            else:
                messagebox.showerror("Erro", error or "Login incorreto")
                logger.warning(f"Failed login attempt for user '{username}'")

        except Exception as e:
            logger.error(f"Login error for user '{username}': {e}", exc_info=True)
            messagebox.showerror(
                "Erro",
                "Ocurrió un error al intentar iniciar sesión. Por favor intente nuevamente."
            )
            # Clear password field on error
            self.password.delete(0, tk.END)

    def _open_dashboard(self, username: str, user_info: dict = None) -> None:
        """Remove login screen and show the main application with menu.

        Args:
            username: The username of the logged-in user
            user_info: Dictionary with user information (id, username, full_name, email, role)
        """
        self.current_username = username
        self.current_user_info = user_info or {}
        self.current_user_role = self.current_user_info.get('role', 'sales')

        # Initialize session tracking
        self.session_start_time = datetime.now()
        self.last_activity_time = datetime.now()
        logger.info(f"Session started for user '{username}' at {self.session_start_time}")

        self.login_frame.destroy()
        self.root.resizable(True, True)
        self.root.geometry("900x550")
        self.root.title(f"ERP Paraguay - {self.current_user_info.get('full_name', username)}")

        self._build_menu()
        self.content_frame = ttk.Frame(self.root, padding=20)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        self._show_inicio()

        # Start session timeout checker
        self._start_session_checker()

    def _build_menu(self) -> None:
        """Create the main menu bar."""
        from app.services.auth_service import check_permission

        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        menu_inicio = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Inicio", menu=menu_inicio)
        menu_inicio.add_command(label="Dashboard", command=self._show_inicio, accelerator="F5")

        menu_ventas = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ventas", menu=menu_ventas)
        if check_permission(self.current_user_role, 'create_sale'):
            menu_ventas.add_command(label="Nueva venta", command=self._new_sale, accelerator="F2")
        if check_permission(self.current_user_role, 'view_sale'):
            menu_ventas.add_command(label="Lista de ventas", command=self._show_sales_list, accelerator="F3")
        menu_ventas.add_separator()
        menu_ventas.add_command(label="Cobranzas", command=self._show_collections)

        menu_clientes = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Clientes", menu=menu_clientes)
        if check_permission(self.current_user_role, 'view_customer'):
            menu_clientes.add_command(label="Lista de clientes", command=self._show_customers)
        if check_permission(self.current_user_role, 'create_customer'):
            menu_clientes.add_command(label="Novo cliente", command=self._new_customer, accelerator="Ctrl+N")

        menu_productos = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Productos", menu=menu_productos)
        if check_permission(self.current_user_role, 'view_product'):
            menu_productos.add_command(label="Lista de productos", command=self._show_products, accelerator="F4")
        menu_productos.add_separator()
        if check_permission(self.current_user_role, 'view_category'):
            menu_productos.add_command(label="Categorías", command=self._show_categories)

        menu_inventario = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Inventario", menu=menu_inventario)
        menu_inventario.add_command(label="Ajustes de stock", command=self._show_stock_adjustments)
        menu_inventario.add_command(label="Movimientos", command=self._show_movements)

        menu_relatorios = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Relatorios", menu=menu_relatorios)
        if check_permission(self.current_user_role, 'view_reports'):
            menu_relatorios.add_command(label="Ventas por período", command=self._show_reports)
            menu_relatorios.add_command(label="Inventario actual", command=self._show_inventory_report)
            menu_relatorios.add_command(label="Estado de cliente", command=self._show_reports)
            menu_relatorios.add_separator()
            menu_relatorios.add_command(label="Gerar PDF (Demo)", command=self._show_reports)

        # Usuários menu (admin only)
        if check_permission(self.current_user_role, 'view_user'):
            menu_usuarios = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Usuários", menu=menu_usuarios)
            menu_usuarios.add_command(label="Lista de usuários", command=self._show_users)
            if check_permission(self.current_user_role, 'create_user'):
                menu_usuarios.add_command(label="Novo usuário", command=self._show_users)

        # Minha Conta menu
        menu_conta = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Minha Conta", menu=menu_conta)
        menu_conta.add_command(label="Alterar Senha", command=self._change_my_password)
        menu_conta.add_separator()
        menu_conta.add_command(label="Sair", command=self._logout, accelerator="Alt+F4")

        # Fornecedores menu (manager/admin only)
        if check_permission(self.current_user_role, 'create_product'):  # Using create_product as proxy for manager+
            menu_fornecedores = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Fornecedores", menu=menu_fornecedores)
            menu_fornecedores.add_command(label="Lista de fornecedores", command=self._show_suppliers)
            menu_fornecedores.add_command(label="Novo fornecedor", command=self._show_suppliers)
            menu_fornecedores.add_separator()
            menu_fornecedores.add_command(label="Compras", command=self._show_purchases)

        # Financeiro menu (manager/admin only)
        if check_permission(self.current_user_role, 'view_reports'):
            menu_financeiro = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Financeiro", menu=menu_financeiro)
            menu_financeiro.add_command(label="Despesas e Relatórios", command=self._show_financial)

        # Help menu
        menu_help = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=menu_help)
        menu_help.add_command(label="Atalhos de Teclado", command=self._show_keyboard_shortcuts)

        menubar.add_command(label="Sair", command=self._logout)

        # Bind keyboard shortcuts
        self.root.bind('<F2>', lambda e: self._new_sale() if check_permission(self.current_user_role, 'create_sale') else None)
        self.root.bind('<F3>', lambda e: self._show_sales_list())
        self.root.bind('<F4>', lambda e: self._show_products() if check_permission(self.current_user_role, 'view_product') else None)
        self.root.bind('<F5>', lambda e: self._refresh_current_view())
        self.root.bind('<Control-n>', lambda e: self._new_customer() if check_permission(self.current_user_role, 'create_customer') else None)
        self.root.bind('<Escape>', self._on_escape_key)
        """Create the main menu bar."""
        from app.services.auth_service import check_permission

        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        menu_inicio = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Inicio", menu=menu_inicio)
        menu_inicio.add_command(label="Dashboard", command=self._show_inicio)

        menu_ventas = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ventas", menu=menu_ventas)
        if check_permission(self.current_user_role, 'create_sale'):
            menu_ventas.add_command(label="Nueva venta", command=self._new_sale)
        if check_permission(self.current_user_role, 'view_sale'):
            menu_ventas.add_command(label="Lista de ventas", command=self._show_sales_list)
        menu_ventas.add_separator()
        menu_ventas.add_command(label="Cobranzas", command=self._show_collections)

        menu_clientes = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Clientes", menu=menu_clientes)
        if check_permission(self.current_user_role, 'view_customer'):
            menu_clientes.add_command(label="Lista de clientes", command=self._show_customers)
        if check_permission(self.current_user_role, 'create_customer'):
            menu_clientes.add_command(label="Novo cliente", command=self._new_customer)

        menu_productos = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Productos", menu=menu_productos)
        if check_permission(self.current_user_role, 'view_product'):
            menu_productos.add_command(label="Lista de productos", command=self._show_products)
        menu_productos.add_separator()
        if check_permission(self.current_user_role, 'view_category'):
            menu_productos.add_command(label="Categorías", command=self._show_categories)

        menu_inventario = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Inventario", menu=menu_inventario)
        menu_inventario.add_command(label="Ajustes de stock", command=self._show_stock_adjustments)
        menu_inventario.add_command(label="Movimientos", command=self._show_movements)

        menu_relatorios = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Relatorios", menu=menu_relatorios)
        if check_permission(self.current_user_role, 'view_reports'):
            menu_relatorios.add_command(label="Ventas por período", command=self._show_reports)
            menu_relatorios.add_command(label="Inventario actual", command=self._show_inventory_report)
            menu_relatorios.add_command(label="Estado de cliente", command=self._show_reports)
            menu_relatorios.add_separator()
            menu_relatorios.add_command(label="Gerar PDF (Demo)", command=self._show_reports)

        # Usuários menu (admin only)
        if check_permission(self.current_user_role, 'view_user'):
            menu_usuarios = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Usuários", menu=menu_usuarios)
            menu_usuarios.add_command(label="Lista de usuários", command=self._show_users)
            if check_permission(self.current_user_role, 'create_user'):
                menu_usuarios.add_command(label="Novo usuário", command=self._show_users)

        # Minha Conta menu
        menu_conta = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Minha Conta", menu=menu_conta)
        menu_conta.add_command(label="Alterar Senha", command=self._change_my_password)
        menu_conta.add_separator()
        menu_conta.add_command(label="Sair", command=self._logout)

        # Fornecedores menu (manager/admin only)
        if check_permission(self.current_user_role, 'create_product'):  # Using create_product as proxy for manager+
            menu_fornecedores = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Fornecedores", menu=menu_fornecedores)
            menu_fornecedores.add_command(label="Lista de fornecedores", command=self._show_suppliers)
            menu_fornecedores.add_command(label="Novo fornecedor", command=self._show_suppliers)
            menu_fornecedores.add_separator()
            menu_fornecedores.add_command(label="Compras", command=self._show_purchases)

        # Financeiro menu (manager/admin only)
        if check_permission(self.current_user_role, 'view_reports'):
            menu_financeiro = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Financeiro", menu=menu_financeiro)
            menu_financeiro.add_command(label="Despesas e Relatórios", command=self._show_financial)

        menubar.add_command(label="Sair", command=self._logout)

    def _clear_content(self) -> None:
        """Remove all widgets from the content area."""
        for w in self.content_frame.winfo_children():
            w.destroy()

    def _show_inicio(self) -> None:
        """Show dashboard with stats and low stock."""
        self._update_activity()  # Update session activity
        self._clear_content()
        self.root.title("ERP Paraguay - Inicio")

        try:
            data = get_dashboard_data()
            low_stock = get_low_stock_products(10)
        except Exception as e:
            logger.exception("Error loading dashboard")
            messagebox.showerror("Erro", f"Error al cargar datos: {e}")
            return

        ttk.Label(
            self.content_frame,
            text=f"Bienvenido, {self.current_username}",
            font=("", 14),
        ).pack(pady=(0, 10))
        ttk.Separator(self.content_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        stats = ttk.Frame(self.content_frame)
        stats.pack(fill=tk.X, pady=10)
        ttk.Label(stats, text=f"Productos en inventario: {data['products']}", font=("", 11)).pack(side=tk.LEFT, padx=(0, 30))
        ttk.Label(stats, text=f"Ventas (total): {data['sales']}", font=("", 11)).pack(side=tk.LEFT)

        ttk.Label(self.content_frame, text="Productos con stock bajo (< 10)", font=("", 11)).pack(anchor=tk.W, pady=(15, 5))
        if not low_stock:
            ttk.Label(self.content_frame, text="Ninguno.", foreground="gray").pack(anchor=tk.W)
        else:
            tree = ttk.Treeview(self.content_frame, columns=("id", "name", "price", "stock"), show="headings", height=8)
            tree.heading("id", text="ID")
            tree.heading("name", text="Producto")
            tree.heading("price", text="Precio")
            tree.heading("stock", text="Stock")
            tree.pack(fill=tk.BOTH, expand=True, pady=5)
            for p in low_stock:
                tree.insert("", tk.END, values=(p.id, p.name, str(p.price), str(p.stock)))

    def _show_products(self) -> None:
        """Show products list with refresh."""
        self._clear_content()
        self.root.title("ERP Paraguay - Productos")

        top = ttk.Frame(self.content_frame)
        top.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(top, text="Actualizar lista", command=self._load_products_table).pack(side=tk.LEFT)

        self.products_tree = ttk.Treeview(
            self.content_frame,
            columns=("id", "name", "price", "stock"),
            show="headings",
            height=20,
        )
        self.products_tree.heading("id", text="ID")
        self.products_tree.heading("name", text="Producto")
        self.products_tree.heading("price", text="Precio")
        self.products_tree.heading("stock", text="Stock")
        self.products_tree.pack(fill=tk.BOTH, expand=True)
        self._load_products_table()

    def _load_products_table(self) -> None:
        """Load products into the Treeview."""
        for row in self.products_tree.get_children():
            self.products_tree.delete(row)
        try:
            for p in list_products():
                self.products_tree.insert("", tk.END, values=(p.id, p.name, str(p.price), str(p.stock)))
        except Exception as e:
            logger.exception("Error loading products")
            messagebox.showerror("Erro", f"Error al cargar productos: {e}")

    def _show_customers(self) -> None:
        """Show customers management window."""
        try:
            CustomersWindow(self.root)
        except Exception as e:
            logger.exception("Error opening customers window")
            messagebox.showerror("Erro", f"Error al abrir ventana de clientes: {e}")

    def _new_customer(self) -> None:
        """Open new customer dialog (directly opens customers window)."""
        self._show_customers()

    def _show_categories(self) -> None:
        """Show categories management window."""
        try:
            CategoriesWindow(self.root)
        except Exception as e:
            logger.exception("Error opening categories window")
            messagebox.showerror("Erro", f"Error al abrir ventana de categorías: {e}")

    def _new_sale(self) -> None:
        """Open new sale (POS) window."""
        self._update_activity()  # Update session activity
        try:
            SalesWindow(self.root)
        except Exception as e:
            logger.exception("Error opening sales window")
            messagebox.showerror("Erro", f"Error al abrir ventana de ventas: {e}")

    def _show_sales_list(self) -> None:
        """Show sales list window."""
        self._update_activity()  # Update session activity
        try:
            SalesListWindow(self.root)
        except Exception as e:
            logger.exception("Error opening sales list window")
            messagebox.showerror("Erro", f"Error al abrir lista de ventas: {e}")

    def _show_collections(self) -> None:
        """Show collections (not implemented yet)."""
        messagebox.showinfo("Info", "Módulo de cobranzas en desarrollo")

    def _show_stock_adjustments(self) -> None:
        """Show stock adjustments (not implemented yet)."""
        messagebox.showinfo("Info", "Módulo de ajustes de stock en desarrollo")

    def _show_movements(self) -> None:
        """Show stock movements (not implemented yet)."""
        messagebox.showinfo("Info", "Módulo de movimientos en desarrollo")

    def _show_inventory_report(self) -> None:
        """Generate inventory report directly."""
        try:
            from tkinter import filedialog
            from app.reports.pdf_reports import generate_inventory_report

            path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
                initialfile="inventory_report.pdf",
            )
            if path:
                generate_inventory_report(path)
                messagebox.showinfo("Sucesso", f"Relatório de inventario guardado:\n{path}")
        except Exception as e:
            logger.exception("Error generating inventory report")
            messagebox.showerror("Erro", f"Error al generar relatório: {e}")

    def _show_users(self) -> None:
        """Show users management window."""
        try:
            UsersWindow(self.root, self.current_user_role)
        except Exception as e:
            logger.exception("Error opening users window")
            messagebox.showerror("Erro", f"Error al abrir ventana de usuários: {e}")

    def _change_my_password(self) -> None:
        """Open dialog to change own password."""
        # Get current user ID from user_info
        user_id = self.current_user_info.get('id')
        if not user_id:
            messagebox.showerror("Erro", "Informações de usuário não disponíveis")
            return

        # Simple password change dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Alterar Senha")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        form_frame = ttk.Frame(dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Senha Atual *").grid(row=0, column=0, sticky=tk.W, pady=5)
        old_password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=old_password_var, show="*", width=30).grid(row=0, column=1, pady=5)

        ttk.Label(form_frame, text="Nova Senha *").grid(row=1, column=0, sticky=tk.W, pady=5)
        new_password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=new_password_var, show="*", width=30).grid(row=1, column=1, pady=5)

        ttk.Label(form_frame, text="Confirmar Senha *").grid(row=2, column=0, sticky=tk.W, pady=5)
        confirm_password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=confirm_password_var, show="*", width=30).grid(row=2, column=1, pady=5)

        def save():
            from app.services.auth_service import change_password
            from app.config import MIN_PASSWORD_LENGTH

            old_pass = old_password_var.get()
            new_pass = new_password_var.get()
            confirm_pass = confirm_password_var.get()

            if not old_pass or not new_pass:
                messagebox.showwarning("Aviso", "Todos os campos são obrigatórios")
                return

            if len(new_pass) < MIN_PASSWORD_LENGTH:
                messagebox.showwarning("Aviso", f"Senha deve ter pelo menos {MIN_PASSWORD_LENGTH} caracteres")
                return

            if new_pass != confirm_pass:
                messagebox.showwarning("Aviso", "Senhas não conferem")
                return

            try:
                success, error = change_password(self.current_username, old_pass, new_pass)
                if success:
                    messagebox.showinfo("Sucesso", "Senha alterada com sucesso")
                    dialog.destroy()
                else:
                    messagebox.showerror("Erro", error or "Erro ao alterar senha")
            except Exception as e:
                logger.exception("Error changing password")
                messagebox.showerror("Erro", f"Erro ao alterar senha: {e}")

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Alterar", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def _show_suppliers(self) -> None:
        """Show suppliers management window."""
        try:
            SuppliersWindow(self.root)
        except Exception as e:
            logger.exception("Error opening suppliers window")
            messagebox.showerror("Erro", f"Error al abrir ventana de fornecedores: {e}")

    def _show_purchases(self) -> None:
        """Show purchases window."""
        try:
            from app.ui.suppliers_window import PurchasesWindow
            PurchasesWindow(self.root)
        except Exception as e:
            logger.exception("Error opening purchases window")
            messagebox.showerror("Erro", f"Error al abrir ventana de compras: {e}")

    def _show_financial(self) -> None:
        """Show financial management window."""
        try:
            FinancialWindow(self.root)
        except Exception as e:
            logger.exception("Error opening financial window")
            messagebox.showerror("Erro", f"Error al abrir ventana financiera: {e}")

    def _refresh_current_view(self) -> None:
        """Refresh the current view."""
        try:
            # Determine current view based on window title
            title = self.root.title().split(" - ")[-1]
            if "Inicio" in title or "Principal" in title:
                self._show_inicio()
            elif "Productos" in title:
                self._load_products_table()
        except Exception as e:
            logger.exception("Error refreshing view")

    def _on_escape_key(self, event=None):
        """Handle ESC key press - close focused window or dialog."""
        try:
            focused = self.root.focus_get()
            if focused and isinstance(focused, tk.Toplevel) or isinstance(focused, tk.Tk):
                focused.destroy()
        except Exception:
            pass

    def _show_keyboard_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        shortcuts_window = tk.Toplevel(self.root)
        shortcuts_window.title("Atalhos de Teclado")
        shortcuts_window.geometry("500x400")
        shortcuts_window.transient(self.root)

        text_frame = ttk.Frame(shortcuts_window, padding=20)
        text_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(text_frame, text="Atalhos de Teclado - ERP Paraguay", font=("", 14, "bold")).pack(pady=(0, 20))

        shortcuts = [
            ("F2", "Nueva Venta"),
            ("F3", "Lista de Ventas"),
            ("F4", "Lista de Productos"),
            ("F5", "Atualizar vista atual"),
            ("Ctrl+N", "Novo Cliente"),
            ("ESC", "Fechar janela/dialogo"),
            ("Alt+F4", "Sair"),
            ("", ""),
            ("Atalhos na janela de vendas:", ""),
            ("Enter", "Adicionar produto ao carrinho"),
            ("F4", "Finalizar venda"),
        ]

        for key, action in shortcuts:
            if key == "":
                ttk.Label(text_frame, text="").pack(pady=5)
            else:
                frame = ttk.Frame(text_frame)
                frame.pack(fill=tk.X, pady=2)
                ttk.Label(frame, text=key, font=("", 10, "bold"), width=15).pack(side=tk.LEFT)
                ttk.Label(frame, text=action).pack(side=tk.LEFT)

        ttk.Button(text_frame, text="Fechar", command=shortcuts_window.destroy).pack(pady=20)

    def _show_reports(self) -> None:
        """Show reports section and generate PDF."""
        self._clear_content()
        self.root.title("ERP Paraguay - Relatorios")

        ttk.Label(self.content_frame, text="Relatorios", font=("", 14)).pack(pady=(0, 20))
        ttk.Label(self.content_frame, text="Generar un PDF de ejemplo (report.pdf).").pack(anchor=tk.W, pady=5)

        def do_generate() -> None:
            try:
                path = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF", "*.pdf")],
                    initialfile="report.pdf",
                )
                if path:
                    generate_pdf(path)
                    messagebox.showinfo("OK", f"PDF guardado en:\n{path}")
            except Exception as e:
                logger.exception("Error generating PDF")
                messagebox.showerror("Erro", f"Error al generar PDF: {e}")

        ttk.Button(self.content_frame, text="Gerar PDF", command=do_generate).pack(pady=20)

    def _logout(self) -> None:
        """Logout user and close the application.

        Cleans up session timers and closes the application after confirmation.
        """
        # Cancel session checker timer
        if self.session_check_timer:
            self.root.after_cancel(self.session_check_timer)
            self.session_check_timer = None

        # Log session duration
        if self.session_start_time:
            session_duration = datetime.now() - self.session_start_time
            logger.info(
                f"User '{self.current_username}' logged out. "
                f"Session duration: {session_duration}"
            )

        if messagebox.askokcancel("Sair", "¿Cerrar la aplicación?"):
            self.root.quit()
            self.root.destroy()


def run_app() -> None:
    """Initialize and run the ERP Paraguay application.

    Sets up logging, creates the main window, and starts the Tkinter event loop.
    """
    setup_logging()
    root = tk.Tk()
    root.title("ERP Paraguay")
    root.resizable(False, False)  # Prevent window resizing for login

    # Center the window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'+{x}+{y}')

    App(root)
    root.mainloop()
