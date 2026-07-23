from decimal import Decimal
from pathlib import Path

from app.application.configuracion_uc.determinar_procedimiento_contratacion import (
    DeterminarProcedimientoContratacion,
)
from app.domain.configuracion_uc import ConfiguracionUCId
from app.modules.documentos.extractor_datos import extraer_datos_op_desde_pdf
from app.modules.inteligencia.comparador import comparar_total_facturas
from app.modules.inteligencia.confiabilidad import calcular_confiabilidad, calcular_prioridad
from app.modules.inteligencia.reglas import diagnosticar_expediente
from app.repositories.configuracion_uc_repository import (
    ConfiguracionUCRepository,
)
from app.schemas.analisis_op import AnalisisOPRead, DocumentoComercialExtraido, RetencionExtraida
from app.services.documentos import documento_service
from app.composition.expediente import expediente_service


class ConfiguracionUCHistoricaNoEncontradaError(LookupError):
    def __init__(self, configuracion_uc_id: ConfiguracionUCId) -> None:
        self.configuracion_uc_id = configuracion_uc_id
        super().__init__(
            "No existe la Configuración UC histórica asociada "
            f"al expediente: {configuracion_uc_id}."
        )


class AnalisisOPService:
    def __init__(
        self,
        determinar_procedimiento_contratacion: DeterminarProcedimientoContratacion,
        configuracion_uc_repository: ConfiguracionUCRepository,
    ) -> None:
        self._determinar_procedimiento_contratacion = (
            determinar_procedimiento_contratacion
        )
        self._configuracion_uc_repository = configuracion_uc_repository

    def analizar(self, expediente_id: str) -> AnalisisOPRead:
        expediente = expediente_service.obtener(expediente_id)
        fecha_referencia = expediente.creado.date()
        documentos = documento_service.listar_por_expediente(expediente_id)
        op = next((doc for doc in documentos if doc.tipo == "OP"), None)

        if op is None:
            return AnalisisOPRead(
                expediente_id=expediente_id,
                modo="ALFA_PDF_TEXTO",
                op_detectada=False,
                proveedor=None,
                cuit=None,
                fondo=None,
                orden_pago=None,
                liquidacion=None,
                fecha_op=None,
                importe_bruto=None,
                importe_neto=None,
                valor_uc=None,
                norma_uc=None,
                cantidad_uc=None,
                procedimiento=None,
                articulo=None,
                inciso=None,
                encuadre_legal=None,
                documentos_comerciales=[],
                retenciones=[],
                validaciones=[],
                advertencias=["No existe Orden de Pago cargada en el expediente."],
                faltantes=["Orden de Pago"],
            )

        ruta = Path(__file__).resolve().parents[3] / op.ruta
        datos = extraer_datos_op_desde_pdf(ruta)

        if datos.texto_extraido:
            importe_bruto = datos.monto_total_facturas or datos.importe_pago or datos.importe_probable
            importe_neto = datos.monto_neto_pagar or datos.importe_pago
            determinacion = None
            if importe_bruto is not None:
                monto = Decimal(str(importe_bruto))
                if expediente.configuracion_uc_id is not None:
                    configuracion = (
                        self._configuracion_uc_repository.obtener_por_id(
                            expediente.configuracion_uc_id
                        )
                    )
                    if configuracion is None:
                        raise ConfiguracionUCHistoricaNoEncontradaError(
                            expediente.configuracion_uc_id
                        )
                    determinacion = (
                        self._determinar_procedimiento_contratacion
                        .ejecutar_con_configuracion(
                            configuracion=configuracion,
                            monto=monto,
                        )
                    )
                else:
                    determinacion = (
                        self._determinar_procedimiento_contratacion.ejecutar(
                            fecha=fecha_referencia,
                            monto=monto,
                        )
                    )

            documentos_comerciales = [
                DocumentoComercialExtraido(
                    tipo=factura.tipo,
                    letra=factura.letra,
                    numero=factura.numero,
                    fecha=factura.fecha,
                    importe=factura.importe,
                )
                for factura in datos.facturas
            ]

            retenciones = [
                RetencionExtraida(concepto=ret.concepto, importe=ret.importe)
                for ret in datos.retenciones
            ]

            validaciones = [
                "OP cargada y asociada al expediente.",
                f"Texto extraído del PDF ({datos.paginas} página/s).",
            ]

            faltantes = [
                "Factura",
                "Remito o conformidad firmada",
                "Validación CAE",
                "Certificado Fiscal ARBA",
                "Constancia ARCA",
            ]

            if datos.cuit:
                validaciones.append("CUIT detectado en la OP.")
            else:
                faltantes.append("CUIT no detectado")

            if datos.proveedor:
                validaciones.append("Proveedor detectado.")
            else:
                faltantes.append("Proveedor no detectado")

            if datos.monto_total_facturas:
                validaciones.append("Monto total de facturas detectado.")
            elif datos.importe_pago:
                validaciones.append("Importe de pago detectado.")
            else:
                faltantes.append("Importe no detectado")

            if datos.monto_neto_pagar:
                validaciones.append("Monto neto a pagar detectado.")

            if datos.facturas:
                suma_facturas = round(sum(f.importe for f in datos.facturas), 2)
                validaciones.append(f"{len(datos.facturas)} factura(s) liquidadas detectadas.")

                if datos.monto_total_facturas is not None:
                    diferencia = round(abs(suma_facturas - datos.monto_total_facturas), 2)
                    if diferencia <= 1:
                        validaciones.append("La suma de facturas coincide con el monto total.")
                    else:
                        faltantes.append(f"Revisar diferencia entre facturas y monto total: ${diferencia:,.2f}")

            if datos.retenciones:
                validaciones.append(f"{len(datos.retenciones)} retención(es) detectada(s).")

            if determinacion is not None:
                validaciones.append("UC calculadas desde el monto total detectado.")

            comparacion = comparar_total_facturas(
                total_op=datos.monto_total_facturas,
                facturas=datos.facturas,
            )
            economia_consistente = comparacion.estado == "CONSISTENTE"

            if comparacion.estado == "CONSISTENTE":
                validaciones.append("Comparador documental: OP y facturas consistentes.")
            elif comparacion.estado == "INCONSISTENTE":
                validaciones.append(f"Comparador documental: diferencia detectada ${comparacion.diferencia:,.2f}.")
                faltantes.append("Revisión contable por diferencia entre OP y facturas")
            else:
                validaciones.append(f"Comparador documental: {comparacion.mensaje}")

            confiabilidad = calcular_confiabilidad(
                op_detectada=True,
                proveedor=datos.proveedor,
                cuit=datos.cuit,
                importe_bruto=importe_bruto,
                importe_neto=importe_neto,
                facturas_detectadas=len(datos.facturas),
                economia_consistente=economia_consistente,
                retenciones_detectadas=len(datos.retenciones),
                faltantes=faltantes,
            )
            prioridad = calcular_prioridad(
                confiabilidad=confiabilidad,
                economia_consistente=economia_consistente,
                faltantes=faltantes,
            )

            validaciones.append(f"Confiabilidad documental: {confiabilidad}%.")
            validaciones.append(f"Prioridad de revisión: {prioridad}.")

            diagnostico = diagnosticar_expediente(
                proveedor=datos.proveedor,
                cuit=datos.cuit,
                importe_bruto=importe_bruto,
                importe_neto=importe_neto,
                facturas_detectadas=len(datos.facturas),
                retenciones_detectadas=len(datos.retenciones),
                faltantes=faltantes,
                economia_consistente=economia_consistente,
            )

            validaciones.append(f"Riesgo administrativo: {diagnostico.riesgo}.")
            validaciones.append(f"Acción sugerida: {diagnostico.accion_sugerida}.")
            validaciones.append(f"Recomendación IA: {diagnostico.recomendacion}")

            advertencias = list(datos.advertencias)
            advertencias.append("Extracción automática inicial. Requiere revisión humana.")

            if (
                expediente.configuracion_uc_id is None
                and determinacion is not None
            ):
                expediente_service.asociar_configuracion_uc(
                    expediente_id,
                    determinacion.configuracion.id_configuracion,
                )

            return AnalisisOPRead(
                expediente_id=expediente_id,
                modo="ALFA_PDF_TEXTO",
                op_detectada=True,
                proveedor=datos.proveedor,
                cuit=datos.cuit,
                fondo=datos.fondo or "Fondo Compensador",
                orden_pago=datos.orden_pago,
                liquidacion=datos.liquidacion,
                fecha_op=datos.fecha,
                importe_bruto=importe_bruto,
                importe_neto=importe_neto,
                valor_uc=(
                    determinacion.valor_uc
                    if determinacion is not None
                    else None
                ),
                norma_uc=(
                    determinacion.rango.referencia_normativa
                    if determinacion is not None
                    else None
                ),
                cantidad_uc=(
                    determinacion.cantidad_uc
                    if determinacion is not None
                    else None
                ),
                procedimiento=(
                    determinacion.rango.procedimiento
                    if determinacion is not None
                    else None
                ),
                articulo=(
                    determinacion.rango.articulo
                    if determinacion is not None
                    else None
                ),
                inciso=(
                    determinacion.rango.inciso
                    if determinacion is not None
                    else None
                ),
                encuadre_legal=(
                    f"{determinacion.rango.articulo} "
                    f"{determinacion.rango.inciso}. "
                    f"{determinacion.rango.referencia_normativa}"
                    if determinacion is not None
                    else None
                ),
                documentos_comerciales=documentos_comerciales,
                retenciones=retenciones,
                validaciones=validaciones,
                advertencias=advertencias,
                faltantes=faltantes,
            )

        return AnalisisOPRead(
            expediente_id=expediente_id,
            modo="EXTRACCION_FALLIDA",
            op_detectada=True,
            proveedor=None,
            cuit=None,
            fondo=None,
            orden_pago=None,
            liquidacion=None,
            fecha_op=None,
            importe_bruto=None,
            importe_neto=None,
            valor_uc=None,
            norma_uc=None,
            cantidad_uc=None,
            procedimiento=None,
            articulo=None,
            inciso=None,
            encuadre_legal=None,
            documentos_comerciales=[],
            retenciones=[],
            validaciones=["OP cargada y asociada al expediente."],
            advertencias=[
                "No fue posible leer correctamente el contenido de la Orden de Pago."
            ],
            faltantes=["Lectura válida de la Orden de Pago"],
        )
