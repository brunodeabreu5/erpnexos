"""Sales management UI window for ERP Paraguay.

This module provides the user interface for the Point of Sale (POS) system.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.services.sales_management_service import (
    create_sale,
    get_sale_by_id,
    list_sales,
    cancel_sale,
    add_payment
)
from app.services.customer_service import list_customers, search_customers
from app.services.product_service import list_products, search_products
from app.reports.pdf_reports import generate_invoice
from app.settings import TaxSettings
from tkinter import filedialog

logger = logging.getLogger(__name__)


class SalesWindow:
    """Main POS window for creating sales."""

    def __init__(self, parent):
        """Initialize the sales window.

        Args:
            parent: The parent Tkinter window
        """
        self.window = tk.Toplevel(parent)
        self.window.title("ERP Paraguay - Nueva Venta")
        self.window.geometry("1100x700")

        # Cart items: List of dicts with product_id, name, quantity, unit_price, discount
        self.cart_items = []
        self.customers_cache = {}
        self.products_cache = {}

        self._build_ui()
        self._load_customers()
        self._load_products()

    def _build_ui(self):
        """Build the user interface."""
        # Main container
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top section - Customer and Product selection
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # Customer selection
        customer_frame = ttk.LabelFrame(top_frame, text="Cliente", padding=10)
        customer_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Label(customer_frame, text="Cliente:").grid(row=0, column=0, sticky=tk.W)
        self.customer_var = tk.StringVar()
        self.customer_combobox = ttk.Combobox(
            customer_frame,
            textvariable=self.customer_var,
            width=40,
            state='readonly'
        )
        self.customer_combobox.grid(row=0, column=1, padx=5, sticky=tk.EW)
        self.customer_combobox.bind('<<ComboboxSelected>>', self._on_customer_select)

        ttk.Button(customer_frame, text="Buscar", command=self._search_customer, width=8).grid(row=0, column=2, padx=5)

        # Product selection
        product_frame = ttk.LabelFrame(top_frame, text="Producto", padding=10)
        product_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        ttk.Label(product_frame, text="Producto:").grid(row=0, column=0, sticky=tk.W)
        self.product_var = tk.StringVar()
        self.product_combobox = ttk.Combobox(
            product_frame,
            textvariable=self.product_var,
            width=40,
            state='readonly'
        )
        self.product_combobox.grid(row=0, column=1, padx=5, sticky=tk.EW)
        self.product_combobox.bind('<<ComboboxSelected>>', self._on_product_select)

        ttk.Button(product_frame, text="Buscar", command=self._search_product, width=8).grid(row=0, column=2, padx=5)

        # Middle section - Add item details
        add_frame = ttk.LabelFrame(main_frame, text="Agregar Item", padding=10)
        add_frame.pack(fill=tk.X, pady=(0, 10))

        # Selected product info
        ttk.Label(add_frame, text="Producto seleccionado:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.selected_product_label = ttk.Label(add_frame, text="Ninguno", font=("", 9, "bold"))
        self.selected_product_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(add_frame, text="Cantidad:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.quantity_var = tk.StringVar(value="1")
        ttk.Entry(add_frame, textvariable=self.quantity_var, width=10).grid(row=0, column=3, padx=(0, 20))

        ttk.Label(add_frame, text="Descuento:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.item_discount_var = tk.StringVar(value="0")
        ttk.Entry(add_frame, textvariable=self.item_discount_var, width=10).grid(row=0, column=5, padx=(0, 20))

        ttk.Button(add_frame, text="Agregar al Carrito", command=self._add_to_cart).grid(row=0, column=6)

        # Cart section
        cart_frame = ttk.LabelFrame(main_frame, text="Carrito de Compras", padding=10)
        cart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        columns = ("product", "qty", "price", "discount", "total", "actions")
        self.cart_tree = ttk.Treeview(cart_frame, columns=columns, show="headings", height=10)

        self.cart_tree.heading("product", text="Producto")
        self.cart_tree.heading("qty", text="Cant.")
        self.cart_tree.heading("price", text="Precio Unit.")
        self.cart_tree.heading("discount", text="Descuento")
        self.cart_tree.heading("total", text="Total")
        self.cart_tree.heading("actions", text="Acciones")

        self.cart_tree.column("product", width=300)
        self.cart_tree.column("qty", width=80, anchor=tk.E)
        self.cart_tree.column("price", width=100, anchor=tk.E)
        self.cart_tree.column("discount", width=100, anchor=tk.E)
        self.cart_tree.column("total", width=100, anchor=tk.E)
        self.cart_tree.column("actions", width=80, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(cart_frame, orient=tk.VERTICAL, command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=scrollbar.set)

        self.cart_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Totals section
        totals_frame = ttk.Frame(main_frame)
        totals_frame.pack(fill=tk.X, pady=(0, 10))

        self.subtotal_var = tk.StringVar(value="0.00")
        self.tax_var = tk.StringVar(value="0.00")
        self.discount_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")

        ttk.Label(totals_frame, text="Subtotal:", font=("", 10)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(totals_frame, textvariable=self.subtotal_var, font=("", 10, "bold"), width=12).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(totals_frame, text=f"{TaxSettings.get_display_string()}:", font=("", 10)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(totals_frame, textvariable=self.tax_var, font=("", 10), width=12).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(totals_frame, text="Descuento:", font=("", 10)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(totals_frame, textvariable=self.discount_var, font=("", 10), width=12).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(totals_frame, text="TOTAL:", font=("", 12, "bold")).pack(side=tk.LEFT, padx=(20, 5))
        ttk.Label(totals_frame, textvariable=self.total_var, font=("", 14, "bold"), foreground="green", width=15).pack(side=tk.LEFT)

        # Bottom section - Payment and finalize
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)

        # Payment method
        payment_frame = ttk.LabelFrame(bottom_frame, text="Método de Pago", padding=10)
        payment_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.payment_method = tk.StringVar(value="cash")
        ttk.Radiobutton(payment_frame, text="Contado", variable=self.payment_method, value="cash").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(payment_frame, text="Tarjeta", variable=self.payment_method, value="card").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(payment_frame, text="Transferencia", variable=self.payment_method, value="transfer").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(payment_frame, text="Crédito", variable=self.payment_method, value="credit").pack(side=tk.LEFT, padx=5)

        # Overall discount
        discount_frame = ttk.LabelFrame(bottom_frame, text="Descuento General", padding=10)
        discount_frame.pack(side=tk.LEFT, fill=tk.X, padx=(5, 5))

        ttk.Label(discount_frame, text="Monto:").pack(side=tk.LEFT, padx=(0, 5))
        self.overall_discount_var = tk.StringVar(value="0")
        ttk.Entry(discount_frame, textvariable=self.overall_discount_var, width=10).pack(side=tk.LEFT)
        ttk.Button(discount_frame, text="Aplicar", command=self._apply_overall_discount, width=8).pack(side=tk.LEFT, padx=(5, 0))

        # Action buttons
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(side=tk.LEFT, padx=(5, 0))

        ttk.Button(button_frame, text="Cancelar", command=self._clear_sale).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Finalizar Venta", command=self._finalize_sale, width=20).pack(side=tk.LEFT)

        self.selected_product = None

    def _load_customers(self):
        """Load customers into combobox."""
        try:
            customers = list_customers(active_only=True)
            self.customers_cache = {c.name: c for c in customers}
            self.customer_combobox['values'] = [c.name for c in customers]
        except Exception as e:
            logger.exception("Error loading customers")

    def _load_products(self):
        """Load products into combobox."""
        try:
            products = list_products()
            self.products_cache = {p.name: p for p in products if p.is_active}
            self.product_combobox['values'] = [p.name for p in products if p.is_active]
        except Exception as e:
            logger.exception("Error loading products")

    def _on_customer_select(self, event):
        """Handle customer selection."""
        pass  # Customer is already selected via combobox

    def _on_product_select(self, event):
        """Handle product selection."""
        product_name = self.product_var.get()
        if product_name in self.products_cache:
            self.selected_product = self.products_cache[product_name]
            self.selected_product_label.config(text=f"{self.selected_product.name} (${self.selected_product.price})")
            self.quantity_var.set("1")
            self.item_discount_var.set("0")

    def _search_customer(self):
        """Search for customers."""
        search_window = tk.Toplevel(self.window)
        search_window.title("Buscar Cliente")
        search_window.geometry("500x300")
        search_window.transient(self.window)
        search_window.grab_set()

        ttk.Label(search_window, text="Buscar:").pack(pady=10)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_window, textvariable=search_var, width=40)
        search_entry.pack(pady=5)
        search_entry.focus()

        results_tree = ttk.Treeview(search_window, columns=("name", "email", "phone"), show="headings", height=10)
        results_tree.heading("name", text="Nome")
        results_tree.heading("email", text="Email")
        results_tree.heading("phone", text="Telefone")
        results_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def do_search():
            term = search_var.get().strip()
            if not term:
                return

            for item in results_tree.get_children():
                results_tree.delete(item)

            try:
                customers = search_customers(term, active_only=True)
                for customer in customers:
                    results_tree.insert("", tk.END, values=(
                        customer.name,
                        customer.email or "-",
                        customer.phone or "-"
                    ))
            except Exception as e:
                logger.exception("Error searching customers")

        def select_customer():
            selection = results_tree.selection()
            if selection:
                item = results_tree.item(selection[0])
                name = item['values'][0]
                self.customer_var.set(name)
                search_window.destroy()

        search_entry.bind('<KeyRelease>', lambda e: do_search() if len(search_var.get()) >= 2 else None)

        button_frame = ttk.Frame(search_window)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Seleccionar", command=select_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cerrar", command=search_window.destroy).pack(side=tk.LEFT, padx=5)

    def _search_product(self):
        """Search for products."""
        search_window = tk.Toplevel(self.window)
        search_window.title("Buscar Producto")
        search_window.geometry("500x300")
        search_window.transient(self.window)
        search_window.grab_set()

        ttk.Label(search_window, text="Buscar:").pack(pady=10)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_window, textvariable=search_var, width=40)
        search_entry.pack(pady=5)
        search_entry.focus()

        results_tree = ttk.Treeview(search_window, columns=("name", "sku", "price", "stock"), show="headings", height=10)
        results_tree.heading("name", text="Nome")
        results_tree.heading("sku", text="SKU")
        results_tree.heading("price", text="Preço")
        results_tree.heading("stock", text="Stock")
        results_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def do_search():
            term = search_var.get().strip()
            if not term:
                return

            for item in results_tree.get_children():
                results_tree.delete(item)

            try:
                products = search_products(term, active_only=True)
                for product in products:
                    results_tree.insert("", tk.END, values=(
                        product.name,
                        product.sku or "-",
                        f"${product.price}",
                        f"{product.stock}"
                    ))
            except Exception as e:
                logger.exception("Error searching products")

        def select_product():
            selection = results_tree.selection()
            if selection:
                item = results_tree.item(selection[0])
                name = item['values'][0]
                self.product_var.set(name)
                self._on_product_select(None)
                search_window.destroy()

        search_entry.bind('<KeyRelease>', lambda e: do_search() if len(search_var.get()) >= 2 else None)

        button_frame = ttk.Frame(search_window)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Seleccionar", command=select_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cerrar", command=search_window.destroy).pack(side=tk.LEFT, padx=5)

    def _add_to_cart(self):
        """Add selected product to cart."""
        if not self.selected_product:
            messagebox.showwarning("Aviso", "Seleccione un producto")
            return

        try:
            quantity = float(self.quantity_var.get())
            if quantity <= 0:
                messagebox.showwarning("Aviso", "Cantidad debe ser mayor a cero")
                return

            if quantity > self.selected_product.stock:
                messagebox.showwarning("Aviso", f"Stock insuficiente. Disponible: {self.selected_product.stock}")
                return

            discount = float(self.item_discount_var.get())

            # Check if product already in cart
            for item in self.cart_items:
                if item['product_id'] == self.selected_product.id:
                    item['quantity'] += quantity
                    item['discount'] += discount
                    break
            else:
                self.cart_items.append({
                    'product_id': self.selected_product.id,
                    'name': self.selected_product.name,
                    'quantity': quantity,
                    'unit_price': float(self.selected_product.price),
                    'discount': discount
                })

            self._refresh_cart()
            self._clear_product_selection()

        except ValueError:
            messagebox.showerror("Erro", "Valores inválidos")

    def _remove_from_cart(self, product_id):
        """Remove item from cart."""
        self.cart_items = [item for item in self.cart_items if item['product_id'] != product_id]
        self._refresh_cart()

    def _refresh_cart(self):
        """Refresh cart display and totals."""
        # Clear cart
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)

        subtotal = Decimal('0')
        total_item_discount = Decimal('0')

        # Add items to cart
        for item in self.cart_items:
            item_subtotal = Decimal(str(item['quantity'])) * Decimal(str(item['unit_price']))
            item_total = item_subtotal - Decimal(str(item['discount']))
            subtotal += item_total
            total_item_discount += Decimal(str(item['discount']))

            self.cart_tree.insert("", tk.END, values=(
                item['name'],
                f"{item['quantity']:.2f}",
                f"${item['unit_price']:.2f}",
                f"${item['discount']:.2f}",
                f"${item_total:.2f}",
                "Remover"
            ), tags=(str(item['product_id']),))

        # Bind click event for remove button
        self.cart_tree.bind('<Button-1>', self._on_cart_click)

        # Apply overall discount
        overall_discount = Decimal(self.overall_discount_var.get() or "0")
        discounted_subtotal = max(subtotal - overall_discount, Decimal('0'))

        # Calculate tax
        tax = discounted_subtotal * Decimal(str(TaxSettings.RATE))

        # Calculate total
        total = discounted_subtotal + tax

        # Update totals display
        self.subtotal_var.set(f"{subtotal:.2f}")
        self.discount_var.set(f"{total_item_discount + overall_discount:.2f}")
        self.tax_var.set(f"{tax:.2f}")
        self.total_var.set(f"{total:.2f}")

    def _on_cart_click(self, event):
        """Handle cart item click."""
        region = self.cart_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.cart_tree.identify_column(event.x)
            item = self.cart_tree.identify_row(event.y)

            if column == "#6":  # Actions column
                values = self.cart_tree.item(item)['values']
                product_id = self.cart_tree.item(item)['tags'][0]
                self._remove_from_cart(int(product_id))

    def _apply_overall_discount(self):
        """Apply overall discount and refresh totals."""
        try:
            discount = float(self.overall_discount_var.get() or "0")
            if discount < 0:
                messagebox.showwarning("Aviso", "Descuento no puede ser negativo")
                return
            self._refresh_cart()
        except ValueError:
            messagebox.showerror("Erro", "Valor de descuento inválido")

    def _clear_product_selection(self):
        """Clear product selection."""
        self.selected_product = None
        self.product_var.set("")
        self.selected_product_label.config(text="Ninguno")
        self.quantity_var.set("1")
        self.item_discount_var.set("0")

    def _clear_sale(self):
        """Clear entire sale."""
        if not messagebox.askyesno("Confirmar", "¿Desea cancelar la venta actual?"):
            return

        self.cart_items = []
        self._refresh_cart()
        self._clear_product_selection()
        self.customer_var.set("")
        self.overall_discount_var.set("0")
        self.payment_method.set("cash")

    def _finalize_sale(self):
        """Finalize the sale."""
        # Validate customer
        customer_name = self.customer_var.get()
        if not customer_name:
            messagebox.showwarning("Aviso", "Seleccione un cliente")
            return

        customer = self.customers_cache.get(customer_name)
        if not customer:
            messagebox.showerror("Erro", "Cliente no encontrado")
            return

        # Validate cart
        if not self.cart_items:
            messagebox.showwarning("Aviso", "El carrito está vacío")
            return

        # Prepare items for API
        items = [{
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'unit_price': item['unit_price'],
            'discount': item['discount']
        } for item in self.cart_items]

        # Get overall discount
        overall_discount = float(self.overall_discount_var.get() or "0")

        try:
            success, error, sale_id = create_sale(
                customer_id=customer.id,
                items=items,
                payment_method=self.payment_method.get(),
                discount=overall_discount
            )

            if success:
                messagebox.showinfo("Sucesso", f"Venta realizada con éxito!\nID de Venta: {sale_id}")
                self._clear_sale()
            else:
                messagebox.showerror("Erro", error or "Error al realizar venta")

        except Exception as e:
            logger.exception("Error finalizing sale")
            messagebox.showerror("Erro", f"Error al realizar venta: {e}")


class SalesListWindow:
    """Window for listing and viewing sales."""

    def __init__(self, parent):
        """Initialize the sales list window.

        Args:
            parent: The parent Tkinter window
        """
        self.window = tk.Toplevel(parent)
        self.window.title("ERP Paraguay - Lista de Ventas")
        self.window.geometry("1000x600")

        self._build_ui()
        self._load_sales()

    def _build_ui(self):
        """Build the user interface."""
        # Top frame with filters
        top_frame = ttk.Frame(self.window, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Button(top_frame, text="Actualizar", command=self._load_sales).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(top_frame, text="Ver Detalles", command=self._view_details).pack(side=tk.LEFT, padx=(0, 10))

        # Sales table
        table_frame = ttk.Frame(self.window, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "date", "customer", "total", "payment_method", "payment_status", "status")
        self.sales_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=20
        )

        self.sales_tree.heading("id", text="ID")
        self.sales_tree.heading("date", text="Data")
        self.sales_tree.heading("customer", text="Cliente")
        self.sales_tree.heading("total", text="Total")
        self.sales_tree.heading("payment_method", text="Método")
        self.sales_tree.heading("payment_status", text="Estado Pag.")
        self.sales_tree.heading("status", text="Estado")

        self.sales_tree.column("id", width=50, anchor=tk.CENTER)
        self.sales_tree.column("date", width=150)
        self.sales_tree.column("customer", width=200)
        self.sales_tree.column("total", width=100, anchor=tk.E)
        self.sales_tree.column("payment_method", width=100)
        self.sales_tree.column("payment_status", width=100)
        self.sales_tree.column("status", width=100)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=scrollbar.set)

        self.sales_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Double click to view details
        self.sales_tree.bind('<Double-Button-1>', lambda e: self._view_details())

    def _load_sales(self):
        """Load sales into table."""
        # Clear existing items
        for item in self.sales_tree.get_children():
            self.sales_tree.delete(item)

        try:
            sales = list_sales()
            for sale in sales:
                customer_name = sale.customer.name if sale.customer else "Unknown"
                self.sales_tree.insert("", tk.END, values=(
                    sale.id,
                    sale.sale_date.strftime("%Y-%m-%d %H:%M"),
                    customer_name,
                    f"${sale.total:.2f}",
                    sale.payment_method,
                    sale.payment_status,
                    sale.status
                ))
        except Exception as e:
            logger.exception("Error loading sales")
            messagebox.showerror("Erro", f"Erro ao carregar vendas: {e}")

    def _view_details(self):
        """View sale details."""
        selection = self.sales_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Seleccione una venta")
            return

        item = self.sales_tree.item(selection[0])
        sale_id = item['values'][0]

        try:
            sale = get_sale_by_id(sale_id)
            if sale:
                SaleDetailsWindow(self.window, sale)
            else:
                messagebox.showerror("Erro", "Venta no encontrada")
        except Exception as e:
            logger.exception("Error loading sale details")
            messagebox.showerror("Erro", f"Erro ao carregar detalhes: {e}")


class SaleDetailsWindow:
    """Window for displaying sale details."""

    def __init__(self, parent, sale: Dict[str, Any]):
        """Initialize sale details window.

        Args:
            parent: The parent Tkinter window
            sale: Sale details dictionary
        """
        self.window = tk.Toplevel(parent)
        self.window.title(f"ERP Paraguay - Venta #{sale['id']}")
        self.window.geometry("700x600")

        self.sale = sale
        self._build_ui()

    def _build_ui(self):
        """Build the user interface."""
        # Main container with scrollbar
        canvas = tk.Canvas(self.window)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Sale info
        info_frame = ttk.LabelFrame(scrollable_frame, text="Información de la Venta", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(info_frame, text=f"ID: {self.sale['id']}").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Cliente: {self.sale['customer_name']}").grid(row=0, column=1, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Data: {self.sale['sale_date'].strftime('%Y-%m-%d %H:%M')}").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Método de Pago: {self.sale['payment_method']}").grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Estado: {self.sale['status']}").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Estado de Pagamento: {self.sale['payment_status']}").grid(row=2, column=1, sticky=tk.W, pady=2)

        # Items
        items_frame = ttk.LabelFrame(scrollable_frame, text="Itens da Venta", padding=10)
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("product", "qty", "price", "discount", "total")
        items_tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=8)

        items_tree.heading("product", text="Producto")
        items_tree.heading("qty", text="Cant.")
        items_tree.heading("price", text="Precio Unit.")
        items_tree.heading("discount", text="Descuento")
        items_tree.heading("total", text="Total")

        for item in self.sale['items']:
            items_tree.insert("", tk.END, values=(
                item['product_name'],
                f"{item['quantity']:.2f}",
                f"${item['unit_price']:.2f}",
                f"${item['discount']:.2f}",
                f"${item['total']:.2f}"
            ))

        items_tree.pack(fill=tk.BOTH, expand=True)

        # Totals
        totals_frame = ttk.LabelFrame(scrollable_frame, text="Totales", padding=10)
        totals_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(totals_frame, text=f"Subtotal: ${self.sale['subtotal']:.2f}").pack(anchor=tk.W, pady=2)
        ttk.Label(totals_frame, text=f"IVA: ${self.sale['tax_amount']:.2f}").pack(anchor=tk.W, pady=2)
        ttk.Label(totals_frame, text=f"Descuento: ${self.sale['discount_amount']:.2f}").pack(anchor=tk.W, pady=2)
        ttk.Label(totals_frame, text=f"TOTAL: ${self.sale['total']:.2f}", font=("", 12, "bold")).pack(anchor=tk.W, pady=5)

        # Payments
        if self.sale['payments']:
            payments_frame = ttk.LabelFrame(scrollable_frame, text="Pagos", padding=10)
            payments_frame.pack(fill=tk.X, padx=10, pady=10)

            for payment in self.sale['payments']:
                ttk.Label(payments_frame, text=f"${payment['amount']:.2f} - {payment['payment_method']} - {payment['payment_date'].strftime('%Y-%m-%d')}").pack(anchor=tk.W, pady=2)

        ttk.Label(totals_frame, text=f"Total Pagado: ${self.sale['amount_paid']:.2f}").pack(anchor=tk.W, pady=2)
        if self.sale['balance_due'] > 0:
            ttk.Label(totals_frame, text=f"Saldo Pendiente: ${self.sale['balance_due']:.2f}", foreground="red").pack(anchor=tk.W, pady=2)

        # Notes
        if self.sale.get('notes'):
            notes_frame = ttk.LabelFrame(scrollable_frame, text="Notas", padding=10)
            notes_frame.pack(fill=tk.X, padx=10, pady=10)
            ttk.Label(notes_frame, text=self.sale['notes']).pack(anchor=tk.W)

        # Buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def print_invoice():
            try:
                path = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF", "*.pdf")],
                    initialfile=f"factura_{self.sale['id']}.pdf",
                )
                if path:
                    generate_invoice(path, self.sale['id'])
                    messagebox.showinfo("Sucesso", f"Factura guardada:\n{path}")
            except Exception as e:
                logger.exception("Error generating invoice")
                messagebox.showerror("Erro", f"Error al generar factura: {e}")

        ttk.Button(button_frame, text="Imprimir Factura", command=print_invoice).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cerrar", command=self.window.destroy).pack(side=tk.RIGHT)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
