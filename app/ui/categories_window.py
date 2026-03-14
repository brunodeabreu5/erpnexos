"""Category management UI window for ERP Paraguay.

This module provides the user interface for category CRUD operations.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from app.services.category_service import (
    list_categories,
    get_category_by_id,
    create_category,
    update_category,
    delete_category
)

logger = logging.getLogger(__name__)


class CategoriesWindow:
    """Window for managing categories."""

    def __init__(self, parent):
        """Initialize the categories window.

        Args:
            parent: The parent Tkinter window
        """
        self.window = tk.Toplevel(parent)
        self.window.title("ERP Paraguay - Categorías")
        self.window.geometry("600x500")

        self.selected_category_id = None

        self._build_ui()
        self._load_categories()

    def _build_ui(self):
        """Build the user interface."""
        # Top frame with buttons
        top_frame = ttk.Frame(self.window, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Button(top_frame, text="Nova Categoria", command=self._new_category).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Editar", command=self._edit_category).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Excluir", command=self._delete_category).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Atualizar", command=self._load_categories).pack(side=tk.LEFT)

        # Categories table
        table_frame = ttk.Frame(self.window, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "name", "description")
        self.categories_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=20
        )

        self.categories_tree.heading("id", text="ID")
        self.categories_tree.heading("name", text="Nome")
        self.categories_tree.heading("description", text="Descrição")

        self.categories_tree.column("id", width=50, anchor=tk.CENTER)
        self.categories_tree.column("name", width=200)
        self.categories_tree.column("description", width=300)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.categories_tree.yview)
        self.categories_tree.configure(yscrollcommand=scrollbar.set)

        self.categories_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind selection event
        self.categories_tree.bind('<<TreeviewSelect>>', self._on_select)

    def _load_categories(self):
        """Load all categories into the table."""
        # Clear existing items
        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)

        try:
            categories = list_categories(active_only=True)
            for category in categories:
                self.categories_tree.insert("", tk.END, values=(
                    category.id,
                    category.name,
                    category.description or "-"
                ))
        except Exception as e:
            logger.exception("Error loading categories")
            messagebox.showerror("Erro", f"Erro ao carregar categorias: {e}")

    def _on_select(self, event):
        """Handle row selection in the table."""
        selection = self.categories_tree.selection()
        if selection:
            item = self.categories_tree.item(selection[0])
            values = item['values']
            self.selected_category_id = values[0]

    def _new_category(self):
        """Open dialog to create a new category."""
        self._open_category_dialog()

    def _edit_category(self):
        """Open dialog to edit selected category."""
        if not self.selected_category_id:
            messagebox.showwarning("Aviso", "Selecione uma categoria para editar")
            return

        try:
            category = get_category_by_id(self.selected_category_id)
            if category:
                self._open_category_dialog(category)
            else:
                messagebox.showerror("Erro", "Categoria não encontrada")
        except Exception as e:
            logger.exception("Error loading category")
            messagebox.showerror("Erro", f"Erro ao carregar categoria: {e}")

    def _delete_category(self):
        """Delete the selected category."""
        if not self.selected_category_id:
            messagebox.showwarning("Aviso", "Selecione uma categoria para excluir")
            return

        if not messagebox.askyesno("Confirmar", "Deseja realmente excluir esta categoria?"):
            return

        try:
            success, error = delete_category(self.selected_category_id)
            if success:
                messagebox.showinfo("Sucesso", "Categoria excluída com sucesso")
                self._load_categories()
                self.selected_category_id = None
            else:
                messagebox.showerror("Erro", error or "Erro ao excluir categoria")
        except Exception as e:
            logger.exception("Error deleting category")
            messagebox.showerror("Erro", f"Erro ao excluir categoria: {e}")

    def _open_category_dialog(self, category=None):
        """Open dialog for creating/editing a category.

        Args:
            category: Category object for editing, None for new category
        """
        dialog = tk.Toplevel(self.window)
        dialog.title("Editar Categoria" if category else "Nova Categoria")
        dialog.geometry("450x250")
        dialog.transient(self.window)
        dialog.grab_set()

        # Form fields
        form_frame = ttk.Frame(dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Name
        ttk.Label(form_frame, text="Nome *").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=category.name if category else "")
        ttk.Entry(form_frame, textvariable=name_var, width=40).grid(row=0, column=1, pady=5)

        # Description
        ttk.Label(form_frame, text="Descrição").grid(row=1, column=0, sticky=tk.W, pady=5)
        desc_var = tk.StringVar(value=category.description if category and category.description else "")
        ttk.Entry(form_frame, textvariable=desc_var, width=40).grid(row=1, column=1, pady=5)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)

        def save():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Aviso", "Nome é obrigatório")
                return

            try:
                if category:
                    # Update existing
                    success, error, _ = update_category(
                        category.id,
                        name=name,
                        description=desc_var.get().strip() or None
                    )
                else:
                    # Create new
                    success, error, _ = create_category(
                        name=name,
                        description=desc_var.get().strip() or None
                    )

                if success:
                    messagebox.showinfo("Sucesso", "Categoria salva com sucesso")
                    dialog.destroy()
                    self._load_categories()
                else:
                    messagebox.showerror("Erro", error or "Erro ao salvar categoria")
            except Exception as e:
                logger.exception("Error saving category")
                messagebox.showerror("Erro", f"Erro ao salvar categoria: {e}")

        ttk.Button(button_frame, text="Salvar", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
