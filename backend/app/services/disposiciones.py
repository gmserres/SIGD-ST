
from datetime import datetime
from pathlib import Path
import re

from app.modules.documentos.extractor_datos import extraer_datos_op_desde_pdf
from app.schemas.disposicion import DisposicionRead, DisposicionUpdate
from app.composition.analisis_op import analisis_op_service
from app.composition.habilitacion_proveedor_op import (
    evaluar_habilitacion_proveedor_op_service,
)
from app.composition.documento import documento_service
from app.composition.expediente import expediente_service
from app.composition.seleccion_proveedor import (
    seleccion_proveedor_repository,
)
from app.domain.habilitacion_proveedor_op import (
    EstadoHabilitacionProveedorOP,
)
from app.domain.finalizacion_expediente import (
    ESTADOS_TERMINALES_ORDINARIOS,
    ExpedienteTerminalError,
)
from app.services.analisis_op import (
    DocumentoNoEsOPError,
    DocumentoOPExpedienteInconsistenteError,
    DocumentoOPNoEncontradoError,
)
from app.services.control_proveedor_op_service import (
    AnalisisOPDocumentoInconsistenteError,
)
from app.services.historial import historial_service
from app.services.parametros import parametros_institucionales_service
from app.services.template_engine import (
    dividir_disposicion,
    formatear_moneda,
    formatear_numero,
    numero_a_letras,
    template_engine,
)


class BorradorDisposicionNoHabilitadoError(ValueError):
    def __init__(self, habilitacion) -> None:
        self.estado = habilitacion.estado
        self.mensaje = habilitacion.mensaje
        self.proxima_accion = habilitacion.proxima_accion
        self.documento_op_id = habilitacion.documento_op_id
        super().__init__(self.mensaje)


class BorradorDisposicionObsoletoError(ValueError):
    def __init__(self, documento_op_id: str) -> None:
        self.documento_op_id = documento_op_id
        self.mensaje = "El borrador fue generado con una habilitación anterior."
        super().__init__(self.mensaje)


class DisposicionOPNoEncontradaError(LookupError):
    pass


class DisposicionOPAmbiguaError(ValueError):
    pass


