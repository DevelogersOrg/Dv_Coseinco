# 06/09/2022 
* Se agrega configuracion para poder visualizar los montos totales de exonerados y demas tanto en el formulario como en la impresion (se tiene que modificar el grupo de tipo de impuesto activando el check "Mostrar base" de los registros que se requieran)

# 07/09/2022
* Se deja el campo pe_affectation_code solo visible en facturas de ventas, para el tipo de afectacion de igv para compras se menaje con el modulo solse_pe_purchase

# 09/09/2022
* Se mejora visualiacion de tipo de impuesto para que solo se muestre en ventas ya que en compras se tiene que manejar distinto

# 13/09/2022
* Se establece un codigo de producto para el xml en caso el producto no cuente con uno y asi evitar enviar "-" que actualmente "devuelve aceptado con observaciones"

# 02/10/2022
* Se arregla bug con el codigo de producto que se envia en el xml
* Se arregla bug que se tenia en algunos casos con el redondeo de la detracciones que se envia en el xml

# 05/10/2022
* Se agrega campo "mostrar_base" a nivel de impuesto (se usa para el punto de venta)

# 23/11/2022
* Se modifica validacion de envio de redondeo para pago en partes cuando es detraccion

# 30/11/2022
* Se soluciona bug en notas de credito que tenian como origen facturas con descuento.


# 06/12/2022
* Se soluciona bug al emitir notas de credito con items con cantidades mayores a 1.

# 23/01/2023
* Se agrega nota de credito por tipo de cambio en fecha de cuotas.

# 28/01/2023
* Se permite mostrar el monto en letras en idioma ingles, opcion creada en solse_pe_edi
* Se crea campo para modulo de pos offline