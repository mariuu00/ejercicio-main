from typing import Annotated
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from dependencias import ConnectionDep
from esquemas import ProductoActualizar
from repositorio import actualizar_producto, obtener_producto, obtener_productos

router = APIRouter(tags=["productos"])

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


@router.get("/")
async def listar_productos(request: Request, conn: ConnectionDep):
    # Ya implementado: muestra la página con la lista de productos.
    productos = await obtener_productos(conn)
    return templates.TemplateResponse(
        request=request,
        name="productos.html",
        context={"productos": productos},
    )


@router.get("/productos/{producto_id}/editar")
async def editar_producto_vista(request: Request, conn: ConnectionDep, producto_id: int):
    producto = await obtener_producto(conn, producto_id)
    if producto is None:
        return templates.TemplateResponse(
            request=request,
            name="componentes/producto_no_encontrado.html",
            context={"producto_id": producto_id},
        )
    return templates.TemplateResponse(
        request=request,
        name="componentes/fila_editar.html",
        context={
            "producto": producto,
            "nombre": producto["nombre"],
            "precio": producto["precio"],
            "cantidad": producto["cantidad"],
            "descripcion": producto["descripcion"] or "",
            "errores": {},
        },
    )


@router.get("/productos/{producto_id}/cancelar")
async def cancelar_edicion_vista(request: Request, conn: ConnectionDep, producto_id: int):
    # Cancelar solo vuelve a mostrar la fila original, sin modificar nada.
    producto = await obtener_producto(conn, producto_id)
    if producto is None:
        return templates.TemplateResponse(
            request=request,
            name="componentes/producto_no_encontrado.html",
            context={"producto_id": producto_id},
        )
    return templates.TemplateResponse(
        request=request,
        name="componentes/fila_producto.html",
        context={"producto": producto},
    )


@router.post("/productos/{producto_id}")
async def guardar_producto_vista(
    request: Request,
    conn: ConnectionDep,
    producto_id: int,
    nombre: Annotated[str | None, Form()] = None,
    precio: Annotated[str | None, Form()] = None,
    cantidad: Annotated[str | None, Form()] = None,
    descripcion: Annotated[str | None, Form()] = None,
):
    producto = await obtener_producto(conn, producto_id)
    if producto is None:
        return templates.TemplateResponse(
            request=request,
            name="componentes/producto_no_encontrado.html",
            context={"producto_id": producto_id},
        )

    errores = {}
    try:
        precio_numero = float(precio) if precio is not None and precio.strip() else None
    except ValueError:
        precio_numero = None
        errores["precio"] = "El precio debe ser un número mayor que cero."

    try:
        cantidad_numero = int(cantidad) if cantidad is not None and cantidad.strip() else None
    except ValueError:
        cantidad_numero = None
        errores["cantidad"] = "La cantidad debe ser un número entero mayor o igual que cero."

    try:
        datos = ProductoActualizar(
            nombre=nombre or "",
            precio=precio_numero,
            cantidad=cantidad_numero,
            descripcion=descripcion,
        )
    except ValidationError as error:
        for detalle in error.errors():
            campo = detalle["loc"][0]
            if campo == "nombre":
                errores[campo] = "El nombre es obligatorio y debe tener entre 1 y 100 caracteres."
            elif campo == "precio":
                errores[campo] = "El precio debe ser un número mayor que cero."
            elif campo == "cantidad":
                errores[campo] = "La cantidad debe ser un número entero mayor o igual que cero."

    if errores:
        return templates.TemplateResponse(
            request=request,
            name="componentes/fila_editar.html",
            context={
                "producto": producto,
                "nombre": nombre or "",
                "precio": precio or "",
                "cantidad": cantidad or "",
                "descripcion": descripcion or "",
                "errores": errores,
            },
            status_code=422,
        )

    actualizado = await actualizar_producto(
        conn,
        producto_id,
        datos.nombre,
        datos.precio,
        datos.cantidad,
        datos.descripcion,
    )
    if not actualizado:
        return templates.TemplateResponse(
            request=request,
            name="componentes/producto_no_encontrado.html",
            context={"producto_id": producto_id},
        )

    producto_actualizado = await obtener_producto(conn, producto_id)
    return templates.TemplateResponse(
        request=request,
        name="componentes/fila_actualizada.html",
        context={"producto": producto_actualizado},
    )