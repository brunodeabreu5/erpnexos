"""Customer management UI window for ERP Paraguay.

This module provides the user interface for customer CRUD operations.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional
from app.services.customer_service import (
    list_customers,
    get_customer_by_id,
    create_customer,
    update_customer,
    delete_customer,
    search_customers
)

logger = logging.getLogger(__name__)


class CustomersWindow:
    """Window for managing customers."""

    def __init__(self, parent):
        """Initialize the customers window.

        Args:
            parent: The parent Tkinter window
        """
        self.window = tk.Toplevel(parent)
        self.window.title("ERP Paraguay - Clientes")
        self.window.geometry("900x600")

        self.selected_customer_id = None

        self._build_ui()
        self._load_customers()

    def _build_ui(self):
        """Build the user interface."""
        # Top frame with buttons and search
        top_frame = ttk.Frame(self.window, padding=10)
        top_frame.pack(fill=tk.X)

        # Buttons
        ttk.Button(top_frame, text="Novo Cliente", command=self._new_customer).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Editar", command=self._edit_customer).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Excluir", command=self._delete_customer).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Atualizar", command=self._load_customers).pack(side=tk.LEFT, padx=(0, 20))

        # Search
        ttk.Label(top_frame, text="Buscar:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind('<KeyRelease>', self._on_search)
        ttk.Button(top_frame, text="🔍", command=self._do_search, width=3).pack(side=tk.LEFT)

        # Customers table
        table_frame = ttk.Frame(self.window, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "name", "email", "phone", "tax_id")
        self.customers_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=20
        )

        self.customers_tree.heading("id", text="ID")
        self.customers_tree.heading("name", text="Nome")
        self.customers_tree.heading("email", text="Email")
        self.customers_tree.heading("phone", text="Telefone")
        self.customers_tree.heading("tax_id", text="RUC/CI")

        self.customers_tree.column("id", width=50, anchor=tk.CENTER)
        self.customers_tree.column("name", width=250)
        self.customers_tree.column("email", width=200)
        self.customers_tree.column("phone", width=120)
        self.customers_tree.column("tax_id", width=120)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.customers_tree.yview)
        self.customers_tree.configure(yscrollcommand=scrollbar.set)

        self.customers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind selection event
        self.customers_tree.bind('<<TreeviewSelect>>', self._on_select)

    def _load_customers(self):
        """Load all customers into the table."""
        # Clear existing items
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)

        try:
            customers = list_customers(active_only=True)
            for customer in customers:
                self.customers_tree.insert("", tk.END, values=(
                    customer.id,
                    customer.name,
                    customer.email or "-",
                    customer.phone or "-",
                    customer.tax_id or "-"
                ))
        except Exception as e:
            logger.exception("Error loading customers")
            messagebox.showerror("Erro", f"Erro ao carregar clientes: {e}")

    def _on_select(self, event):
        """Handle row selection in the table."""
        selection = self.customers_tree.selection()
        if selection:
            item = self.customers_tree.item(selection[0])
            values = item['values']
            self.selected_customer_id = values[0]

    def _new_customer(self):
        """Open dialog to create a new customer."""
        self._open_customer_dialog()

    def _edit_customer(self):
        """Open dialog to edit selected customer."""
        if not self.selected_customer_id:
            messagebox.showwarning("Aviso", "Selecione um cliente para editar")
            return

        try:
            customer = get_customer_by_id(self.selected_customer_id)
            if customer:
                self._open_customer_dialog(customer)
            else:
                messagebox.showerror("Erro", "Cliente não encontrado")
        except Exception as e:
            logger.exception("Error loading customer")
            messagebox.showerror("Erro", f"Erro ao carregar cliente: {e}")

    def _delete_customer(self):
        """Delete the selected customer."""
        if not self.selected_customer_id:
            messagebox.showwarning("Aviso", "Selecione um cliente para excluir")
            return

        if not messagebox.askyesno("Confirmar", "Deseja realmente excluir este cliente?"):
            return

        try:
            success, error = delete_customer(self.selected_customer_id)
            if success:
                messagebox.showinfo("Sucesso", "Cliente excluído com sucesso")
                self._load_customers()
                self.selected_customer_id = None
            else:
                messagebox.showerror("Erro", error or "Erro ao excluir cliente")
        except Exception as e:
            logger.exception("Error deleting customer")
            messagebox.showerror("Erro", f"Erro ao excluir cliente: {e}")

    def _on_search(self, event):
        """Handle search input."""
        search_term = self.search_var.get().strip()
        if len(search_term) >= 2:
            self._do_search()
        elif not search_term:
            self._load_customers()

    def _do_search(self):
        """Perform search."""
        search_term = self.search_var.get().strip()
        if not search_term:
            self._load_customers()
            return

        # Clear existing items
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)

        try:
            customers = search_customers(search_term, active_only=True)
            for customer in customers:
                self.customers_tree.insert("", tk.END, values=(
                    customer.id,
                    customer.name,
                    customer.email or "-",
                    customer.phone or "-",
                    customer.tax_id or "-"
                ))
        except Exception as e:
            logger.exception("Error searching customers")
            messagebox.showerror("Erro", f"Erro ao buscar clientes: {e}")

    def _open_customer_dialog(self, customer=None):
        """Open dialog for creating/editing a customer.

        Args:
            customer: Customer object for editing, None for new customer
        """
        dialog = tk.Toplevel(self.window)
        dialog.title("Editar Cliente" if customer else "Novo Cliente")
        dialog.geometry("500x350")
        dialog.transient(self.window)
        dialog.grab_set()

        # Form fields
        form_frame = ttk.Frame(dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Name
        ttk.Label(form_frame, text="Nome *").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=customer.name if customer else "")
        ttk.Entry(form_frame, textvariable=name_var, width=40).grid(row=0, column=1, pady=5)

        # Email
        ttk.Label(form_frame, text="Email").grid(row=1, column=0, sticky=tk.W, pady=5)
        email_var = tk.StringVar(value=customer.email if customer and customer.email else "")
        ttk.Entry(form_frame, textvariable=email_var, width=40).grid(row=1, column=1, pady=5)

        # Phone
        ttk.Label(form_frame, text="Telefone").grid(row=2, column=0, sticky=tk.W, pady=5)
        phone_var = tk.StringVar(value=customer.phone if customer and customer.phone else "")
        ttk.Entry(form_frame, textvariable=phone_var, width=40).grid(row=2, column=1, pady=5)

        # Tax ID
        ttk.Label(form_frame, text="RUC/CI").grid(row=3, column=0, sticky=tk.W, pady=5)
        tax_id_var = tk.StringVar(value=customer.tax_id if customer and customer.tax_id else "")
        ttk.Entry(form_frame, textvariable=tax_id_var, width=40).grid(row=3, column=1, pady=5)

        # Address
        ttk.Label(form_frame, text="Endereço").grid(row=4, column=0, sticky=tk.W, pady=5)
        address_var = tk.StringVar(value=customer.address if customer and customer.address else "")
        ttk.Entry(form_frame, textvariable=address_var, width=40).grid(row=4, column=1, pady=5)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)

        def save():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Aviso", "Nome é obrigatório")
                return

            try:
                if customer:
                    # Update existing
                    success, error, _ = update_customer(
                        customer.id,
                        name=name,
                        email=email_var.get().strip() or None,
                        phone=phone_var.get().strip() or None,
                        address=address_var.get().strip() or None,
                        tax_id=tax_id_var.get().strip() or None
                    )
                else:
                    # Create new
                    success, error, _ = create_customer(
                        name=name,
                        email=email_var.get().strip() or None,
                        phone=phone_var.get().strip() or None,
                        address=address_var.get().strip() or None,
                        tax_id=tax_id_var.get().strip() or None
                    )

                if success:
                    messagebox.showinfo("Sucesso", "Cliente salvo com sucesso")
                    dialog.destroy()
                    self._load_customers()
                else:
                    messagebox.showerror("Erro", error or "Erro ao salvar cliente")
            except Exception as e:
                logger.exception("Error saving customer")
                messagebox.showerror("Erro", f"Erro ao salvar cliente: {e}")

        ttk.Button(button_frame, text="Salvar", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
