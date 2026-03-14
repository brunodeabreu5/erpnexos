"""User management UI window for ERP Paraguay.

This module provides the user interface for user CRUD operations.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional
from app.services.user_service import (
    list_users,
    get_user_by_id,
    create_user,
    update_user,
    change_user_password,
    deactivate_user,
    get_audit_logs,
    VALID_ROLES
)
from app.database.models import User

logger = logging.getLogger(__name__)


class UsersWindow:
    """Window for managing users (admin only)."""

    def __init__(self, parent, current_user_role: str = 'admin'):
        """Initialize the users window.

        Args:
            parent: The parent Tkinter window
            current_user_role: Role of the current user (for permission check)
        """
        # Check permission
        from app.services.auth_service import check_permission
        if not check_permission(current_user_role, 'view_user'):
            messagebox.showerror("Acesso Negado", "Você não tem permissão para acessar esta funcionalidade")
            return

        self.window = tk.Toplevel(parent)
        self.window.title("ERP Paraguay - Usuários")
        self.window.geometry("900x600")

        self.current_user_role = current_user_role
        self.selected_user_id = None

        self._build_ui()
        self._load_users()

    def _build_ui(self):
        """Build the user interface."""
        # Top frame with buttons
        top_frame = ttk.Frame(self.window, padding=10)
        top_frame.pack(fill=tk.X)

        if self._can_create_user():
            ttk.Button(top_frame, text="Novo Usuário", command=self._new_user).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(top_frame, text="Editar", command=self._edit_user).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(top_frame, text="Alterar Senha", command=self._change_password).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(top_frame, text="Desativar", command=self._deactivate_user).pack(side=tk.LEFT, padx=(0, 5))
        else:
            ttk.Button(top_frame, text="Alterar Minha Senha", command=self._change_my_password).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(top_frame, text="Atualizar", command=self._load_users).pack(side=tk.LEFT, padx=(0, 20))

        if self._can_view_audit_logs():
            ttk.Button(top_frame, text="Logs de Auditoria", command=self._view_audit_logs).pack(side=tk.LEFT)

        # Users table
        table_frame = ttk.Frame(self.window, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "username", "full_name", "email", "role", "last_login", "is_active")
        self.users_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=20
        )

        self.users_tree.heading("id", text="ID")
        self.users_tree.heading("username", text="Usuário")
        self.users_tree.heading("full_name", text="Nome Completo")
        self.users_tree.heading("email", text="Email")
        self.users_tree.heading("role", text="Função")
        self.users_tree.heading("last_login", text="Último Login")
        self.users_tree.heading("is_active", text="Ativo")

        self.users_tree.column("id", width=50, anchor=tk.CENTER)
        self.users_tree.column("username", width=150)
        self.users_tree.column("full_name", width=200)
        self.users_tree.column("email", width=200)
        self.users_tree.column("role", width=100)
        self.users_tree.column("last_login", width=150)
        self.users_tree.column("is_active", width=60, anchor=tk.CENTER)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)

        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind selection event
        self.users_tree.bind('<<TreeviewSelect>>', self._on_select)

    def _can_create_user(self) -> bool:
        """Check if current user can create users."""
        from app.services.auth_service import check_permission
        return check_permission(self.current_user_role, 'create_user')

    def _can_edit_user(self) -> bool:
        """Check if current user can edit users."""
        from app.services.auth_service import check_permission
        return check_permission(self.current_user_role, 'edit_user')

    def _can_view_audit_logs(self) -> bool:
        """Check if current user can view audit logs."""
        from app.services.auth_service import check_permission
        return check_permission(self.current_user_role, 'view_audit_logs')

    def _load_users(self):
        """Load all users into the table."""
        # Clear existing items
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)

        try:
            users = list_users(include_inactive=True)
            for user in users:
                last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Nunca"
                self.users_tree.insert("", tk.END, values=(
                    user.id,
                    user.username,
                    user.full_name or "-",
                    user.email or "-",
                    user.role,
                    last_login,
                    "Sim" if user.is_active else "Não"
                ))
        except Exception as e:
            logger.exception("Error loading users")
            messagebox.showerror("Erro", f"Erro ao carregar usuários: {e}")

    def _on_select(self, event):
        """Handle row selection in the table."""
        selection = self.users_tree.selection()
        if selection:
            item = self.users_tree.item(selection[0])
            values = item['values']
            self.selected_user_id = values[0]

    def _new_user(self):
        """Open dialog to create a new user."""
        self._open_user_dialog()

    def _edit_user(self):
        """Open dialog to edit selected user."""
        if not self.selected_user_id:
            messagebox.showwarning("Aviso", "Selecione um usuário para editar")
            return

        try:
            user = get_user_by_id(self.selected_user_id)
            if user:
                self._open_user_dialog(user)
            else:
                messagebox.showerror("Erro", "Usuário não encontrado")
        except Exception as e:
            logger.exception("Error loading user")
            messagebox.showerror("Erro", f"Erro ao carregar usuário: {e}")

    def _deactivate_user(self):
        """Deactivate the selected user."""
        if not self.selected_user_id:
            messagebox.showwarning("Aviso", "Selecione um usuário para desativar")
            return

        if not messagebox.askyesno("Confirmar", "Deseja realmente desativar este usuário?"):
            return

        try:
            success, error = deactivate_user(self.selected_user_id)
            if success:
                messagebox.showinfo("Sucesso", "Usuário desativado com sucesso")
                self._load_users()
                self.selected_user_id = None
            else:
                messagebox.showerror("Erro", error or "Erro ao desativar usuário")
        except Exception as e:
            logger.exception("Error deactivating user")
            messagebox.showerror("Erro", f"Erro ao desativar usuário: {e}")

    def _change_password(self):
        """Open dialog to change user's password."""
        if not self.selected_user_id:
            messagebox.showwarning("Aviso", "Selecione um usuário")
            return

        self._open_password_dialog(self.selected_user_id)

    def _change_my_password(self):
        """Open dialog to change own password."""
        # This would need the current user's ID - for now using selected
        if not self.selected_user_id:
            messagebox.showwarning("Aviso", "Selecione seu usuário")
            return

        self._open_password_dialog(self.selected_user_id)

    def _open_password_dialog(self, user_id: int):
        """Open password change dialog.

        Args:
            user_id: ID of the user
        """
        dialog = tk.Toplevel(self.window)
        dialog.title("Alterar Senha")
        dialog.geometry("400x200")
        dialog.transient(self.window)
        dialog.grab_set()

        form_frame = ttk.Frame(dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Nova Senha *").grid(row=0, column=0, sticky=tk.W, pady=5)
        new_password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=new_password_var, show="*", width=30).grid(row=0, column=1, pady=5)

        ttk.Label(form_frame, text="Confirmar Senha *").grid(row=1, column=0, sticky=tk.W, pady=5)
        confirm_password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=confirm_password_var, show="*", width=30).grid(row=1, column=1, pady=5)

        def save():
            new_pass = new_password_var.get()
            confirm_pass = confirm_password_var.get()

            if not new_pass:
                messagebox.showwarning("Aviso", "Nova senha é obrigatória")
                return

            if new_pass != confirm_pass:
                messagebox.showwarning("Aviso", "Senhas não conferem")
                return

            try:
                success, error = change_user_password(user_id, new_pass)
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

    def _open_user_dialog(self, user=None):
        """Open dialog for creating/editing a user.

        Args:
            user: User object for editing, None for new user
        """
        from app.validators import MIN_PASSWORD_LENGTH

        dialog = tk.Toplevel(self.window)
        dialog.title("Editar Usuário" if user else "Novo Usuário")
        dialog.geometry("450x400")
        dialog.transient(self.window)
        dialog.grab_set()

        # Form fields
        form_frame = ttk.Frame(dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        row = 0

        # Username (only for new users)
        if not user:
            ttk.Label(form_frame, text="Usuário *").grid(row=row, column=0, sticky=tk.W, pady=5)
            username_var = tk.StringVar()
            ttk.Entry(form_frame, textvariable=username_var, width=30).grid(row=row, column=1, pady=5)
            row += 1

            # Password (required for new users)
            ttk.Label(form_frame, text=f"Senha * (mín. {MIN_PASSWORD_LENGTH})").grid(row=row, column=0, sticky=tk.W, pady=5)
            password_var = tk.StringVar()
            ttk.Entry(form_frame, textvariable=password_var, show="*", width=30).grid(row=row, column=1, pady=5)
            row += 1
        else:
            username_var = None
            password_var = None

        # Full name
        ttk.Label(form_frame, text="Nome Completo").grid(row=row, column=0, sticky=tk.W, pady=5)
        full_name_var = tk.StringVar(value=user.full_name if user and user.full_name else "")
        ttk.Entry(form_frame, textvariable=full_name_var, width=30).grid(row=row, column=1, pady=5)
        row += 1

        # Email
        ttk.Label(form_frame, text="Email").grid(row=row, column=0, sticky=tk.W, pady=5)
        email_var = tk.StringVar(value=user.email if user and user.email else "")
        ttk.Entry(form_frame, textvariable=email_var, width=30).grid(row=row, column=1, pady=5)
        row += 1

        # Role
        ttk.Label(form_frame, text="Função *").grid(row=row, column=0, sticky=tk.W, pady=5)
        role_var = tk.StringVar(value=user.role if user else "sales")
        role_combo = ttk.Combobox(form_frame, textvariable=role_var, values=VALID_ROLES, state="readonly", width=27)
        role_combo.grid(row=row, column=1, pady=5)
        row += 1

        # Active status (only for editing)
        if user:
            is_active_var = tk.BooleanVar(value=user.is_active)
            ttk.Checkbutton(form_frame, text="Usuário Ativo", variable=is_active_var).grid(row=row, column=1, sticky=tk.W, pady=5)
            row += 1
        else:
            is_active_var = tk.BooleanVar(value=True)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)

        def save():
            # Validate and save
            if not user:
                # New user
                username = username_var.get().strip()
                password = password_var.get()

                if not username:
                    messagebox.showwarning("Aviso", "Usuário é obrigatório")
                    return
                if not password:
                    messagebox.showwarning("Aviso", "Senha é obrigatória")
                    return

                try:
                    success, error, _ = create_user(
                        username=username,
                        password=password,
                        full_name=full_name_var.get().strip() or None,
                        email=email_var.get().strip() or None,
                        role=role_var.get()
                    )

                    if success:
                        messagebox.showinfo("Sucesso", "Usuário criado com sucesso")
                        dialog.destroy()
                        self._load_users()
                    else:
                        messagebox.showerror("Erro", error or "Erro ao criar usuário")
                except Exception as e:
                    logger.exception("Error creating user")
                    messagebox.showerror("Erro", f"Erro ao criar usuário: {e}")
            else:
                # Update existing user
                try:
                    success, error, _ = update_user(
                        user.id,
                        full_name=full_name_var.get().strip() or None,
                        email=email_var.get().strip() or None,
                        role=role_var.get(),
                        is_active=is_active_var.get()
                    )

                    if success:
                        messagebox.showinfo("Sucesso", "Usuário atualizado com sucesso")
                        dialog.destroy()
                        self._load_users()
                    else:
                        messagebox.showerror("Erro", error or "Erro ao atualizar usuário")
                except Exception as e:
                    logger.exception("Error updating user")
                    messagebox.showerror("Erro", f"Erro ao atualizar usuário: {e}")

        ttk.Button(button_frame, text="Salvar", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def _view_audit_logs(self):
        """View audit logs."""
        AuditLogsWindow(self.window, self.current_user_role)


class AuditLogsWindow:
    """Window for viewing audit logs."""

    def __init__(self, parent, current_user_role: str = 'admin'):
        """Initialize the audit logs window.

        Args:
            parent: The parent Tkinter window
            current_user_role: Role of the current user
        """
        self.window = tk.Toplevel(parent)
        self.window.title("ERP Paraguay - Logs de Auditoria")
        self.window.geometry("1000x600")

        self._build_ui()
        self._load_logs()

    def _build_ui(self):
        """Build the user interface."""
        # Top frame
        top_frame = ttk.Frame(self.window, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Button(top_frame, text="Atualizar", command=self._load_logs).pack(side=tk.LEFT)
        ttk.Button(top_frame, text="Fechar", command=self.window.destroy).pack(side=tk.LEFT, padx=(5, 0))

        # Logs table
        table_frame = ttk.Frame(self.window, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "user", "action", "entity_type", "entity_id", "created_at")
        self.logs_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=20
        )

        self.logs_tree.heading("id", text="ID")
        self.logs_tree.heading("user", text="Usuário")
        self.logs_tree.heading("action", text="Ação")
        self.logs_tree.heading("entity_type", text="Entidade")
        self.logs_tree.heading("entity_id", text="ID Entidade")
        self.logs_tree.heading("created_at", text="Data/Hora")

        self.logs_tree.column("id", width=50, anchor=tk.CENTER)
        self.logs_tree.column("user", width=150)
        self.logs_tree.column("action", width=200)
        self.logs_tree.column("entity_type", width=120)
        self.logs_tree.column("entity_id", width=100, anchor=tk.CENTER)
        self.logs_tree.column("created_at", width=180)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.logs_tree.yview)
        self.logs_tree.configure(yscrollcommand=scrollbar.set)

        self.logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Double click to view details
        self.logs_tree.bind('<Double-Button-1>', self._view_details)

    def _load_logs(self):
        """Load audit logs into table."""
        # Clear existing items
        for item in self.logs_tree.get_children():
            self.logs_tree.delete(item)

        try:
            logs = get_audit_logs(limit=100)
            for log in logs:
                username = log.user.username if log.user else "Unknown"
                self.logs_tree.insert("", tk.END, values=(
                    log.id,
                    username,
                    log.action,
                    log.entity_type,
                    log.entity_id,
                    log.created_at.strftime("%Y-%m-%d %H:%M:%S")
                ))
        except Exception as e:
            logger.exception("Error loading audit logs")
            messagebox.showerror("Erro", f"Erro ao carregar logs: {e}")

    def _view_details(self, event):
        """View log entry details."""
        selection = self.logs_tree.selection()
        if not selection:
            return

        item = self.logs_tree.item(selection[0])
        values = item['values']

        # Show details dialog
        dialog = tk.Toplevel(self.window)
        dialog.title("Detalhes do Log")
        dialog.geometry("500x400")
        dialog.transient(self.window)

        info_frame = ttk.Frame(dialog, padding=20)
        info_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(info_frame, text=f"ID: {values[0]}", font=("", 10)).pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Usuário: {values[1]}", font=("", 10)).pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Ação: {values[2]}", font=("", 10)).pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Entidade: {values[3]} (ID: {values[4]})", font=("", 10)).pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Data/Hora: {values[5]}", font=("", 10)).pack(anchor=tk.W, pady=2)

        ttk.Button(info_frame, text="Fechar", command=dialog.destroy).pack(pady=20)
