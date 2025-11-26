
# Utilidad para poblar la base de datos con menús iniciales (solo para inicialización)
def poblar_db_con_menus_estaticos(db):
    """
    Pobla la base de datos con los menús, precios e ingredientes definidos aquí.
    Solo agrega si no existen. No usar para lógica de negocio.
    """
    from models import Menu as MenuDB, Ingrediente, MenuIngrediente
    menus = {
        "Hamburguesa": {"precio": 3500, "req": {"pan de hamburguesa": 1, "carne": 1, "lamina de queso": 1}},
        "Completo": {"precio": 2500, "req": {"pan de completo": 1, "vienesa": 1, "tomate": 0.5}},
        "Papas Fritas": {"precio": 2000, "req": {"papas": 1.5}},
        "Pollo Frito": {"precio": 4500, "req": {"presa de pollo": 2}},
        "Panqueques": {"precio": 3000, "req": {"panqueques": 1, "huevos": 1, "porcion de harina": 0.1}},
        "Ensalada Mixta": {"precio": 2200, "req": {"lechuga": 1.2, "zanahoria rallada": 2.15, "tomate": 3.15}},
        "Coca Cola": {"precio": 1500, "req": {"coca cola": 1}},
        "Pepsi": {"precio": 1500, "req": {"pepsi": 1}},
    }
    # Poblar ingredientes únicos
    ingredientes_set = set()
    for reqs in menus.values():
        ingredientes_set.update(reqs["req"].keys())
    ingredientes_objs = {}
    for ing in ingredientes_set:
        obj = db.query(Ingrediente).filter_by(nombre=ing).first()
        if not obj:
            obj = Ingrediente(nombre=ing, unidad="unid", cantidad=100)
            db.add(obj)
            db.commit()
            db.refresh(obj)
        ingredientes_objs[ing] = obj
    # Poblar menús y asociar ingredientes
    for nombre, datos in menus.items():
        menu = db.query(MenuDB).filter_by(nombre=nombre).first()
        descripcion = "Menú especial de la casa."
        if not menu:
            menu = MenuDB(nombre=nombre, precio=datos["precio"], descripcion=descripcion)
            db.add(menu)
            db.commit()
            db.refresh(menu)
        else:
            # Actualizar precio y descripción si han cambiado
            if menu.precio != datos["precio"] or menu.descripcion != descripcion:
                menu.precio = datos["precio"]
                menu.descripcion = descripcion
                db.commit()
        # Asociar ingredientes
        for ing, cant in datos["req"].items():
            ing_obj = ingredientes_objs[ing]
            rel = db.query(MenuIngrediente).filter_by(menu_id=menu.id, ingrediente_id=ing_obj.id).first()
            if not rel:
                rel = MenuIngrediente(menu_id=menu.id, ingrediente_id=ing_obj.id, cantidad=cant)
                db.add(rel)
        db.commit()