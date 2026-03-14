"""Supplier management UI window for ERP Paraguay.

This module provides the user interface for supplier and purchase management.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional
from datetime import datetime

from app.services.supplier_service import (
    list_suppliers,
    get_supplier_by_id,
    create_supplier,
    update_supplier,
    delete_supplier,
    search_suppliers,
    list_purchases,
    get_purchase_by_id,
    create_purchase,
    receive_purchase
)
from app.services.product_service import list_products

logger = logging.getLogger(__name__)


class SuppliersWindow:
    """Window for managing suppliers."""

    def __init__(self, parent):
        """Initialize the suppliers window.

        Args:
            parent: The parent Tkinter window
        """
        self.window = tk.Toplevel(parent)
        self.window.title("ERP Paraguay - Fornecedores")
        self.window.geometry("1000x600")

        self.selected_supplier_id = None

        self._build_ui()
        self._load_suppliers()

    def _build_ui(self):
        """Build the user interface."""
        # Top frame with buttons
        top_frame = ttk.Frame(self.window, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Button(top_frame, text="Novo Fornecedor", command=self._new_supplier).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Editar", command=self._edit_supplier).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Excluir", command=self._delete_supplier).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Nova Compra", command=self._new_purchase).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Ver Compras", command=self._view_purchases).pack(side=tk.LEFT, padx=(0, 20))

        # Search
        ttk.Label(top_frame, text="Buscar:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind('<KeyRelease>', self._on_search)
        ttk.Button(top_frame, text="🔍", command=self._do_search, width=3).pack(side=tk.LEFT)

        ttk.Button(top_frame, text="Atualizar", command=self._load_suppliers).pack(side=tk.LEFT)

        # Suppliers table
        table_frame = ttk.Frame(self.window, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "name", "contact", "email", "phone", "tax_id")
        self.suppliers_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=15
        )

        self.suppliers_tree.heading("id", text="ID")
        self.suppliers_tree.heading("name", text="Nome")
        self.suppliers_tree.heading("contact", text="Contato")
        self.suppliers_tree.heading("email", text="Email")
        self.suppliers_tree.heading("phone", text="Telefone")
        self.suppliers_tree.heading("tax_id", text="RUC/CI")

        self.suppliers_tree.column("id", width=50, anchor=tk.CENTER)
        self.suppliers_tree.column("name", width=200)
        self.suppliers_tree.column("contact", width=150)
        self.suppliers_tree.column("email", width=180)
        self.suppliers_tree.column("phone", width=120)
        self.suppliers_tree.column("tax_id", width=120)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.suppliers_tree.yview)
        self.suppliers_tree.configure(yscrollcommand=scrollbar.set)

        self.suppliers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind selection event
        self.suppliers_tree.bind('<<TreeviewSelect>>', self._on_select)

    def _load_suppliers(self):
        """Load all suppliers into the table."""
        # Clear existing items
        for item in self.suppliers_tree.get_children():
            self.suppliers_tree.delete(item)

        try:
            suppliers = list_suppliers(active_only=True)
            for supplier in suppliers:
                self.suppliers_tree.insert("", tk.END, values=(
                    supplier.id,
                    supplier.name,
                    supplier.contact_person or "-",
                    supplier.email or "-",
                    supplier.phone or "-",
                    supplier.tax_id or "-"
                ))
        except Exception as e:
            logger.exception("Error loading suppliers")
            messagebox.showerror("Erro", f"Erro ao carregar fornecedores: {e}")

    def _on_select(self, event):
        """Handle row selection in the table."""
        selection = self.suppliers_tree.selection()
        if selection:
            item = self.suppliers_tree.item(selection[0])
            values = item['values']
            self.selected_supplier_id = values[0]

    def _new_supplier(self):
        """Open dialog to create a new supplier."""
        self._open_supplier_dialog()

    def _edit_supplier(self):
        """Open dialog to edit selected supplier."""
        if not self.selected_supplier_id:
            messagebox.showwarning("Aviso", "Selecione um fornecedor para editar")
            return

        try:
            supplier = get_supplier_by_id(self.selected_supplier_id)
            if supplier:
                self._open_supplier_dialog(supplier)
            else:
                messagebox.showerror("Erro", "Fornecedor não encontrado")
        except Exception as e:
            logger.exception("Error loading supplier")
            messagebox.showerror("Erro", f"Erro ao carregar fornecedor: {e}")

    def _delete_supplier(self):
        """Delete the selected supplier."""
        if not self.selected_supplier_id:
            messagebox.showwarning("Aviso", "Selecione um fornecedor para excluir")
            return

        if not messagebox.askyesno("Confirmar", "Deseja realmente excluir este fornecedor?"):
            return

        try:
            success, error = delete_supplier(self.selected_supplier_id)
            if success:
                messagebox.showinfo("Sucesso", "Fornecedor excluído com sucesso")
                self._load_suppliers()
                self.selected_supplier_id = None
            else:
                messagebox.showerror("Erro", error or "Erro ao excluir fornecedor")
        except Exception as e:
            logger.exception("Error deleting supplier")
            messagebox.showerror("Erro", f"Erro ao excluir fornecedor: {e}")

    def _on_search(self, event):
        """Handle search input."""
        search_term = self.search_var.get().strip()
        if len(search_term) >= 2:
            self._do_search()
        elif not search_term:
            self._load_suppliers()

    def _do_search(self):
        """Perform search."""
        search_term = self.search_var.get().strip()
        if not search_term:
            self._load_suppliers()
            return

        # Clear existing items
        for item in self.suppliers_tree.get_children():
            self.suppliers_tree.delete(item)

        try:
            suppliers = search_suppliers(search_term, active_only=True)
            for supplier in suppliers:
                self.suppliers_tree.insert("", tk.END, values=(
                    supplier.id,
                    supplier.name,
                    supplier.contact_person or "-",
                    supplier.email or "-",
                    supplier.phone or "-",
                    supplier.tax_id or "-"
                ))
        except Exception as e:
            logger.exception("Error searching suppliers")
            messagebox.showerror("Erro", f"Erro ao buscar fornecedores: {e}")

    def _open_supplier_dialog(self, supplier=None):
        """Open dialog for creating/editing a supplier.

        Args:
            supplier: Supplier object for editing, None for new supplier
        """
        dialog = tk.Toplevel(self.window)
        dialog.title("Editar Fornecedor" if supplier else "Novo Fornecedor")
        dialog.geometry("500x400")
        dialog.transient(self.window)
        dialog.grab_set()

        # Form fields
        form_frame = ttk.Frame(dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Name
        ttk.Label(form_frame, text="Nome *").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value=supplier.name if supplier else "")
        ttk.Entry(form_frame, textvariable=name_var, width=40).grid(row=0, column=1, pady=5)

        # Contact person
        ttk.Label(form_frame, text="Contato").grid(row=1, column=0, sticky=tk.W, pady=5)
        contact_var = tk.StringVar(value=supplier.contact_person if supplier and supplier.contact_person else "")
        ttk.Entry(form_frame, textvariable=contact_var, width=40).grid(row=1, column=1, pady=5)

        # Email
        ttk.Label(form_frame, text="Email").grid(row=2, column=0, sticky=tk.W, pady=5)
        email_var = tk.StringVar(value=supplier.email if supplier and supplier.email else "")
        ttk.Entry(form_frame, textvariable=email_var, width=40).grid(row=2, column=1, pady=5)

        # Phone
        ttk.Label(form_frame, text="Telefone").grid(row=3, column=0, sticky=tk.W, pady=5)
        phone_var = tk.StringVar(value=supplier.phone if supplier and supplier.phone else "")
        ttk.Entry(form_frame, textvariable=phone_var, width=40).grid(row=3, column=1, pady=5)

        # Tax ID
        ttk.Label(form_frame, text="RUC/CI").grid(row=4, column=0, sticky=tk.W, pady=5)
        tax_id_var = tk.StringVar(value=supplier.tax_id if supplier and supplier.tax_id else "")
        ttk.Entry(form_frame, textvariable=tax_id_var, width=40).grid(row=4, column=1, pady=5)

        # Address
        ttk.Label(form_frame, text="Endereço").grid(row=5, column=0, sticky=tk.W, pady=5)
        address_var = tk.StringVar(value=supplier.address if supplier and supplier.address else "")
        ttk.Entry(form_frame, textvariable=address_var, width=40).grid(row=5, column=1, pady=5)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)

        def save():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Aviso", "Nome é obrigatório")
                return

            try:
                if supplier:
                    # Update existing
                    success, error, _ = update_supplier(
                        supplier.id,
                        name=name,
                        contact_person=contact_var.get().strip() or None,
                        email=email_var.get().strip() or None,
                        phone=phone_var.get().strip() or None,
                        address=address_var.get().strip() or None,
                        tax_id=tax_id_var.get().strip() or None
                    )
                else:
                    # Create new
                    success, error, _ = create_supplier(
                        name=name,
                        contact_person=contact_var.get().strip() or None,
                        email=email_var.get().strip() or None,
                        phone=phone_var.get().strip() or None,
                        address=address_var.get().strip() or None,
                        tax_id=tax_id_var.get().strip() or None
                    )

                if success:
                    messagebox.showinfo("Sucesso", "Fornecedor salvo com sucesso")
                    dialog.destroy()
                    self._load_suppliers()
                else:
                    messagebox.showerror("Erro", error or "Erro ao salvar fornecedor")
            except Exception as e:
                logger.exception("Error saving supplier")
                messagebox.showerror("Erro", f"Erro ao salvar fornecedor: {e}")

        ttk.Button(button_frame, text="Salvar", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def _new_purchase(self):
        """Open dialog to create a new purchase."""
        if not self.selected_supplier_id:
            messagebox.showwarning("Aviso", "Selecione um fornecedor")
            return

        try:
            supplier = get_supplier_by_id(self.selected_supplier_id)
            if supplier:
                PurchaseDialog(self.window, self.selected_supplier_id, supplier.name, self._on_purchase_created)
            else:
                messagebox.showerror("Erro", "Fornecedor não encontrado")
        except Exception as e:
            logger.exception("Error loading supplier")
            messagebox.showerror("Erro", f"Erro ao carregar fornecedor: {e}")

    def _on_purchase_created(self):
        """Callback when purchase is created."""
        messagebox.showinfo("Sucesso", "Compra registrada com sucesso")

    def _view_purchases(self):
        """View purchases (optionally filtered by supplier)."""
        PurchasesWindow(self.window, self.selected_supplier_id)


class PurchaseDialog:
    """Dialog for creating a purchase."""

    def __init__(self, parent, supplier_id: int, supplier_name: str, callback=None):
        """Initialize the purchase dialog.

        Args:
            parent: The parent Tkinter window
            supplier_id: ID of the supplier
            supplier_name: Name of the supplier
            callback: Callback function when purchase is created
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Nova Compra - {supplier_name}")
        self.dialog.geometry("900x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.supplier_id = supplier_id
        self.callback = callback
        self.products_cache = {}
        self.cart_items = []

        self._build_ui()
        self._load_products()

    def _build_ui(self):
        """Build the user interface."""
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Product selection
        top_frame = ttk.LabelFrame(main_frame, text="Seleção de Produto", padding=10)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(top_frame, text="Produto:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.product_var = tk.StringVar()
        self.product_combobox = ttk.Combobox(
            top_frame,
            textvariable=self.product_var,
            width=40,
            state='readonly'
        )
        self.product_combobox.grid(row=0, column=1, padx=5, sticky=tk.EW)
        self.product_combobox.bind('<<ComboboxSelected>>', self._on_product_select)

        ttk.Label(top_frame, text="Custo Unit.:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.unit_cost_var = tk.StringVar(value="0")
        ttk.Entry(top_frame, textvariable=self.unit_cost_var, width=10).grid(row=0, column=3, padx=5)

        ttk.Label(top_frame, text="Quantidade:").grid(row=0, column=4, sticky=tk.W, padx=(10, 5))
        self.quantity_var = tk.StringVar(value="1")
        ttk.Entry(top_frame, textvariable=self.quantity_var, width=10).grid(row=0, column=5, padx=5)

        ttk.Button(top_frame, text="Adicionar", command=self._add_to_cart).grid(row=0, column=6, padx=10)

        # Cart
        cart_frame = ttk.LabelFrame(main_frame, text="Itens da Compra", padding=10)
        cart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        columns = ("product", "qty", "cost", "subtotal", "actions")
        self.cart_tree = ttk.Treeview(cart_frame, columns=columns, show="headings", height=10)

        self.cart_tree.heading("product", text="Produto")
        self.cart_tree.heading("qty", text="Quant.")
        self.cart_tree.heading("cost", text="Custo Unit.")
        self.cart_tree.heading("subtotal", text="Subtotal")
        self.cart_tree.heading("actions", text="Ações")

        self.cart_tree.column("product", width=400)
        self.cart_tree.column("qty", width=100, anchor=tk.E)
        self.cart_tree.column("cost", width=120, anchor=tk.E)
        self.cart_tree.column("subtotal", width=120, anchor=tk.E)
        self.cart_tree.column("actions", width=80, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(cart_frame, orient=tk.VERTICAL, command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=scrollbar.set)

        self.cart_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.cart_tree.bind('<Button-1>', self._on_cart_click)

        # Totals
        totals_frame = ttk.Frame(main_frame)
        totals_frame.pack(fill=tk.X, pady=(0, 10))

        self.total_var = tk.StringVar(value="0.00")
        ttk.Label(totals_frame, text="Total da Compra:", font=("", 11)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(totals_frame, textvariable=self.total_var, font=("", 12, "bold"), foreground="green").pack(side=tk.LEFT)

        # Notes
        notes_frame = ttk.Frame(main_frame)
        notes_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(notes_frame, text="Observações:").pack(side=tk.LEFT, padx=(0, 5))
        self.notes_var = tk.StringVar()
        ttk.Entry(notes_frame, textvariable=self.notes_var, width=60).pack(side=tk.LEFT)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Cancelar", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Salvar Compra", command=self._save_purchase, width=20).pack(side=tk.RIGHT)

    def _load_products(self):
        """Load products into combobox."""
        try:
            products = list_products()
            self.products_cache = {p.name: p for p in products if p.is_active}
            self.product_combobox['values'] = [p.name for p in products if p.is_active]
        except Exception as e:
            logger.exception("Error loading products")

    def _on_product_select(self, event):
        """Handle product selection."""
        product_name = self.product_var.get()
        if product_name in self.products_cache:
            product = self.products_cache[product_name]
            if product.cost_price:
                self.unit_cost_var.set(str(product.cost_price))
            self.quantity_var.set("1")

    def _add_to_cart(self):
        """Add product to cart."""
        product_name = self.product_var.get()
        if not product_name:
            messagebox.showwarning("Aviso", "Selecione um produto")
            return

        try:
            product = self.products_cache[product_name]
            quantity = float(self.quantity_var.get())
            unit_cost = float(self.unit_cost_var.get())

            if quantity <= 0:
                messagebox.showwarning("Aviso", "Quantidade deve ser maior que zero")
                return

            if unit_cost <= 0:
                messagebox.showwarning("Aviso", "Custo unitário deve ser maior que zero")
                return

            # Check if product already in cart
            for item in self.cart_items:
                if item['product_id'] == product.id:
                    item['quantity'] += quantity
                    item['unit_cost'] = unit_cost  # Update cost
                    break
            else:
                self.cart_items.append({
                    'product_id': product.id,
                    'name': product.name,
                    'quantity': quantity,
                    'unit_cost': unit_cost
                })

            self._refresh_cart()
            self.product_var.set("")
            self.unit_cost_var.set("0")
            self.quantity_var.set("1")

        except ValueError:
            messagebox.showerror("Erro", "Valores inválidos")

    def _on_cart_click(self, event):
        """Handle cart item click."""
        region = self.cart_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.cart_tree.identify_column(event.x)
            item = self.cart_tree.identify_row(event.y)

            if column == "#5":  # Actions column
                values = self.cart_tree.item(item)['values']
                product_name = values[0]
                # Remove from cart
                self.cart_items = [item for item in self.cart_items if item['name'] != product_name]
                self._refresh_cart()

    def _refresh_cart(self):
        """Refresh cart display."""
        # Clear cart
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)

        total = 0
        for item in self.cart_items:
            subtotal = item['quantity'] * item['unit_cost']
            total += subtotal

            self.cart_tree.insert("", tk.END, values=(
                item['name'],
                f"{item['quantity']:.2f}",
                f"{item['unit_cost']:.2f}",
                f"{subtotal:.2f}",
                "Remover"
            ))

        self.total_var.set(f"{total:.2f}")

    def _save_purchase(self):
        """Save the purchase."""
        if not self.cart_items:
            messagebox.showwarning("Aviso", "Adicione itens à compra")
            return

        try:
            items = [{
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'unit_cost': item['unit_cost']
            } for item in self.cart_items]

            notes = self.notes_var.get().strip() or None

            success, error, purchase_id = create_purchase(self.supplier_id, items, notes)

            if success:
                if self.callback:
                    self.callback()
                self.dialog.destroy()
                messagebox.showinfo("Sucesso", f"Compra registrada!\nID: {purchase_id}")
            else:
                messagebox.showerror("Erro", error or "Erro ao salvar compra")

        except Exception as e:
            logger.exception("Error saving purchase")
            messagebox.showerror("Erro", f"Erro ao salvar compra: {e}")


class PurchasesWindow:
    """Window for viewing purchases."""

    def __init__(self, parent, supplier_id: Optional[int] = None):
        """Initialize the purchases window.

        Args:
            parent: The parent Tkinter window
            supplier_id: Optional supplier ID to filter purchases
        """
        self.window = tk.Toplevel(parent)
        self.window.title("ERP Paraguay - Compras")
        self.window.geometry("1000x600")

        self.supplier_id = supplier_id

        self._build_ui()
        self._load_purchases()

    def _build_ui(self):
        """Build the user interface."""
        # Top frame
        top_frame = ttk.Frame(self.window, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Button(top_frame, text="Atualizar", command=self._load_purchases).pack(side=tk.LEFT)
        ttk.Button(top_frame, text="Ver Detalhes", command=self._view_details).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Receber Compra", command=self._receive_purchase).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="Fechar", command=self.window.destroy).pack(side=tk.LEFT)

        # Purchases table
        table_frame = ttk.Frame(self.window, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "supplier", "date", "total", "status")
        self.purchases_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=20
        )

        self.purchases_tree.heading("id", text="ID")
        self.purchases_tree.heading("supplier", text="Fornecedor")
        self.purchases_tree.heading("date", text="Data")
        self.purchases_tree.heading("total", text="Total")
        self.purchases_tree.heading("status", text="Status")

        self.purchases_tree.column("id", width=50, anchor=tk.CENTER)
        self.purchases_tree.column("supplier", width=250)
        self.purchases_tree.column("date", width=180)
        self.purchases_tree.column("total", width=120, anchor=tk.E)
        self.purchases_tree.column("status", width=120)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.purchases_tree.yview)
        self.purchases_tree.configure(yscrollcommand=scrollbar.set)

        self.purchases_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.purchases_tree.bind('<Double-Button-1>', lambda e: self._view_details())

    def _load_purchases(self):
        """Load purchases into table."""
        # Clear existing items
        for item in self.purchases_tree.get_children():
            self.purchases_tree.delete(item)

        try:
            purchases = list_purchases(supplier_id=self.supplier_id)
            for purchase in purchases:
                self.purchases_tree.insert("", tk.END, values=(
                    purchase.id,
                    purchase.supplier.name if purchase.supplier else "Unknown",
                    purchase.purchase_date.strftime("%Y-%m-%d %H:%M"),
                    f"{purchase.total:.2f}",
                    purchase.status
                ))
        except Exception as e:
            logger.exception("Error loading purchases")
            messagebox.showerror("Erro", f"Erro ao carregar compras: {e}")

    def _view_details(self):
        """View purchase details."""
        selection = self.purchases_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma compra")
            return

        item = self.purchases_tree.item(selection[0])
        purchase_id = item['values'][0]

        try:
            purchase = get_purchase_by_id(purchase_id)
            if purchase:
                PurchaseDetailsWindow(self.window, purchase)
            else:
                messagebox.showerror("Erro", "Compra não encontrada")
        except Exception as e:
            logger.exception("Error loading purchase details")
            messagebox.showerror("Erro", f"Erro ao carregar detalhes: {e}")

    def _receive_purchase(self):
        """Receive a purchase (update stock)."""
        selection = self.purchases_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma compra")
            return

        item = self.purchases_tree.item(selection[0])
        purchase_id = item['values'][0]
        status = item['values'][4]

        if status == 'received':
            messagebox.showinfo("Info", "Esta compra já foi recebida")
            return

        if not messagebox.askyesno("Confirmar", "Deseja receber esta compra e atualizar o estoque?"):
            return

        try:
            success, error = receive_purchase(purchase_id)
            if success:
                messagebox.showinfo("Sucesso", "Compra recebida e estoque atualizado")
                self._load_purchases()
            else:
                messagebox.showerror("Erro", error or "Erro ao receber compra")
        except Exception as e:
            logger.exception("Error receiving purchase")
            messagebox.showerror("Erro", f"Erro ao receber compra: {e}")


class PurchaseDetailsWindow:
    """Window for displaying purchase details."""

    def __init__(self, parent, purchase: dict):
        """Initialize purchase details window.

        Args:
            parent: The parent Tkinter window
            purchase: Purchase details dictionary
        """
        self.window = tk.Toplevel(parent)
        self.window.title(f"ERP Paraguay - Compra #{purchase['id']}")
        self.window.geometry("700x500")

        self.purchase = purchase
        self._build_ui()

    def _build_ui(self):
        """Build the user interface."""
        # Main container
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Purchase info
        info_frame = ttk.LabelFrame(main_frame, text="Informações da Compra", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(info_frame, text=f"ID: {self.purchase['id']}").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Fornecedor: {self.purchase['supplier_name']}").grid(row=0, column=1, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Data: {self.purchase['purchase_date'].strftime('%Y-%m-%d %H:%M')}").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Status: {self.purchase['status']}").grid(row=1, column=1, sticky=tk.W, pady=2)

        # Items
        items_frame = ttk.LabelFrame(main_frame, text="Itens da Compra", padding=10)
        items_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        columns = ("product", "qty", "cost", "subtotal")
        items_tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=10)

        items_tree.heading("product", text="Produto")
        items_tree.heading("qty", text="Quant.")
        items_tree.heading("cost", text="Custo Unit.")
        items_tree.heading("subtotal", text="Subtotal")

        for item in self.purchase['items']:
            items_tree.insert("", tk.END, values=(
                item['product_name'],
                f"{item['quantity']:.2f}",
                f"{item['unit_cost']:.2f}",
                f"{item['subtotal']:.2f}"
            ))

        items_tree.pack(fill=tk.BOTH, expand=True)

        # Totals
        totals_frame = ttk.Frame(main_frame)
        totals_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(totals_frame, text=f"Subtotal: {self.purchase['subtotal']:.2f}").pack(anchor=tk.W, pady=2)
        ttk.Label(totals_frame, text=f"TOTAL: {self.purchase['total']:.2f}", font=("", 12, "bold")).pack(anchor=tk.W, pady=5)

        # Notes
        if self.purchase.get('notes'):
            notes_frame = ttk.LabelFrame(main_frame, text="Observações", padding=10)
            notes_frame.pack(fill=tk.X)
            ttk.Label(notes_frame, text=self.purchase['notes']).pack(anchor=tk.W)

        # Close button
        ttk.Button(main_frame, text="Fechar", command=self.window.destroy).pack(pady=10)