class DisposicionService:
    def __init__(self) -> None:
        self._borradores: dict[tuple[str, str], DisposicionRead] = {}
        self._plantilla_fc = Path(__file__).resolve().parents[3] / "storage" / "templates" / "disposicion_fc_v2026.md"
        self._plantilla_version = "Disposición FC 2026.2"

    def generar_borrador(
        self,
        expediente_id: str,
        documento_op_id: str,
        *,
        regenerar: bool = False,
    ) -> DisposicionRead:
        self._asegurar_mutable(expediente_id)
        habilitacion = self._evaluar_habilitacion(
            expediente_id, documento_op_id
        )
        clave = (expediente_id, documento_op_id)
        if clave in self._borradores and not regenerar:
            return self._con_estado_actual(
                self._borradores[clave], habilitacion
            )

        analisis = analisis_op_service.reconstruir_documento(
            expediente_id, documento_op_id
        )
        if analisis.documento_op_id != documento_op_id:
            raise AnalisisOPDocumentoInconsistenteError(
                documento_op_id, analisis.documento_op_id
            )
        if not analisis.op_detectada or analisis.modo == "EXTRACCION_FALLIDA":
            raise ValueError(
                "La Orden de Pago fue incorporada al expediente, pero no fue "
                "posible extraer la información necesaria para generar la "
                "disposición."
            )

        expediente = expediente_service.obtener(expediente_id)
        historial = historial_service.listar_por_expediente(expediente_id)
        validado_observado = any(h.accion == "EXPEDIENTE_VALIDADO_CON_OBSERVACIONES" for h in historial)
        checklist_fisico = any(h.accion == "CHECKLIST_FISICO_REGISTRADO" for h in historial)
        datos_op = self._datos_op_documento(
            expediente_id, documento_op_id
        )
        proveedor_presentacion = (
            habilitacion.proveedor_definitivo_razon_social
        )
        if proveedor_presentacion is None:
            seleccion = self._obtener_seleccion_habilitante(
                habilitacion.seleccion_proveedor_id,
                expediente_id,
            )
            proveedor_presentacion = seleccion.proveedor_razon_social

        plantilla = template_engine.cargar(self._plantilla_fc)
        variables = self._construir_variables(
            expediente,
            analisis,
            datos_op,
            proveedor=proveedor_presentacion,
            cuit=habilitacion.proveedor_definitivo_cuit,
        )
        render = template_engine.renderizar(plantilla, variables)
        visto, considerando, dispone = dividir_disposicion(render.contenido)

        numero = None
        observaciones = [
            "Borrador generado con motor de plantillas institucionales.",
            f"Plantilla: {self._plantilla_version}.",
            f"Variables reemplazadas: {len(render.variables_usadas) - len(render.variables_faltantes)} de {len(render.variables_usadas)}.",
        ]
        if render.variables_faltantes:
            observaciones.append("Variables pendientes: " + ", ".join(render.variables_faltantes))
        if checklist_fisico:
            observaciones.append("La documentación física fue acreditada mediante checklist de validación.")
        if validado_observado:
            observaciones.append("El expediente fue validado con observaciones. Revisar el historial antes de emitir.")

        ahora = datetime.now()
        borrador = DisposicionRead(
            expediente_id=expediente_id,
            documento_op_id=documento_op_id,
            control_proveedor_op_id=habilitacion.control_proveedor_op_id,
            seleccion_proveedor_id=habilitacion.seleccion_proveedor_id,
            proveedor_definitivo_id=habilitacion.proveedor_definitivo_id,
            proveedor_definitivo_cuit=(
                habilitacion.proveedor_definitivo_cuit
            ),
            proveedor_definitivo_razon_social=(
                habilitacion.proveedor_definitivo_razon_social
            ),
            estado_habilitacion_actual=habilitacion.estado,
            obsoleto=False,
            numero_disposicion=numero,
            estado="BORRADOR_PLANTILLA",
            visto=visto,
            considerando=considerando,
            dispone=dispone,
            observaciones_ia=observaciones,
            creado=ahora,
            actualizado=ahora,
        )
        self._borradores[clave] = borrador
        historial_service.registrar(
            expediente_id,
            "PLANTILLA_APLICADA",
            detalle=(
                f"Documento OP: {documento_op_id} | "
                f"{self._plantilla_version} | variables: "
                f"{len(render.variables_usadas) - len(render.variables_faltantes)}"
                f"/{len(render.variables_usadas)}"
            ),
        )
        historial_service.registrar(
            expediente_id,
            "BORRADOR_DISPOSICION_GENERADO",
            detalle=(
                f"Documento OP: {documento_op_id} | "
                f"Borrador de Disposición Nº {numero}"
            ),
        )
        return borrador

    def actualizar_borrador(
        self,
        expediente_id: str,
        documento_op_id: str,
        data: DisposicionUpdate,
    ) -> DisposicionRead:
        self._asegurar_mutable(expediente_id)
        borrador = self.obtener_exportable(expediente_id, documento_op_id)
        actualizado = borrador.model_copy(
            update={
                **data.model_dump(exclude_unset=True),
                "actualizado": datetime.now(),
            }
        )
        self._borradores[(expediente_id, documento_op_id)] = actualizado
        historial_service.registrar(
            expediente_id,
            "BORRADOR_DISPOSICION_ACTUALIZADO",
            detalle=f"Documento OP: {documento_op_id}",
        )
        return actualizado

    def obtener_borrador(
        self, expediente_id: str, documento_op_id: str
    ) -> DisposicionRead:
        clave = (expediente_id, documento_op_id)
        if clave not in self._borradores:
            self._asegurar_mutable(expediente_id)
            return self.generar_borrador(expediente_id, documento_op_id)
        habilitacion = evaluar_habilitacion_proveedor_op_service.evaluar(
            expediente_id, documento_op_id
        )
        return self._con_estado_actual(self._borradores[clave], habilitacion)

    def obtener_exportable(
        self, expediente_id: str, documento_op_id: str
    ) -> DisposicionRead:
        borrador = self.obtener_borrador(expediente_id, documento_op_id)
        if borrador.obsoleto:
            raise BorradorDisposicionObsoletoError(documento_op_id)
        return borrador

    def generar_borrador_legacy(
        self, expediente_id: str, *, regenerar: bool = False
    ) -> DisposicionRead:
        return self.generar_borrador(
            expediente_id,
            self.resolver_documento_op_legacy(expediente_id),
            regenerar=regenerar,
        )

    def actualizar_borrador_legacy(
        self, expediente_id: str, data: DisposicionUpdate
    ) -> DisposicionRead:
        return self.actualizar_borrador(
            expediente_id,
            self.resolver_documento_op_legacy(expediente_id),
            data,
        )

    def obtener(self, expediente_id: str) -> DisposicionRead:
        documento_op_id = self.resolver_documento_op_legacy(expediente_id)
        return self.obtener_borrador(expediente_id, documento_op_id)

    def resolver_documento_op_legacy(self, expediente_id: str) -> str:
        documentos_op = [
            documento
            for documento in documento_service.listar_por_expediente(
                expediente_id
            )
            if documento.tipo.upper() == "OP"
        ]
        if not documentos_op:
            raise DisposicionOPNoEncontradaError(expediente_id)
        if len(documentos_op) > 1:
            raise DisposicionOPAmbiguaError(expediente_id)
        return documentos_op[0].id

    def _datos_op_documento(
        self, expediente_id: str, documento_op_id: str
    ):
        documento = documento_service.obtener_por_id(documento_op_id)
        if documento is None:
            raise DocumentoOPNoEncontradoError(documento_op_id)
        if documento.expediente_id != expediente_id:
            raise DocumentoOPExpedienteInconsistenteError(
                documento_op_id, expediente_id
            )
        if documento.tipo.upper() != "OP":
            raise DocumentoNoEsOPError(documento_op_id)
        ruta = Path(__file__).resolve().parents[3] / documento.ruta
        if not ruta.exists():
            return None
        return extraer_datos_op_desde_pdf(ruta)

    def _construir_variables(
        self,
        expediente,
        analisis,
        datos_op,
        *,
        proveedor: str | None = None,
        cuit: str | None = None,
    ) -> dict[str, str]:
        parametros = parametros_institucionales_service.obtener()
        importe_bruto = analisis.importe_bruto
        fecha = self._fecha_larga(analisis.fecha_op)
        ejercicio = str(parametros.ejercicio)
        facturas = datos_op.facturas if datos_op else analisis.documentos_comerciales
        retenciones = datos_op.retenciones if datos_op else analisis.retenciones
        texto_op = datos_op.texto_extraido if datos_op else ""
        forma_pago = self._extraer_por_etiqueta(texto_op, "Forma de Pago") or "Transferencia"
        cbu = self._extraer_por_etiqueta(texto_op, "Número de cbu") or self._extraer_por_etiqueta(texto_op, "Numero de cbu") or "CBU pendiente de verificación"
        fondo = (datos_op.fondo if datos_op and datos_op.fondo else analisis.fondo) or "FONDO COMPENSADOR"
        fondo = fondo.upper()
        articulo_dr = " ".join(
            valor
            for valor in (analisis.articulo, analisis.inciso)
            if valor
        ) or "artículo pendiente de parametrización"

        return {
            "FECHA": fecha,
            "ORDEN_PAGO": (
                getattr(analisis, "orden_pago", None) or "OP pendiente"
            ),
            "LIQUIDACION": (
                getattr(analisis, "liquidacion", None)
                or "Liquidación pendiente"
            ),
            "ID_SUNA": expediente.id_suna or "ID SUNA pendiente",
            "EXPEDIENTE": expediente.numero_interno,
            "DISPOSICION": "____/____",
            "PROVEEDOR": (
                proveedor
                if proveedor is not None
                else analisis.proveedor or "PROVEEDOR PENDIENTE"
            ),
            "CUIT": (
                cuit
                if cuit is not None
                else analisis.cuit or "CUIT PENDIENTE"
            ),
            "IMPORTE": formatear_moneda(importe_bruto),
            "IMPORTE_LETRAS": numero_a_letras(importe_bruto),
            "UC": formatear_numero(analisis.cantidad_uc, 2),
            "NORMA_UC": analisis.norma_uc or "norma pendiente de parametrización",
            "TABLA_FACTURAS": self._tabla_facturas(facturas),
            "CONCEPTO_PAGO": expediente.objeto or "concepto pendiente de completar",
            "ESTABLECIMIENTOS": expediente.establecimiento or "establecimientos pendientes de completar",
            "ARTICULO_DR": articulo_dr,
            "PROCEDIMIENTO": analisis.procedimiento or "procedimiento pendiente",
            "TABLA_DETALLE_OP": self._tabla_detalle_op(importe_bruto, retenciones, analisis.importe_neto, forma_pago, cbu),
            "FONDO": fondo,
            "EJERCICIO": ejercicio,
        }

    def _tabla_facturas(self, facturas) -> str:
        if not facturas:
            return "| Factura | Fecha | Importe |\n| --- | --- | ---: |\n| Factura pendiente | Fecha pendiente | Importe pendiente |"
        filas = ["| Factura | Fecha | Importe |", "| --- | --- | ---: |"]
        for factura in facturas:
            codigo = self._codigo_factura(factura)
            filas.append(f"| {codigo} | {factura.fecha} | {formatear_moneda(factura.importe)} |")
        return "\n".join(filas)

    def _tabla_detalle_op(self, importe_bruto, retenciones, importe_neto, forma_pago: str, cbu: str) -> str:
        filas = ["| Concepto | Detalle |", "| --- | ---: |"]
        filas.append(f"| Monto Total de Facturas | {formatear_moneda(importe_bruto)} |")
        for retencion in retenciones:
            filas.append(f"| {retencion.concepto} | {formatear_moneda(retencion.importe)} |")
        filas.append(f"| **Monto Neto a Pagar** | **{formatear_moneda(importe_neto)}** |")
        filas.append(f"| Forma de Pago | {forma_pago} |")
        filas.append(f"| Número de CBU | {cbu} |")
        return "\n".join(filas)

    def _codigo_factura(self, factura) -> str:
        letra = getattr(factura, "letra", "") or ""
        numero = getattr(factura, "numero", "") or ""
        if numero.startswith("FAC"):
            return numero
        return f"FAC[{letra}]{numero}" if letra else numero

    def _fecha_larga(self, fecha: str | None) -> str:
        if not fecha:
            
            hoy = datetime.now()
            meses = [
                "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
            ]
            return f"{hoy.day} de {meses[hoy.month]} de {hoy.year}"
        partes = re.split(r"[/-]", fecha)
        if len(partes) != 3:
            return fecha
        dia = int(partes[0])
        mes = int(partes[1])
        anio = partes[2]
        meses = [
            "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
        ]
        return f"{dia} de {meses[mes]} de {anio}"

    def _ejercicio(self, fecha: str | None) -> str:
        if fecha:
            partes = re.split(r"[/-]", fecha)
            if len(partes) == 3:
                return partes[2]
        return str(datetime.now().year)

    def _articulo_dr(self, procedimiento: str | None) -> str:
        if procedimiento == "Factura Conformada":
            return "18 inc. C"
        return "artículo pendiente de parametrización"

    def _extraer_por_etiqueta(self, texto: str, etiqueta: str) -> str | None:
        if not texto:
            return None
        patron = rf"{re.escape(etiqueta)}\s*[:.\- ]*(?:\.|\s)*(.+)"
        match = re.search(patron, texto, flags=re.IGNORECASE)
        if not match:
            return None
        valor = re.sub(r"\s+", " ", match.group(1)).strip(" .:-")
        return valor[:120] if valor else None

    @staticmethod
    def _evaluar_habilitacion(expediente_id: str, documento_op_id: str):
        habilitacion = evaluar_habilitacion_proveedor_op_service.evaluar(
            expediente_id, documento_op_id
        )
        if habilitacion.estado != EstadoHabilitacionProveedorOP.HABILITADO:
            raise BorradorDisposicionNoHabilitadoError(habilitacion)
        return habilitacion

    @staticmethod
    def _asegurar_mutable(expediente_id: str) -> None:
        expediente = expediente_service.obtener(expediente_id)
        estado = getattr(expediente, "estado", None)
        valor_estado = getattr(estado, "value", estado)
        if valor_estado in ESTADOS_TERMINALES_ORDINARIOS:
            raise ExpedienteTerminalError(
                expediente_id, valor_estado
            )

    @staticmethod
    def _obtener_seleccion_habilitante(
        seleccion_proveedor_id: str | None,
        expediente_id: str,
    ):
        if seleccion_proveedor_id is None:
            raise RuntimeError(
                "La habilitación no identifica la selección de proveedor."
            )
        seleccion = seleccion_proveedor_repository.obtener_por_id(
            seleccion_proveedor_id
        )
        if (
            seleccion is None
            or seleccion.id_seleccion != seleccion_proveedor_id
        ):
            raise RuntimeError(
                "No se encontró la selección de proveedor habilitante."
            )
        if seleccion.expediente_id != expediente_id:
            raise RuntimeError(
                "La selección habilitante no pertenece al Expediente."
            )
        return seleccion

    @staticmethod
    def _con_estado_actual(borrador: DisposicionRead, habilitacion):
        habilitado = (
            habilitacion.estado
            == EstadoHabilitacionProveedorOP.HABILITADO
        )
        mismo_contexto = habilitado and all(
            (
                borrador.control_proveedor_op_id
                == habilitacion.control_proveedor_op_id,
                borrador.seleccion_proveedor_id
                == habilitacion.seleccion_proveedor_id,
                borrador.proveedor_definitivo_id
                == habilitacion.proveedor_definitivo_id,
                borrador.proveedor_definitivo_cuit
                == habilitacion.proveedor_definitivo_cuit,
                borrador.proveedor_definitivo_razon_social
                == habilitacion.proveedor_definitivo_razon_social,
            )
        )
        return borrador.model_copy(
            update={
                "estado_habilitacion_actual": habilitacion.estado,
                "obsoleto": not mismo_contexto,
            }
        )


disposicion_service = DisposicionService()
