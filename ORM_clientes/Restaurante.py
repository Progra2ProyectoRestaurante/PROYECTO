# Restaurante.py - Aplicación principal
# Correcciones aplicadas: 
# - llamadas correctas a Menu.disponibles_segun_stock(self.stock)
# - sin uso incorrecto de self.db en lógica local
# - compatibilidad total con Stock, Menu, Pedido
# - visualización intacta

import os, csv, tempfile
import re
import customtkinter as ctk
from typing import Dict
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import fitz  # PyMuPDF

from logic.Stock import Stock
from logic.Menu import poblar_db_con_menus_estaticos
from logic.Pedido import Pedido
from utils.Menupdf import generar_carta_pdf
from utils.Boleta import Boleta
import models
import graficos

APP_W, APP_H = 1200, 640

class RestauranteApp(ctk.CTk):
    def __init__(self, db=None):
        self.db = db
        super().__init__()
        self.title("Restaurante - Evaluación 2")
        self.geometry(f"{APP_W}x{APP_H}")
        self.resizable(False, False)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.stock = Stock()
        self.pedido = Pedido(self.stock, db=self.db)

        self.img_dir = os.path.join(os.path.dirname(__file__), "img")
        self.menu_images = self._cargar_imagenes_menus()

        self.tabs = ctk.CTkTabview(self, width=APP_W - 20, height=APP_H - 40)
        self.tabs.pack(padx=10, pady=10)

        # Orden: Carga, Stock, Carta, Clientes, Pedido, Boleta, Gráficos
        for nombre in ("Carga de ingredientes", "Stock", "Carta restaurant", "Clientes", "Pedido", "Boleta", "Gráficos"):
            self.tabs.add(nombre)

        self._init_tab_csv()
        self._init_tab_stock()
        self._init_tab_carta()
        self._init_tab_clientes()
        self._init_tab_pedido()
        self._init_tab_boleta()
        self._init_tab_graficos()

        self._carta_temp_pdf = None
        self._boleta_temp_pdf = None
        self._menu_interno = None  # Menús disponibles según stock


    # ==========================================
    # UTILIDADES
    # ==========================================

    def _cargar_imagenes_menus(self):
        imgs = {}
        search_dirs = []

        if os.path.isdir(self.img_dir):
            search_dirs.append(self.img_dir)

        root_dir = os.path.dirname(__file__)
        if root_dir not in search_dirs:
            search_dirs.append(root_dir)

        def candidate_paths_in_dir(name_base: str, dir_path: str):
            exts = [".png", ".jpg", ".jpeg"]
            variants = [
                name_base.lower(),
                name_base.lower().replace(" ", "_"),
                name_base.lower().replace(" ", "-"),
                name_base.lower().replace(" ", "")
            ]
            for v in variants:
                for e in exts:
                    yield os.path.join(dir_path, f"{v}{e}")

        files = []
        for d in search_dirs:
            try:
                for f in os.listdir(d):
                    if os.path.isfile(os.path.join(d, f)):
                        files.append((d, f))
            except Exception:
                continue

        # Obtener nombres de menús desde la base de datos
        from crud.menu_crud import listar_menus
        nombres_menus = [m.nombre for m in listar_menus(self.db)]

        for m in nombres_menus:
            found = None
            base = m.strip().lower()

            for d in search_dirs:
                for p in candidate_paths_in_dir(base, d):
                    if os.path.exists(p):
                        found = p
                        break
                if found:
                    break

            if not found:
                tokens = [t for t in base.replace("-", " ").replace("_", " ").split() if len(t) > 2]
                for d, f in files:
                    lf = f.lower()
                    for tok in tokens:
                        if tok in lf:
                            found = os.path.join(d, f)
                            break
                    if found:
                        break

            if found:
                try:
                    pil_img = Image.open(found).convert("RGBA")
                    pil_img = pil_img.resize((110, 82), Image.LANCZOS)
                    imgs[m] = ctk.CTkImage(pil_img, size=(110, 82))
                except:
                    pass

        return imgs


    def _estilizar_tree(self, tree):
        st = ttk.Style()
        st.theme_use("clam")
        st.configure("Treeview",
                     background="#2a2f38",
                     fieldbackground="#2a2f38",
                     foreground="#e6e6e6",
                     rowheight=26,
                     borderwidth=0)
        st.configure("Treeview.Heading",
                     background="#3b4252",
                     foreground="#e6e6e6",
                     font=("Segoe UI", 10, "bold"))
        st.map("Treeview",
               background=[("selected", "#1e88e5")])

        tree.tag_configure("odd", background="#2e3440")
        tree.tag_configure("even", background="#2a2f38")
    
        # ==========================================
    # TAB: CARGA DE INGREDIENTES (CSV)
    # ==========================================

    def _init_tab_csv(self):
        f = self.tabs.tab("Carga de ingredientes")

        bar = ctk.CTkFrame(f)
        bar.pack(fill="x", pady=8)

        ctk.CTkButton(bar, text="Cargar CSV", command=self.cargar_csv).pack(side="left", padx=6)
        ctk.CTkButton(bar, text="Agregar al Stock", command=self.agregar_csv_a_stock).pack(side="left", padx=6)

        self.tree_csv = ttk.Treeview(
            f, columns=("nombre", "unidad", "cantidad"),
            show="headings",
            height=16
        )

        for col, w, a in (("nombre", 520, "w"), ("unidad", 160, "center"), ("cantidad", 160, "e")):
            self.tree_csv.heading(col, text=col.upper())
            self.tree_csv.column(col, width=w, anchor=a, stretch=False)

        self._estilizar_tree(self.tree_csv)
        self.tree_csv.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        vs = ttk.Scrollbar(f, orient="vertical", command=self.tree_csv.yview)
        self.tree_csv.configure(yscrollcommand=vs.set)
        vs.place(in_=self.tree_csv, relx=1, rely=0, relheight=1, x=-1)


    def cargar_csv(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar ingredientes_menu.csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")]
        )
        if not ruta:
            return

        with open(ruta, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))

        if not rows:
            messagebox.showerror("Error", "CSV vacío.")
            return

        hdr = [h.strip().lower() for h in rows[0]]

        def idx(c):
            return hdr.index(c) if c in hdr else None

        iN, iU, iC = idx("nombre"), idx("unidad"), idx("cantidad")

        if None in (iN, iU, iC):
            iN, iU, iC = 0, 1, 2

        for i in self.tree_csv.get_children():
            self.tree_csv.delete(i)

        for k, r in enumerate(rows[1:]):
            if not r:
                continue

            vals = [
                (r[iN] if iN < len(r) else "").strip(),
                (r[iU] if iU < len(r) else "").strip(),
                (r[iC] if iC < len(r) else "0").strip().replace(",", "."),
            ]

            self.tree_csv.insert("", "end", values=vals, tags=("even" if k % 2 == 0 else "odd",))

        self.csv_path = ruta


    def agregar_csv_a_stock(self):
        if not hasattr(self, "csv_path"):
            messagebox.showwarning("Atención", "Primero cargue un CSV.")
            return


        with open(self.csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if self.db:
                from crud.ingrediente_crud import crear_ingrediente
            for row in reader:
                nombre = (row.get("nombre") or "").strip().lower()
                unidad = (row.get("unidad") or "").strip()
                cant = (row.get("cantidad") or "0").strip().replace(",", ".")

                try:
                    cant = float(cant)
                except:
                    cant = float((cant.lower().replace("x", "") or 0))

                if nombre:
                    self.stock.agregar_o_sumar(nombre, unidad, cant)
                    if self.db:
                        crear_ingrediente(self.db, nombre, unidad, cant)

        messagebox.showinfo("OK", "Ingredientes cargados al stock y base de datos.")
        self._refrescar_stock()
        self._refrescar_pedido_cards()


    # ==========================================
    # TAB: STOCK
    # ==========================================

    def _init_tab_stock(self):
        f = self.tabs.tab("Stock")

        container = ctk.CTkFrame(f)
        container.pack(fill="both", expand=True, padx=8, pady=8)

        # ---- LEFT ----
        left_frame = ctk.CTkFrame(container, width=100)
        left_frame.pack(side="left", fill="y", padx=(0, 8), pady=4)

        grid = ctk.CTkFrame(left_frame)
        grid.pack(padx=8, pady=8, anchor="n")

        ctk.CTkLabel(grid, text="Nombre del Ingrediente").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(grid, text="Unidad").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ctk.CTkLabel(grid, text="Cantidad").grid(row=4, column=0, sticky="w", pady=(8, 0))

        self.var_nombre = ctk.StringVar()
        self.var_cantidad = ctk.StringVar()
        self.cmb_unidad = ctk.CTkComboBox(grid, values=["kg", "unid"], state="readonly", width=120)
        self.cmb_unidad.set("kg")

        ctk.CTkEntry(grid, textvariable=self.var_nombre, width=260, placeholder_text="ej: oregano").grid(row=1, column=0, pady=(4, 0))
        self.cmb_unidad.grid(row=3, column=0, pady=(4, 0))

        ctk.CTkEntry(grid, textvariable=self.var_cantidad, width=120, placeholder_text="ej: 1").grid(row=5, column=0, pady=(4, 0))
        ctk.CTkButton(grid, text="Ingresar Ingrediente", command=self._stock_agregar).grid(row=6, column=0, pady=(12, 0))

        # ---- CENTER ----
        center_frame = ctk.CTkFrame(container)
        center_frame.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=4)

        self.tree_stock = ttk.Treeview(
            center_frame,
            columns=("nombre", "unidad", "cantidad"),
            show="headings",
            height=18
        )

        for col, w, a in (("nombre", 270, "w"), ("unidad", 120, "center"), ("cantidad", 120, "e")):
            self.tree_stock.heading(col, text=col.capitalize())
            self.tree_stock.column(col, width=w, anchor=a, stretch=False)

        self._estilizar_tree(self.tree_stock)
        self.tree_stock.pack(fill="both", expand=True, padx=8, pady=8)

        vs = ttk.Scrollbar(center_frame, orient="vertical", command=self.tree_stock.yview)
        self.tree_stock.configure(yscrollcommand=vs.set)
        vs.pack(side="right", fill="y")

        # ---- RIGHT ----
        right_frame = ctk.CTkFrame(container, width=320)
        right_frame.pack(side="right", fill="y", padx=(12, 0), pady=8)

        ctk.CTkButton(right_frame, text="Eliminar Ingrediente", command=self._stock_eliminar, width=180).pack(pady=(20, 8))

        self.btn_generar_menu = ctk.CTkButton(right_frame, text="Generar Menú", command=self._generar_menu_interno, width=180)
        self.btn_generar_menu.pack(pady=8)

        self.lbl_menu_interno = ctk.CTkLabel(right_frame, text="Menú interno: (no generado)")
        self.lbl_menu_interno.pack(pady=(12, 0), padx=8)
    # ==========================================
    # FUNCIONES STOCK
    # ==========================================    
    def _stock_agregar(self):
        nombre = self.var_nombre.get().strip().lower()
        unidad = self.cmb_unidad.get().strip()
        try:
            cantidad = float(self.var_cantidad.get().replace(",", "."))
        except Exception:
            cantidad = 0
        if not nombre:
            messagebox.showwarning("Atención", "Ingrese el nombre del ingrediente.")
            return
        if not unidad:
            messagebox.showwarning("Atención", "Seleccione la unidad.")
            return
        if cantidad <= 0:
            messagebox.showwarning("Atención", "Ingrese una cantidad positiva.")
            return
        # Guardar en la base de datos
        if self.db:
            from crud.ingrediente_crud import crear_ingrediente
            ingr = crear_ingrediente(self.db, nombre, unidad, cantidad)
            if ingr is None:
                messagebox.showerror("Error", "No se pudo agregar o actualizar el ingrediente en la base de datos.")
        # También mantener en memoria para lógica local
        self.stock.agregar_o_sumar(nombre, unidad, cantidad)
        self._refrescar_stock()
        self._refrescar_pedido_cards()

    def _carta_agregar_menu(self, nombre, precio):
        if not nombre or precio is None or precio <= 0:
            messagebox.showwarning("Atención", "Nombre y precio válidos requeridos.")
            return None
        if self.db:
            from crud.menu_crud import crear_menu
            menu = crear_menu(self.db, nombre, precio)
            if menu is None:
                messagebox.showerror("Error", "No se pudo crear el menú en la base de datos.")
            return menu
        return None

    def _carta_agregar_ingrediente_a_menu(self, menu_id, ingrediente_id, cantidad):
        if self.db:
            from crud.menu_crud import agregar_ingrediente_a_menu
            ok = agregar_ingrediente_a_menu(self.db, menu_id, ingrediente_id, cantidad)
            if not ok:
                messagebox.showerror("Error", "No se pudo asociar el ingrediente al menú en la base de datos.")

    # Puedes llamar a estos métodos desde la interfaz de carta/menú según tu lógica de UI.

    def _stock_eliminar(self):
        sel = self.tree_stock.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un ingrediente para eliminar.")
            return
        nombre = self.tree_stock.item(sel[0], "values")[0]
        self.stock.eliminar(nombre)
        if self.db:
            from crud.ingrediente_crud import eliminar_ingrediente
            eliminar_ingrediente(self.db, nombre)
        self._refrescar_stock()
        self._refrescar_pedido_cards()

    def _stock_restar(self):
        nombre = self.var_nombre.get().strip()
        try:
            cant = float(self.var_cantidad.get().replace(",", "."))
        except:
            cant = 0

        if not nombre:
            messagebox.showwarning("Atención", "Ingrese nombre.")
            return

        if cant <= 0:
            messagebox.showwarning("Atención", "Ingrese una cantidad positiva.")
            return

        if self.stock.cantidad_de(nombre) < cant:
            messagebox.showerror("Error", f"No hay suficiente stock de '{nombre}'.")
            return

        self.stock._items[nombre.lower()].descontar(cant)
        self._refrescar_stock()
        self._refrescar_pedido_cards()


    def _refrescar_stock(self):
        for i in self.tree_stock.get_children():
            self.tree_stock.delete(i)

        for k, ing in enumerate(self.stock.listar()):
            self.tree_stock.insert(
                "",
                "end",
                values=(ing.nombre, ing.unidad, f"{ing.cantidad:g}"),
                tags=("even" if k % 2 == 0 else "odd",)
            )

    # ==========================================
    # GENERAR MENÚ INTERNO
    # ==========================================

    def _generar_menu_interno(self):
        # Calcula qué menús pueden prepararse con el stock actual usando la base de datos
        from crud.menu_crud import listar_menus, requerimientos_menu
        menus = listar_menus(self.db)
        disp = []
        no_disp = []
        for menu in menus:
            reqs = requerimientos_menu(self.db, menu.id)
            if self.stock.validar_stock(reqs):
                disp.append(menu.nombre)
            else:
                no_disp.append(menu.nombre)
        self._menu_interno = disp  # 💾 SE GUARDA AQUÍ

        for m in no_disp:
            reqs = requerimientos_menu(self.db, next(menu.id for menu in menus if menu.nombre == m))
            faltas = self.stock.faltantes(reqs)
            if faltas:
                txt = ", ".join([f"{i} (req {r:g}, disp {d:g})" for i, r, d in faltas])
                print(f"[ALERTA] Faltan ingredientes para {m} → {txt}")

        # Actualizar etiqueta
        try:
            self.lbl_menu_interno.configure(text=f"Menú interno: {len(disp)} items")
        except:
            pass

        messagebox.showinfo("OK", f"Menú interno generado ({len(disp)} items).")


    # ==========================================
    # TAB: CARTA RESTAURANT
    # ==========================================



    def _init_tab_carta(self):
        f = self.tabs.tab("Carta restaurant")

        bar = ctk.CTkFrame(f)
        bar.pack(fill="x", pady=8)

        ctk.CTkButton(
            bar,
            text="Generar Carta (PDF)",
            command=self._generar_y_ver_carta
        ).pack(side="left", padx=6)

        # Selector de menú
        if self.db:
            from crud.menu_crud import listar_menus
            self.menu_selector_var = ctk.StringVar()
            self._actualizar_menu_selector()
            self.menu_selector.pack(side="left", padx=8)

        # Formulario de creación/edición de menú
        if self.db:
            # Mostrar TODOS los ingredientes, sin importar el stock
            ingredientes = [i.nombre for i in self.db.query(models.Ingrediente).all()]
            form = ctk.CTkFrame(f)
            form.pack(fill="x", padx=8, pady=4)
            ctk.CTkLabel(form, text="Nombre menú:").grid(row=0, column=0, padx=4, pady=2, sticky="w")
            self.var_menu_nombre = ctk.StringVar()
            ctk.CTkEntry(form, textvariable=self.var_menu_nombre, width=160).grid(row=0, column=1, padx=4, sticky="w")
            ctk.CTkLabel(form, text="Precio:").grid(row=0, column=2, padx=4, sticky="w")
            self.var_menu_precio = ctk.StringVar()
            ctk.CTkEntry(form, textvariable=self.var_menu_precio, width=80).grid(row=0, column=3, padx=4, sticky="w")
            ctk.CTkLabel(form, text="Descripción:").grid(row=1, column=0, padx=4, pady=2, sticky="w")
            self.var_menu_descripcion = ctk.StringVar()
            ctk.CTkEntry(form, textvariable=self.var_menu_descripcion, width=320).grid(row=1, column=1, columnspan=3, padx=4, sticky="w")
            ctk.CTkLabel(form, text="Ingrediente:").grid(row=2, column=0, padx=4, pady=2, sticky="w")
            self.ingredientes_listbox = ctk.CTkComboBox(form, values=ingredientes, width=180, state="readonly")
            self.ingredientes_listbox.grid(row=2, column=1, padx=4, sticky="w")
            ctk.CTkLabel(form, text="Cantidad:").grid(row=2, column=2, padx=4, sticky="w")
            self.var_ing_cantidad = ctk.StringVar()
            ctk.CTkEntry(form, textvariable=self.var_ing_cantidad, width=80).grid(row=2, column=3, padx=4, sticky="w")
            ctk.CTkButton(form, text="Agregar ingrediente", command=self._agregar_ingrediente_a_nuevo_menu).grid(row=2, column=4, padx=4, sticky="w")
            self.lista_ingredientes_menu = []  # [(nombre, cantidad)]
            self.ingredientes_menu_label = ctk.CTkLabel(form, text="Ingredientes del menú: []", anchor="w", justify="left")
            self.ingredientes_menu_label.grid(row=3, column=0, columnspan=5, sticky="w", padx=4, pady=2)
            ctk.CTkButton(form, text="Crear/Actualizar menú", command=self._crear_actualizar_menu).grid(row=4, column=0, columnspan=2, pady=4, sticky="w")
            ctk.CTkButton(form, text="Limpiar", command=self._limpiar_formulario_menu).grid(row=4, column=2, columnspan=2, pady=4, sticky="w")
            ctk.CTkButton(form, text="Cargar menú seleccionado", command=self._cargar_menu_seleccionado).grid(row=4, column=4, pady=4, sticky="w")

        # Canvas para mostrar PDF
        self.carta_canvas_frame = ctk.CTkFrame(f)
        self.carta_canvas_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.carta_canvas = ctk.CTkCanvas(self.carta_canvas_frame, bg="#222", highlightthickness=0)
        self.carta_canvas.pack(side="left", fill="both", expand=True)

        self.carta_scrollbar = ctk.CTkScrollbar(
            self.carta_canvas_frame,
            orientation="vertical",
            command=self.carta_canvas.yview
        )
        self.carta_scrollbar.pack(side="right", fill="y")

        self.carta_canvas.configure(yscrollcommand=self.carta_scrollbar.set)
        self._carta_img_container = [None]

    def _actualizar_menu_selector(self):
        from crud.menu_crud import listar_menus
        menus = [m.nombre for m in listar_menus(self.db)]
        if hasattr(self, 'menu_selector'):
            self.menu_selector.configure(values=menus)
        else:
            self.menu_selector = ctk.CTkComboBox(self.tabs.tab("Carta restaurant").winfo_children()[0], values=menus, variable=self.menu_selector_var, width=200, state="readonly")

    def _agregar_ingrediente_a_nuevo_menu(self):
        nombre = self.ingredientes_listbox.get()
        try:
            cantidad = float(self.var_ing_cantidad.get().replace(",", "."))
        except Exception:
            cantidad = 0
        # Validaciones: duplicados, cantidad válida
        if not nombre or cantidad <= 0:
            messagebox.showwarning("Atención", "Seleccione ingrediente y cantidad positiva.")
            return
        if any(n == nombre for n, _ in self.lista_ingredientes_menu):
            messagebox.showwarning("Atención", "Ingrediente ya agregado.")
            return
        # Validar existencia y stock suficiente
        from crud.ingrediente_crud import obtener_por_nombre
        ing = obtener_por_nombre(self.db, nombre)
        if not ing:
            messagebox.showerror("Error", "Ingrediente no existe.")
            return
        if ing.cantidad < cantidad:
            messagebox.showwarning("Atención", f"Stock insuficiente para {nombre}.")
            return
        self.lista_ingredientes_menu.append((nombre, cantidad))
        # Uso de map para mostrar ingredientes
        txt = ", ".join(map(lambda x: f"{x[0]}: {x[1]:g}", self.lista_ingredientes_menu))
        self.ingredientes_menu_label.configure(text=f"Ingredientes del menú: [{txt}]")

    def _limpiar_formulario_menu(self):
        self.var_menu_nombre.set("")
        self.var_menu_precio.set("")
        self.lista_ingredientes_menu = []
        self.ingredientes_menu_label.configure(text="Ingredientes del menú: []")

    def _crear_actualizar_menu(self):
        nombre = self.var_menu_nombre.get().strip()
        try:
            precio = int(self.var_menu_precio.get().replace(",", ""))
        except Exception:
            precio = 0
        descripcion = self.var_menu_descripcion.get().strip()
        if not nombre or precio <= 0 or not self.lista_ingredientes_menu:
            messagebox.showwarning("Atención", "Complete nombre, precio, descripción y al menos un ingrediente.")
            return
        # Crear o actualizar menú
        from crud.menu_crud import crear_menu, obtener_menu_por_nombre, agregar_ingrediente_a_menu
        from crud.ingrediente_crud import obtener_por_nombre
        menu = obtener_menu_por_nombre(self.db, nombre)
        if not menu:
            menu = crear_menu(self.db, nombre, precio)
            menu.descripcion = descripcion
        else:
            menu.precio = precio
            menu.descripcion = descripcion
            self.db.commit()
        # Limpiar ingredientes previos
        for rel in list(menu.ingredientes):
            self.db.delete(rel)
        self.db.commit()
        # Agregar ingredientes nuevos (uso de filter y reduce)
        from functools import reduce
        ingredientes_validos = list(filter(lambda x: x[1] > 0, self.lista_ingredientes_menu))
        for nombre_ing, cantidad in ingredientes_validos:
            ing = obtener_por_nombre(self.db, nombre_ing)
            if ing:
                agregar_ingrediente_a_menu(self.db, menu.id, ing.id, cantidad)
        self.db.commit()
        # Uso de reduce para contar total de ingredientes
        total_ings = reduce(lambda acc, x: acc + 1, ingredientes_validos, 0)
        self._limpiar_formulario_menu()
        self._actualizar_menu_selector()
        self._refrescar_pedido_cards()
        # Actualizar menú interno y carta PDF para reflejar cambios
        self._generar_menu_interno()
        self._generar_y_ver_carta()
        messagebox.showinfo("OK", f"Menú guardado con {total_ings} ingredientes y carta actualizada.")

    def _cargar_menu_seleccionado(self):
        if not self.db:
            return
        menu_nombre = self.menu_selector_var.get()
        if not menu_nombre:
            messagebox.showwarning("Atención", "Seleccione un menú.")
            return
        from crud.menu_crud import obtener_menu_por_nombre, ingredientes_de_menu
        menu = obtener_menu_por_nombre(self.db, menu_nombre)
        if not menu:
            messagebox.showerror("Error", "No se encontró el menú.")
            return
        self.var_menu_nombre.set(menu.nombre)
        self.var_menu_precio.set(str(menu.precio))
        ingredientes = ingredientes_de_menu(self.db, menu.id)
        self.lista_ingredientes_menu = [(n, c) for n, c, u in ingredientes]
        txt = ", ".join(map(lambda x: f"{x[0]}: {x[1]:g}", self.lista_ingredientes_menu))
        self.ingredientes_menu_label.configure(text=f"Ingredientes del menú: [{txt}]")


    def _mostrar_ingredientes_menu(self):
        if not self.db:
            messagebox.showerror("Error", "No hay conexión a la base de datos.")
            return
        menu_nombre = self.menu_selector_var.get()
        if not menu_nombre:
            messagebox.showwarning("Atención", "Seleccione un menú.")
            return
        from crud.menu_crud import obtener_menu_por_nombre, ingredientes_de_menu
        menu = obtener_menu_por_nombre(self.db, menu_nombre)
        if not menu:
            messagebox.showerror("Error", "No se encontró el menú.")
            return
        ingredientes = ingredientes_de_menu(self.db, menu.id)
        if not ingredientes:
            msg = "Este menú no tiene ingredientes asociados."
        else:
            msg = "Ingredientes para '{}':\n".format(menu_nombre)
            for nombre, cantidad, unidad in ingredientes:
                msg += f"- {nombre}: {cantidad:g} {unidad}\n"
        # Mostrar en ventana emergente
        top = ctk.CTkToplevel(self)
        top.title(f"Ingredientes de {menu_nombre}")
        top.geometry("380x320")
        top.resizable(False, False)
        ctk.CTkLabel(top, text=msg, justify="left", wraplength=350).pack(padx=16, pady=16)
        ctk.CTkButton(top, text="Cerrar", command=top.destroy).pack(pady=8)

    def _ui_listar_menus(self):
        if not self.db:
            return []
        from crud.menu_crud import listar_menus
        return [m.nombre for m in listar_menus(self.db)]

    def _ui_listar_ingredientes(self):
        if not self.db:
            return []
        from crud.ingrediente_crud import listar_ingredientes
        return [i.nombre for i in listar_ingredientes(self.db)]

    def _ui_agregar_menu(self):
        nombre = self.var_menu_nombre.get().strip()
        try:
            precio = int(self.var_menu_precio.get().replace(",", ""))
        except Exception:
            precio = 0
        menu = self._carta_agregar_menu(nombre, precio)
        if menu:
            messagebox.showinfo("OK", f"Menú '{nombre}' creado.")
            # Actualizar combos
            self.cmb_asoc_menu.configure(values=self._ui_listar_menus())

    def _ui_asociar_ingrediente_menu(self):
        menu_nombre = self.var_asoc_menu.get().strip()
        ingr_nombre = self.var_asoc_ingrediente.get().strip()
        try:
            cantidad = float(self.var_asoc_cantidad.get().replace(",", "."))
        except Exception:
            cantidad = 0
        if not menu_nombre or not ingr_nombre or cantidad <= 0:
            messagebox.showwarning("Atención", "Completa todos los campos correctamente.")
            return
        # Buscar IDs
        menu_id = None
        ingr_id = None
        if self.db:
            from crud.menu_crud import obtener_menu_por_nombre
            from crud.ingrediente_crud import obtener_por_nombre
            menu = obtener_menu_por_nombre(self.db, menu_nombre)
            ingr = obtener_por_nombre(self.db, ingr_nombre)
            if menu: menu_id = menu.id
            if ingr: ingr_id = ingr.id
        if menu_id and ingr_id:
            self._carta_agregar_ingrediente_a_menu(menu_id, ingr_id, cantidad)
            messagebox.showinfo("OK", f"Ingrediente asociado a menú.")
        else:
            messagebox.showerror("Error", "No se pudo encontrar el menú o ingrediente.")


    def _generar_y_ver_carta(self):
        # Mostrar todos los menús registrados en la base de datos
        if not self.db:
            messagebox.showwarning("Atención", "No hay conexión a la base de datos.")
            return
        from crud.menu_crud import listar_menus
        menus = [m.nombre for m in listar_menus(self.db)]
        if not menus:
            messagebox.showwarning("Atención", "No hay menús registrados.")
            return
        fd, ruta = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        generar_carta_pdf(ruta, menus, self.db)
        self._carta_temp_pdf = ruta
        self._render_pdf(ruta, self.carta_canvas, self._carta_img_container)


    # ==========================================
    # TAB: PEDIDO
    # ==========================================

    def _init_tab_pedido(self):

        f = self.tabs.tab("Pedido")

        topbar = ctk.CTkFrame(f)
        topbar.pack(fill="x", pady=(8, 0))


        ctk.CTkLabel(topbar, text="Correo del cliente:", font=ctk.CTkFont(size=12)).pack(side="left", padx=8)
        self.var_pedido_correo = ctk.StringVar()
        ctk.CTkEntry(topbar, textvariable=self.var_pedido_correo, width=200).pack(side="left", padx=4)

        # Campo de fecha para el pedido
        import datetime
        ctk.CTkLabel(topbar, text="Fecha del pedido:", font=ctk.CTkFont(size=12)).pack(side="left", padx=8)
        self.var_pedido_fecha = ctk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        ctk.CTkEntry(topbar, textvariable=self.var_pedido_fecha, width=110).pack(side="left", padx=4)

        ctk.CTkLabel(topbar, text="Seleccione menús:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=8)

        ctk.CTkButton(topbar, text="Generar Pedido", command=self._generar_boleta_interna).pack(side="right", padx=8)

        self.btn_eliminar_pedido = ctk.CTkButton(topbar, text="Eliminar Menú", command=self._pedido_quitar)
        self.btn_eliminar_pedido.pack(side="right", padx=8)

        self.lbl_total = ctk.CTkLabel(topbar, text="Total: $0.00", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_total.pack(side="right", padx=12)

        # Botones de los menús disponibles
        self.cards_frame = ctk.CTkFrame(f)
        self.cards_frame.pack(fill="x", padx=8, pady=8)

        # Tabla pedido
        self.tree_pedido = ttk.Treeview(
            f,
            columns=("menu", "cant", "punit", "importe"),
            show="headings",
            height=10
        )

        for col, w, a, t in (
            ("menu", 440, "w", "MENÚ"),
            ("cant", 120, "center", "CANT."),
            ("punit", 160, "e", "P. UNIT."),
            ("importe", 180, "e", "IMPORTE")
        ):
            self.tree_pedido.heading(col, text=t)
            self.tree_pedido.column(col, width=w, anchor=a, stretch=False)

        self._estilizar_tree(self.tree_pedido)
        self.tree_pedido.pack(fill="both", expand=True, padx=8, pady=(0, 8))


    def _importar_pedido(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo de pedido",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")]
        )
        if not ruta:
            return

        try:
            with open(ruta, newline="", encoding="utf-8-sig") as f:
                rows = list(csv.reader(f))

            if not rows:
                messagebox.showerror("Error", "Archivo vacío.")
                return

            hdr = [h.strip().lower() for h in rows[0]]

            def idx(c): return hdr.index(c) if c in hdr else None

            iM, iC = idx("menu"), idx("cantidad")
            if None in (iM, iC):
                iM, iC = 0, 1

            self.pedido.vaciar_pedido()

            for r in rows[1:]:
                if not r:
                    continue
                menu = (r[iM] if iM < len(r) else "").strip()
                try:
                    cant = int(float(r[iC].replace(",", ".")))
                except:
                    cant = 1

                from crud.menu_crud import listar_menus
                nombres_db = [m.nombre for m in listar_menus(self.db)]
                if menu and menu in nombres_db:
                    self.pedido.agregar_item(menu, cant)

            self._refrescar_pedido_tree()
            messagebox.showinfo("OK", "Pedido importado correctamente.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar el pedido:\n{e}")

        self._refrescar_pedido_tree()
        self._refrescar_pedido_cards()

        if not self.pedido.confirmacion_req():
            faltas = self.pedido.stock_faltantes()
            menu_implicado = next(iter(self.pedido.items), "Pedido")
            self._show_stock_warning(menu_implicado, faltas)


    def _refrescar_pedido_cards(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()

        # Mostrar todos los menús de la base de datos como botones para pedir
        from crud.menu_crud import listar_menus
        menus = listar_menus(self.db) if self.db else []
        for i, menu in enumerate(menus):
            img = self.menu_images.get(menu.nombre)
            ctk.CTkButton(
                self.cards_frame,
                text=menu.nombre,
                image=img,
                compound="top",
                width=150,
                height=120,
                command=lambda x=menu.nombre: self._pedido_agregar(x)
            ).grid(row=i // 5, column=i % 5, padx=6, pady=6)


    def _refrescar_pedido_tree(self):
        for i in self.tree_pedido.get_children():
            self.tree_pedido.delete(i)

        total = 0
        for k, (m, c, pu, imp) in enumerate(self.pedido.detalle()):
            self.tree_pedido.insert(
                "",
                "end",
                values=(m, c, f"${pu:,}".replace(",", "."), f"${imp:,}".replace(",", ".")),
                tags=("even" if k % 2 == 0 else "odd",)
            )
            total += imp

        total_text = f"${total:,}".replace(",", ".") + ".00"
        self.lbl_total.configure(text=f"Total: {total_text}")


    def _pedido_agregar(self, menu):
        # Validar correo antes de permitir agregar
        correo = self.var_pedido_correo.get().strip()
        if not correo:
            messagebox.showwarning("Atención", "Ingrese el correo del cliente antes de pedir.")
            return
        cliente = self.db.query(models.Cliente).filter(models.Cliente.correo == correo).first() if self.db else None
        if not cliente:
            messagebox.showwarning("Atención", "El correo no corresponde a un cliente registrado.")
            return

        # Obtener requerimientos desde la base de datos
        from crud.menu_crud import obtener_menu_por_nombre, requerimientos_menu
        hipotetico = {}
        items_tmp = dict(self.pedido.items)
        items_tmp[menu] = items_tmp.get(menu, 0) + 1

        for m, cnt in items_tmp.items():
            menu_obj = obtener_menu_por_nombre(self.db, m)
            reqs = requerimientos_menu(self.db, menu_obj.id) if menu_obj else {}
            for ing, cant in reqs.items():
                hipotetico[ing] = hipotetico.get(ing, 0.0) + cant * cnt

        faltas = self.stock.faltantes(hipotetico)

        if faltas:
            self._show_stock_warning(menu, faltas)
            return

        self.pedido.agregar_item(menu, 1)
        self._refrescar_pedido_tree()
        
        # ==========================================
    # QUITAR DEL PEDIDO
    # ==========================================

    def _pedido_quitar(self):
        sel = self.tree_pedido.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un menú para eliminar.")
            return

        menu = self.tree_pedido.item(sel[0], "values")[0]
        self.pedido.quitar_item(menu, 1)
        self._refrescar_pedido_tree()


    # ==========================================
    # GENERAR BOLETA PDF
    # ==========================================

    def _generar_boleta_interna(self):
        if not self.pedido.items:
            messagebox.showwarning("Atención", "Pedido vacío.")
            return

        if not self.pedido.confirmacion_req():
            faltas = self.pedido.stock_faltantes()
            if faltas:
                txt = ", ".join([f"{i} (req {r:g}, disp {d:g})" for i, r, d in faltas])
                print(f"[ALERTA] No se puede generar boleta → {txt}")
            messagebox.showerror("Stock insuficiente", "No alcanza el stock para este pedido.")
            return

        fd, ruta = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

        detalle = self.pedido.detalle()
        subtotal = sum(x[3] for x in detalle)
        iva = round(subtotal * 0.19)
        total = subtotal + iva

        from datetime import datetime as dt
        fecha_str = self.var_pedido_fecha.get().strip()
        try:
            fecha_boleta = dt.strptime(fecha_str, "%Y-%m-%d")
        except Exception:
            fecha_boleta = dt.today()
        boleta = Boleta(detalle, subtotal, iva, total, fecha=fecha_boleta)
        boleta.generar_pdf(ruta)

        self._boleta_temp_pdf = ruta

        messagebox.showinfo("OK", "¡Pedido generado correctamente!")

        # Guardar pedido y sus ítems en la base de datos
        if self.db:
            correo = self.var_pedido_correo.get().strip()
            fecha_str = self.var_pedido_fecha.get().strip()
            # Asegurar formato string YYYY-MM-DD
            from datetime import datetime as dt
            try:
                fecha = dt.strptime(fecha_str, "%Y-%m-%d").strftime("%Y-%m-%d")
            except Exception:
                fecha = dt.today().strftime("%Y-%m-%d")
            cliente = self.db.query(models.Cliente).filter(models.Cliente.correo == correo).first()
            if cliente:
                pedido_db = models.Pedido(cliente_id=cliente.id, fecha=fecha)
                self.db.add(pedido_db)
                self.db.commit()
                self.db.refresh(pedido_db)
                for m, c, pu, imp in detalle:
                    menu_db = self.db.query(models.Menu).filter(models.Menu.nombre == m).first()
                    if menu_db:
                        item_db = models.PedidoItem(pedido_id=pedido_db.id, menu_id=menu_db.id, cantidad=c)
                        self.db.add(item_db)
                self.db.commit()

        # Descontar stock real
        self.pedido.confirmar_y_desc()
        self._refrescar_stock()


    # ==========================================
    # TAB: VISUALIZAR BOLETA
    # ==========================================

    def _init_tab_boleta(self):
        f = self.tabs.tab("Boleta")

        bar = ctk.CTkFrame(f)
        bar.pack(fill="x", pady=8)

        ctk.CTkButton(bar, text="Generar Boleta (PDF)", command=self._mostrar_boleta_pdf).pack(
            side="left", padx=6
        )
        ctk.CTkButton(bar, text="Exportar Boleta (PDF)", command=self.exportar_boleta_pdf).pack(
            side="left", padx=6
        )

        self.boleta_canvas_frame = ctk.CTkFrame(f)
        self.boleta_canvas_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.boleta_canvas = ctk.CTkCanvas(self.boleta_canvas_frame, bg="#222", highlightthickness=0)
        self.boleta_canvas.pack(side="left", fill="both", expand=True)

        self.boleta_scrollbar = ctk.CTkScrollbar(
            self.boleta_canvas_frame, orientation="vertical", command=self.boleta_canvas.yview
        )
        self.boleta_scrollbar.pack(side="right", fill="y")

        self.boleta_canvas.configure(yscrollcommand=self.boleta_scrollbar.set)
        self._boleta_img_container = [None]


    # ==========================================
    # RENDER PDF (Carta / Boleta)
    # ==========================================

    def _render_pdf(self, ruta_pdf, canvas, img_container):
        try:
            doc = fitz.open(ruta_pdf)
            page = doc[0]

            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            ratio = (APP_W - 40) / img.width
            img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)

            photo = ImageTk.PhotoImage(img)

            canvas.config(scrollregion=(0, 0, img.width, img.height))
            canvas.delete("all")
            canvas.create_image(0, 0, anchor="nw", image=photo)

            img_container[0] = photo  # evitar garbage collection

            doc.close()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo renderizar el PDF:\n{e}")


    # ==========================================
    # MOSTRAR BOLETA
    # ==========================================

    def _mostrar_boleta_pdf(self):
        if self._boleta_temp_pdf:
            self._render_pdf(self._boleta_temp_pdf, self.boleta_canvas, self._boleta_img_container)
        else:
            messagebox.showinfo("Info", "Primero genera una boleta desde la pestaña 'Pedido'.")


    # ==========================================
    # EXPORTAR BOLETA A ARCHIVO
    # ==========================================

    def exportar_boleta_pdf(self):
        if not self._boleta_temp_pdf:
            messagebox.showinfo("Info", "Primero genera una boleta desde la pestaña Pedido.")
            return

        ruta_destino = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("Todos los archivos", "*.*")],
            title="Guardar boleta PDF"
        )

        if not ruta_destino:
            return

        try:
            with open(self._boleta_temp_pdf, "rb") as src, open(ruta_destino, "wb") as dst:
                dst.write(src.read())

            messagebox.showinfo("OK", f"Boleta exportada a:\n{ruta_destino}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar la boleta:\n{e}")


    # ==========================================
    # AVISO DE STOCK BAJO
    # ==========================================

    def _show_stock_warning(self, menu, faltas):
        try:
            dlg = ctk.CTkToplevel(self)
            dlg.title("Stock Insuficiente")
            dlg.geometry("480x160")
            dlg.resizable(False, False)
            dlg.transient(self)
            dlg.grab_set()

            frm = ctk.CTkFrame(dlg, corner_radius=8)
            frm.pack(fill="both", expand=True, padx=12, pady=12)

            icon = ctk.CTkLabel(frm, text="⚠", font=ctk.CTkFont(size=40))
            icon.grid(row=0, column=0, rowspan=2, padx=(6, 12), sticky="n")

            title = ctk.CTkLabel(frm, text="Stock Insuficiente",
                                 font=ctk.CTkFont(size=14, weight="bold"))
            title.grid(row=0, column=1, sticky="w")

            msg = f"No hay ingredientes suficientes para '{menu}'."
            if faltas:
                detalles = "\n".join([f"{i}: req {r:g} / disp {d:g}" for i, r, d in faltas])
                msg = msg + "\n" + detalles

            body = ctk.CTkLabel(frm, text=msg, wraplength=360, justify="left")
            body.grid(row=1, column=1, sticky="w")

            ctk.CTkButton(frm, text="OK", width=90, command=dlg.destroy).grid(
                row=2, column=1, sticky="e", pady=(12, 0)
            )

        except:
            messagebox.showwarning("Stock insuficiente",
                                   f"No hay stock para '{menu}'.")


    # ==========================================
    # TAB: GRÁFICOS
    # ==========================================

    def _init_tab_graficos(self):
        f = self.tabs.tab("Gráficos")
        frame = ctk.CTkFrame(f)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkLabel(frame, text="Selecciona tipo de gráfico:").pack(pady=8)
        self.var_grafico_tipo = ctk.StringVar(value="Ventas por fecha (diarias)")
        opciones = [
            "Ventas por fecha (diarias)",
            "Ventas por fecha (mensuales)",
            "Menús más comprados",
            "Uso de ingredientes en pedidos"
        ]
        self.cmb_grafico = ctk.CTkComboBox(frame, values=opciones, variable=self.var_grafico_tipo, state="readonly", width=260)
        self.cmb_grafico.pack(pady=4)
        ctk.CTkButton(frame, text="Mostrar Gráfico", command=self._mostrar_grafico_seleccionado).pack(pady=16)

    def _mostrar_grafico_seleccionado(self):
        if not self.db:
            messagebox.showerror("Error", "No hay conexión a la base de datos.")
            return
        tipo = self.var_grafico_tipo.get()
        try:
            if tipo == "Ventas por fecha (diarias)":
                graficos.graficar_ingresos_por_dia(self.db)
            elif tipo == "Ventas por fecha (mensuales)":
                graficos.graficar_ingresos_por_mes(self.db)
            elif tipo == "Menús más comprados":
                graficos.graficar_menus_mas_vendidos(self.db)
            elif tipo == "Uso de ingredientes en pedidos":
                graficos.graficar_uso_ingredientes(self.db)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo graficar: {e}")

    def _init_tab_clientes(self):
        f = self.tabs.tab("Clientes")
        frame = ctk.CTkFrame(f)
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        # Tabla de clientes
        self.tree_clientes = ttk.Treeview(frame, columns=("id", "nombre", "correo"), show="headings", height=12)
        for col, w in (("id", 60), ("nombre", 200), ("correo", 260)):
            self.tree_clientes.heading(col, text=col.upper())
            self.tree_clientes.column(col, width=w, anchor="w", stretch=False)
        self.tree_clientes.pack(fill="x", padx=8, pady=8)

        # Formulario
        form = ctk.CTkFrame(frame)
        form.pack(pady=8)
        ctk.CTkLabel(form, text="Nombre").grid(row=0, column=0, padx=4, pady=4)
        ctk.CTkLabel(form, text="Correo").grid(row=1, column=0, padx=4, pady=4)
        self.var_cliente_nombre = ctk.StringVar()
        self.var_cliente_correo = ctk.StringVar()
        ctk.CTkEntry(form, textvariable=self.var_cliente_nombre, width=180).grid(row=0, column=1, padx=4)
        ctk.CTkEntry(form, textvariable=self.var_cliente_correo, width=180).grid(row=1, column=1, padx=4)
        ctk.CTkButton(form, text="Agregar", command=self._cliente_agregar).grid(row=0, column=2, padx=8)
        ctk.CTkButton(form, text="Actualizar", command=self._cliente_actualizar).grid(row=1, column=2, padx=8)
        ctk.CTkButton(form, text="Eliminar", command=self._cliente_eliminar).grid(row=2, column=2, padx=8)

        self._refrescar_clientes()
        self.tree_clientes.bind("<ButtonRelease-1>", self._cliente_seleccionar)

    def _refrescar_clientes(self):
        self.tree_clientes.delete(*self.tree_clientes.get_children())
        if not self.db:
            return
        clientes = self.db.query(models.Cliente).all()
        # Uso de map para transformar
        filas = list(map(lambda c: (c.id, c.nombre, c.correo), clientes))
        for fila in filas:
            self.tree_clientes.insert("", "end", values=fila)

    def _cliente_seleccionar(self, event):
        sel = self.tree_clientes.selection()
        if sel:
            vals = self.tree_clientes.item(sel[0], "values")
            self.var_cliente_nombre.set(vals[1])
            self.var_cliente_correo.set(vals[2])
            self._cliente_id_sel = vals[0]
        else:
            self._cliente_id_sel = None

    def _cliente_agregar(self):
        nombre = self.var_cliente_nombre.get().strip()
        correo = self.var_cliente_correo.get().strip()
        if not nombre or not correo:
            messagebox.showwarning("Atención", "Nombre y correo no pueden estar vacíos.")
            return
        if not self._validar_correo(correo):
            messagebox.showwarning("Atención", "Correo no válido.")
            return
        # Unicidad
        if self.db.query(models.Cliente).filter(models.Cliente.correo == correo).first():
            messagebox.showwarning("Atención", "Correo ya registrado.")
            return
        nuevo = models.Cliente(nombre=nombre, correo=correo)
        self.db.add(nuevo)
        self.db.commit()
        self._refrescar_clientes()

    def _cliente_actualizar(self):
        if not hasattr(self, '_cliente_id_sel') or not self._cliente_id_sel:
            messagebox.showwarning("Atención", "Seleccione un cliente.")
            return
        nombre = self.var_cliente_nombre.get().strip()
        correo = self.var_cliente_correo.get().strip()
        if not nombre or not correo:
            messagebox.showwarning("Atención", "Nombre y correo no pueden estar vacíos.")
            return
        if not self._validar_correo(correo):
            messagebox.showwarning("Atención", "Correo no válido.")
            return
        cliente = self.db.query(models.Cliente).get(self._cliente_id_sel)
        if not cliente:
            messagebox.showerror("Error", "Cliente no encontrado.")
            return
        # Unicidad
        otro = self.db.query(models.Cliente).filter(models.Cliente.correo == correo, models.Cliente.id != cliente.id).first()
        if otro:
            messagebox.showwarning("Atención", "Correo ya registrado por otro cliente.")
            return
        cliente.nombre = nombre
        cliente.correo = correo
        self.db.commit()
        self._refrescar_clientes()

    def _cliente_eliminar(self):
        if not hasattr(self, '_cliente_id_sel') or not self._cliente_id_sel:
            messagebox.showwarning("Atención", "Seleccione un cliente.")
            return
        cliente = self.db.query(models.Cliente).get(self._cliente_id_sel)
        if not cliente:
            messagebox.showerror("Error", "Cliente no encontrado.")
            return
        # Impedir eliminar si tiene pedidos asociados
        if self.db.query(models.Pedido).filter(models.Pedido.cliente_id == cliente.id).first():
            messagebox.showwarning("Atención", "No se puede eliminar: el cliente tiene pedidos asociados.")
            return
        self.db.delete(cliente)
        self.db.commit()
        self._refrescar_clientes()

    def _validar_correo(self, correo):
        return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", correo)