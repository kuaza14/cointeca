from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from string import Template
from typing import Iterable


@dataclass(frozen=True)
class ClauseTemplate:
    title: str
    body_template: str
    page_break_before: bool = False


def _format_currency(value: Decimal | int | float | None) -> str:
    if value is None:
        return "$0"
    return f"${value:,.0f}".replace(",", ".")


def _to_ddmmyyyy(value: date | None) -> str:
    if not value:
        return "-"
    return value.strftime("%d/%m/%Y")


def _safe_value(value: object | None, default: str = "-") -> str:
    if value in (None, ""):
        return default
    return str(value)


def _render(body_template: str, replacements: dict[str, str]) -> str:
    return Template(body_template).safe_substitute(replacements)


def _get_clause_templates() -> Iterable[ClauseTemplate]:
    return [
        ClauseTemplate(
            title="CLÁUSULA PRIMERA: OBJETO Y FUNCIONES",
            body_template=(
                "EL EMPLEADOR contrata los servicios personales de EL TRABAJADOR, para que éste "
                "desempeñe en forma exclusiva las funciones inherentes al cargo de "
                "<strong>${cargo}</strong>, en ${direccion_empresa}, y su desempeño de las "
                "actividades será donde sea enviado por motivo de las funciones de su cargo. "
                "Para desarrollar las actividades contenidas en el objeto, así como la ejecución "
                "de las tareas ordinarias y anexas al mencionado cargo, de conformidad con los "
                "reglamentos, ordenes e instrucciones que le imparta EL EMPLEADOR, observando en "
                "su cumplimiento la diligencia y el cuidado necesarios."
                "<br><br>"
                "<strong>PARÁGRAFO PRIMERO:</strong> Las funciones asociadas a su cargo son, "
                "entre otras: las propias del cargo de ${cargo}, brindar el soporte necesario "
                "para el desarrollo efectivo de las actividades operativas."
                "<br><br>"
                "<strong>PARÁGRAFO SEGUNDO:</strong> Las partes acuerdan expresamente que EL "
                "TRABAJADOR durante la vigencia de este contrato de trabajo, no podrá prestar "
                "directa o indirectamente sus servicios laborales a otros contratantes ni aportar "
                "su fuerza de trabajo en forma que afecte su salud u ocasione el desgaste de su "
                "organismo y esto le impida prestar eficazmente el servicio contenido en este contrato."
                "<br><br>"
                "<strong>PARÁGRAFO TERCERO:</strong> EL TRABAJADOR durante la vigencia del "
                "contrato podrá realizar labores que no fueran inherentes al cargo contratado, "
                "para desarrollar temporalmente las actividades contenidas en el objeto de la "
                "empresa usuaria, de conformidad con los reglamentos, ordenes e instrucciones que "
                "le imparta EL EMPLEADOR."
                "<br><br>"
                "<strong>PARÁGRAFO CUARTO:</strong> El incumplimiento de una de las obligaciones "
                "contenidas en esta cláusula, por una sola vez, será considerado como violación "
                "grave, para todos los efectos legales."
                "<br><br>"
                "<strong>PARÁGRAFO QUINTO:</strong> EL TRABAJADOR no podrá ceder el uso del "
                "vehículo a otras personas, ni transportar personal no autorizado, ni mover el "
                "vehículo para cosas distintas a las oficialmente asignadas por la empresa."
            ),
        ),
        ClauseTemplate(
            title="CLÁUSULA SEGUNDA: OBLIGACIONES DE EL TRABAJADOR",
            body_template=(
                "Además de las obligaciones determinadas en la Ley y en los reglamentos, EL "
                "TRABAJADOR se compromete a cumplir las siguientes obligaciones especiales: "
                "<strong>1)</strong> A poner al servicio de EL EMPLEADOR toda su capacidad normal "
                "de trabajo, en el desempeño de las funciones propias de la obra o labor "
                "contratada y, en las labores anexas complementarias del mismo, de conformidad "
                "con las ordenes e instrucciones que imparta EL EMPLEADOR, esto, a través de sus "
                "representantes autorizados, en virtud de la subordinación delegada. "
                "<strong>2)</strong> Llenar los registros de asistencia al lugar de trabajo "
                "(listado de asistencia o huellero dactilar), elemento que será parte integral "
                "para la liquidación de su contrato de obra labor. "
                "<strong>3)</strong> Cumplir el contrato de manera cuidadosa en el lugar, tiempo "
                "y condiciones que EL EMPLEADOR le señale y de acuerdo con los horarios que se "
                "fijen conforme a las necesidades del servicio. "
                "<strong>4)</strong> Llegar oportunamente al sitio de trabajo conforme a lo "
                "pactado y cumplir el horario establecido, salvo aquellos casos debidamente "
                "justificados y comprobados de fuerza mayor o caso fortuito, o previo permiso de "
                "la autoridad superior. "
                "<strong>5)</strong> Guardar absoluta y estricta reserva sobre los hechos, "
                "documentos físicos y/o electrónicos, informaciones y en general, sobre todos los "
                "asuntos y materias que lleguen a su conocimiento por razón de su oficio. "
                "<strong>6)</strong> Evitar cualquier disminución intencional del ritmo de "
                "trabajo o suspensión de labores injustificables e intempestivas o impedir el "
                "buen desarrollo de las labores de los demás compañeros. "
                "<strong>7)</strong> Mantener relaciones respetuosas y morales con los "
                "directivos, órganos de vigilancia y control y demás compañeros, favoreciendo un "
                "clima cordial y culto. "
                "<strong>8)</strong> Responder económicamente por las pérdidas de los dineros y "
                "demás bienes que estén bajo su manejo y responsabilidad. "
                "<strong>9)</strong> Ayudar al cuidado y ejecución de las labores en el trabajo, "
                "prevenir los accidentes de trabajo y las enfermedades profesionales, acatando "
                "las normas de higiene y seguridad industrial que determine el comité paritario "
                "de seguridad y salud en el trabajo de la EMPRESA. "
                "<strong>10)</strong> Presentarse al trabajo en óptimas condiciones para laborar, "
                "no alterados por estado de embriaguez o bajo la influencia de sustancias "
                "psicoactivas. "
                "<strong>11)</strong> Los correos electrónicos y mensajes vía WhatsApp referentes "
                "a asuntos laborales serán atendidos de manera prioritaria por el trabajador "
                "durante la jornada laboral o trabajo en casa, respetando siempre la vida "
                "personal y los espacios de descanso. "
                "<strong>12)</strong> EL TRABAJADOR que presente incapacidad deberá entregarla "
                "junto con sus soportes respectivos a EL EMPLEADOR a más tardar dentro de los dos "
                "(2) días hábiles siguientes a la expedición de la misma por medio de los canales "
                "dispuestos por EL EMPLEADOR. "
                "<strong>13)</strong> Cumplir con las demás obligaciones legales y reglamentarias. "
                "<strong>14)</strong> Participar en la ejecución, vigilancia y control de los "
                "programas y actividades de Seguridad y Salud en el Trabajo, por medio de sus "
                "representantes en los Comités de Medicina, Higiene y Seguridad Industrial de la "
                "empresa y asistir a los cursos y programas educativos. "
                "<strong>15)</strong> Dar estricto cumplimiento a las normas que para la "
                "Protección del Medio Ambiente se han trazado, evitando el deterioro ecológico y "
                "manteniendo la calidad ambiental. "
                "<strong>16)</strong> Cumplir permanentemente con espíritu de lealtad, "
                "colaboración y disciplina con la empresa. "
                "<strong>17)</strong> Permitir la prueba de alcoholimetría que se disponga a "
                "realizarle. "
                "<strong>18)</strong> Abstenerse de retirar de las instalaciones donde funcione "
                "la empresa, elementos, máquinas, útiles o papelería de propiedad del EMPLEADOR "
                "sin su autorización escrita. "
                "<strong>19)</strong> Será responsable de las fotos multas que ocasione en la "
                "prestación del servicio."
                "<br><br>"
                "<strong>PARÁGRAFO:</strong> El trabajador deberá responder por las herramientas "
                "y objetos que hacen parte del vehículo."
            ),
        ),
        ClauseTemplate(
            title="CLÁUSULA TERCERA: REMUNERACIÓN",
            body_template=(
                "EL EMPLEADOR pagará a EL TRABAJADOR un salario mensual de "
                "<strong>${salario}</strong> M/CTE. Adicionalmente, se reconocerá el auxilio de "
                "transporte legal vigente si a ello hubiere lugar."
                "<br><br>"
                "<strong>PARÁGRAFO PRIMERO:</strong> EL EMPLEADOR tiene organizado el pago del "
                "salario MES VENCIDO."
                "<br><br>"
                "<strong>PARÁGRAFO SEGUNDO:</strong> PAGOS QUE NO CONSTITUYEN SALARIO. Las partes "
                "expresamente acuerdan que lo que reciba el trabajador o llegue a recibir en el "
                "futuro, adicional a su salario ordinario, ya sean beneficios o auxilios "
                "habituales u ocasionales, tales como alimentación, habitación o vestuario, "
                "bonificaciones ocasionales o cualquier otra que reciba, en dinero o en especie, "
                "no constituye salario, acogiéndonos al Artículo 15 de la Ley 50 de 1990."
                "<br><br>"
                "<strong>PARÁGRAFO TERCERO:</strong> FORMA DE PAGO. Las partes acuerdan que el "
                "valor del salario pactado en la presente cláusula será cancelado a EL "
                "TRABAJADOR mediante transferencia electrónica, en la entidad bancaria y cuenta "
                "que el trabajador acredite, y en caso de no tener una cuenta bancaria se "
                "compromete a abrirla dentro de tres (3) días posteriores a la firma del presente "
                "contrato."
                "<br><br>"
                "<strong>PARÁGRAFO CUARTO:</strong> Para este efecto, prestarán mérito de "
                "comprobante de pago los documentos que acrediten tal consignación."
                "<br><br>"
                "<strong>PARÁGRAFO QUINTO:</strong> Según lo requerido por EL TRABAJADOR, EL "
                "EMPLEADOR podrá otorgar avances o préstamos, extraordinarios o periódicos, con "
                "cargo a las obligaciones laborales que obren a favor de EL TRABAJADOR. "
                "Expresamente acepta EL TRABAJADOR que los avances o préstamos que así se "
                "realicen a su favor NO constituyen un mayor valor de su salario."
                "<br><br>"
                "<strong>PARÁGRAFO SEXTO:</strong> Cuando por causa emanada directa o "
                "indirectamente de la relación contractual existan obligaciones de tipo económico "
                "a cargo de EL TRABAJADOR y a favor del EMPLEADOR, éste procederá a efectuar las "
                "deducciones a que hubiere lugar en cualquier tiempo y más concretamente, a la "
                "terminación del presente Contrato y la liquidación del Contrato Laboral, y así "
                "lo autoriza desde ahora EL TRABAJADOR."
            ),
        ),
        ClauseTemplate(
            title="CLÁUSULA CUARTA: DURACIÓN, PRÓRROGA Y JORNADA DEL CONTRATO",
            body_template=(
                "El presente contrato tendrá una duración de "
                "<strong>${tipo_contrato}</strong>, con fecha de inicio: "
                "<strong>${fecha_ingreso}</strong>. Si antes de la fecha de vencimiento ninguna "
                "de las partes avisare por escrito a la otra su determinación de no prorrogarlo, "
                "con una antelación no inferior a treinta (30) días, el contrato se entenderá "
                "renovado por un periodo igual al inicialmente pactado."
                "<br><br>"
                "<strong>PARÁGRAFO PRIMERO:</strong> Las partes pactan de común acuerdo un "
                "período de prueba correspondiente a los dos (2) primeros meses de labores. El "
                "detalle y los efectos de este periodo se especifican más adelante en el cuerpo "
                "de este contrato."
                "<br><br>"
                "El presente contrato se celebra POR OBRA O LABOR CONTRATADA, para realizar la "
                "conducción de un vehículo dentro de la ejecución de las obras eléctricas y "
                "civiles; estas se asignarán de acuerdo con el desarrollo de la obra, las "
                "capacidades y aptitudes del Trabajador y las necesidades del frente de trabajo. "
                "Las PARTES dejan expresa constancia de conocer y aceptar que la obra mencionada, "
                "como todas las obras eléctricas y civiles, van terminando gradualmente, a medida "
                "que van siendo concluidas las diferentes etapas o tramos de su ejecución, lo "
                "cual impone una disminución gradual y progresiva del personal empleado en ella. "
                "Ejecutada dicha obra o la parte de la obra pactada, se entenderá terminado el "
                "contrato de trabajo, sin necesidad de preaviso alguno."
                "<br><br>"
                "<strong>PARÁGRAFO SEGUNDO:</strong> Las partes convienen en que la jornada "
                "laboral que rige el presente contrato será la siguiente: se obliga a laborar una "
                "jornada ordinaria mínima de cuarenta y cuatro (44) horas semanales, en los "
                "turnos y dentro de las horas señaladas por EL EMPLEADOR, pudiendo hacer éste "
                "ajustes o cambios de horario cuando lo estime conveniente. Por acuerdo expreso o "
                "tácito de las partes, podrán repartirse las horas de la jornada ordinaria en la "
                "forma prevista en el artículo 164 del Código Sustantivo del Trabajo, modificado "
                "por el Art. 23 de la Ley 50 de 1990. EL TRABAJADOR y EL EMPLEADOR podrán acordar "
                "que la jornada semanal de cuarenta y cuatro (44) horas se realice mediante "
                "jornadas diarias flexibles de trabajo, distribuidas en máximo seis (6) días a la "
                "semana, dentro de la jornada ordinaria de 7:00 a.m. a 4:30 p.m. y sábados de "
                "7:00 a.m. a 11:00 a.m."
                "<br><br>"
                "<strong>PARÁGRAFO TERCERO:</strong> Estas disposiciones NO aplican para los "
                "trabajadores considerados como de dirección, manejo y confianza, ya que ellos NO "
                "están limitados a la jornada máxima laboral."
            ),
            page_break_before=True,
        ),
        ClauseTemplate(
            title="CLÁUSULA QUINTA: PERÍODO DE PRUEBA",
            body_template=(
                "EL TRABAJADOR está sujeto a un periodo de prueba que corresponde a dos (02) "
                "meses o la quinta parte de la duración de la obra o labor contratada, y por "
                "consiguiente cualquiera de las PARTES podrá terminar el contrato unilateralmente, "
                "en cualquier momento durante dicho periodo, sin que por este hecho se cause el "
                "pago de indemnización alguna, como lo establece el <strong>Art. 78 del C.S.T.</strong>"
            ),
        ),
        ClauseTemplate(
            title="CLÁUSULA SEXTA: CONFIANZA Y MANEJO",
            body_template=(
                "Si las funciones que desempeñe EL TRABAJADOR llegaren a considerarse como de "
                "dirección, manejo y confianza, éste se encuentra excluido de la regulación sobre "
                "jornada máxima legal y deberá trabajar el tiempo necesario para el cabal "
                "desempeño de sus funciones, sin perjuicio de cumplir los horarios mínimos "
                "establecidos por EL EMPLEADOR. Para el caso de este contrato laboral, el cargo "
                "para el cual es contratado EL TRABAJADOR NO es considerado como de dirección, "
                "manejo y confianza."
                "<br><br>"
                "<strong>PARÁGRAFO PRIMERO:</strong> Si por cualquier circunstancia EL "
                "TRABAJADOR prestare su servicio en día dominical o festivo, o en un horario "
                "adicional al mínimo establecido, no tendrá derecho a sobre remuneración alguna, "
                "si tal trabajo no hubiere sido autorizado por EL EMPLEADOR previamente; no "
                "obstante, cuando así se lo requiera EL EMPLEADOR, por necesidades de la labor "
                "para la cual ha sido contratado, EL TRABAJADOR se compromete a prestar sus "
                "servicios durante esos tiempos adicionales y no podrá negarse a ello, excepto "
                "que medie una causa debidamente justificada para el efecto."
            ),
        ),
        ClauseTemplate(
            title="CLÁUSULA SÉPTIMA: FALTAS GRAVES",
            body_template=(
                "Son justas causas para dar por terminado unilateralmente este contrato, por "
                "cualquiera de las partes, las enumeradas en los Arts. 62 y 63 del C.S.T., "
                "modificados por el Art. 7º del Decreto 2351/65 y además, por parte de EL "
                "EMPLEADOR, las faltas que para el efecto se califiquen como graves en "
                "reglamentos y demás documentos que contengan reglamentaciones, ordenes, "
                "instrucciones o prohibiciones de carácter general o particular. Expresamente "
                "se califican en este acto como faltas graves las siguientes:"
                "<br><br>"
                "<strong>a)</strong> La violación por parte de EL TRABAJADOR de cualquiera de "
                "sus obligaciones y prohibiciones legales, contractuales o reglamentarias, en "
                "particular las contempladas como tales en el Reglamento Interno de Trabajo. "
                "<strong>b)</strong> El retardo de diez (10) minutos en la hora de entrada, en "
                "un día o dentro del mismo mes, sin excusa suficiente. "
                "<strong>c)</strong> La falta en el trabajo en la mañana, en la tarde o en el "
                "turno correspondiente, sin excusa previa por primera vez. "
                "<strong>d)</strong> Faltar al trabajo durante el día sin excusa suficiente. "
                "<strong>e)</strong> La ejecución por parte de EL TRABAJADOR de labores "
                "remuneradas al servicio de terceros, sin que medie autorización previa, expresa "
                "y escrita de EL EMPLEADOR. "
                "<strong>f)</strong> Ausentarse del lugar de trabajo sin permiso del empleador o "
                "sin justa causa debidamente comprobada. "
                "<strong>g)</strong> La revelación de secretos y datos reservados de EL EMPLEADOR. "
                "<strong>h)</strong> Todo acto de violencia en que incurra EL TRABAJADOR fuera "
                "del servicio en contra del personal directivo de la Empresa o sus compañeros de "
                "trabajo. "
                "<strong>i)</strong> La negligencia en que incurra en su trabajo y por virtud de "
                "la cual se ponga en peligro la vida de sus compañeros, la seguridad del "
                "establecimiento, de los elementos de trabajo o de sus máquinas, herramientas, "
                "materias primas, productos en proceso o terminados. "
                "<strong>j)</strong> Realizar actos inseguros o no reportar los mismos en "
                "detrimento de la salud y la vida propia y la de los demás compañeros. "
                "<strong>k)</strong> No reportar incidentes y accidentes de trabajo al personal "
                "encargado o al área encargada dentro del día siguiente a su ocurrencia. "
                "<strong>l)</strong> Cambiar turno sin previa autorización de la jefatura del "
                "área por segunda vez. "
                "<strong>m)</strong> El abandono de sus obligaciones y responsabilidades, sin "
                "previa autorización de su superior. "
                "<strong>n)</strong> El hecho de que EL TRABAJADOR llegue embriagado a la "
                "Empresa o consuma dentro de ella licores o bebidas embriagantes, o drogas "
                "enervantes aún por la primera vez. "
                "<strong>o)</strong> El incumplimiento por parte de EL TRABAJADOR de cualquiera "
                "de las funciones específicas asignadas por la Empresa para su cargo a la firma "
                "del presente contrato, o las que le asignen posteriormente. "
                "<strong>p)</strong> Utilizar los recursos de la empresa para uso personal. "
                "<strong>q)</strong> Pelear, provocar riñas, amenazar, intimidar, coaccionar, "
                "usar lenguaje irrespetuoso o indecente para con sus compañeros o superiores "
                "dentro o fuera del trabajo. "
                "<strong>r)</strong> Crear o levantar falsos testimonios o rumores sobre "
                "compañeros, jefes, subordinados o superiores, dependientes, clientes y en "
                "general de las personas que intervienen con la empresa. "
                "<strong>s)</strong> Conservar armas de cualquier clase en el sitio de trabajo o "
                "dependencias de la empresa, excepto los trabajadores contratados para fines de "
                "seguridad. "
                "<strong>t)</strong> Proporcionar ambientes tensos y de discordia que pueda "
                "afectar el clima laboral. "
                "<strong>u)</strong> El uso indebido que haga de sumas de dinero entregadas como "
                "anticipo de gastos u otro motivo específico. "
                "<strong>v)</strong> Faltar a las actividades o capacitaciones programadas por "
                "la empresa sin justa causa o previo permiso. "
                "<strong>w)</strong> El uso indebido y/o negligencia en el cuidado de la "
                "dotación y demás implementos de seguridad industrial que le sean entregados por "
                "EL EMPLEADOR."
                "<br><br>"
                "<strong>PARÁGRAFO PRIMERO:</strong> La tolerancia por parte de EL EMPLEADOR de "
                "alguna(s) de las anteriores causales o de cualquier otra, no significan "
                "aceptación alguna a la misma y no impiden la terminación del presente contrato "
                "de trabajo en forma unilateral y con justa causa."
            ),
            page_break_before=True,
        ),
        ClauseTemplate(
            title="CLÁUSULA OCTAVA: ELEMENTOS Y HERRAMIENTAS",
            body_template=(
                "Los elementos, herramientas especiales de trabajo que se suministren a EL "
                "TRABAJADOR, tales como dotaciones, carnés, computadores, entre otros objetos y "
                "elementos, deben ser conservados por EL TRABAJADOR y devueltos a la Empresa a "
                "la terminación del contrato de trabajo, mediante acta de entrega."
                "<br><br>"
                "<strong>PARÁGRAFO PRIMERO:</strong> Responder por la integridad y el buen orden "
                "de los útiles, maquinaria, equipo y cualquier clase de elementos que EL "
                "EMPLEADOR ponga bajo su responsabilidad y cuidado para la correcta ejecución de "
                "las tareas a cargo de EL TRABAJADOR. Cuando ocurriesen daños o pérdidas no "
                "imputables al uso normal de dichos elementos, EL TRABAJADOR pagará el valor "
                "comercial del objeto dañado o perdido, o el precio del arreglo, siempre que a "
                "juicio de EL EMPLEADOR tal arreglo sea posible. Cualquier obligación pendiente "
                "a cargo de EL TRABAJADOR y a favor de EL EMPLEADOR por este concepto podrá ser "
                "deducida o compensada, facultad cuyo ejercicio en forma expresa acepta EL "
                "TRABAJADOR."
            ),
        ),
        ClauseTemplate(
            title="CLÁUSULA NOVENA: INVENCIONES Y DESCUBRIMIENTOS",
            body_template=(
                "Los derechos patrimoniales derivados de las invenciones o descubrimientos "
                "realizados por EL TRABAJADOR pertenecen a EL EMPLEADOR, sin perjuicio de los "
                "derechos morales de autor que permanecerán en cabeza del creador de la obra, de "
                "acuerdo con la Ley 23 de 1982 y la Decisión 351 de la Comisión del Acuerdo de "
                "Cartagena."
            ),
        ),
        ClauseTemplate(
            title="CLÁUSULA DÉCIMA: REGLAMENTOS",
            body_template=(
                "Forman parte del presente contrato los reglamentos de EL EMPLEADOR tales como: "
                "Reglamento Interno de Trabajo, Reglamento de Higiene y Seguridad Industrial y "
                "Manual de Funciones."
                "<br><br>"
                "<strong>PARÁGRAFO PRIMERO:</strong> EL EMPLEADOR queda facultado para imponer a "
                "EL TRABAJADOR sanciones disciplinarias consistentes en suspensión no mayor a "
                "ocho (8) días por la primera falta y hasta dos (2) meses en caso de "
                "reincidencia, según formato de sanciones disciplinarias, de conformidad con la "
                "ley laboral vigente y el Reglamento Interno de Trabajo."
            ),
        ),
        ClauseTemplate(
            title="CLÁUSULA DÉCIMA PRIMERA: CONFIDENCIALIDAD",
            body_template=(
                "EL TRABAJADOR se compromete a mantener un convenio de confidencialidad especial "
                "en cumplimiento a la normatividad relacionada con la protección de datos "
                "personales (Ley 1581 de 2012)."
                "<br><br>"
                "<strong>PARÁGRAFO PRIMERO — CONFIDENCIALIDAD:</strong> Toda información que "
                "conozca EL TRABAJADOR relacionada con datos personales de los trabajadores de la "
                "empresa como consecuencia del manejo a su cargo de las bases de datos existentes "
                "en la compañía es completamente reservada. EL TRABAJADOR se compromete a guardar "
                "la más estricta reserva sobre dicha información y a no divulgarla a terceros sin "
                "autorización del trabajador titular ni a usarla para propósitos distintos del "
                "cumplimiento de sus obligaciones laborales."
                "<br><br>"
                "<strong>a)</strong> Es deber especial a cargo del trabajador responsable de las "
                "bases de datos garantizar la reserva de la información, conservarla bajo "
                "condiciones de seguridad necesarias para impedir su adulteración, pérdida, "
                "consulta, uso o acceso no autorizado o fraudulento. "
                "<strong>b)</strong> La violación de este acuerdo de confidencialidad, a juicio "
                "de la empresa, será considerada falta grave y causal de terminación contractual "
                "con justa causa imputable a EL TRABAJADOR. "
                "<strong>c)</strong> El presente acuerdo obedece al principio de bilateralidad "
                "contractual y es resultado de la libre voluntad de las partes. "
                "<strong>d)</strong> La parte receptora de la información solo podrá revelar "
                "información de la otra a quienes la requieran judicialmente o mediante explícita "
                "autorización del propietario de la información. "
                "<strong>e)</strong> El incumplimiento de cualquiera de las partes de la "
                "cláusula de confidencialidad la constituirá en deudora de la otra, por la suma "
                "equivalente a cinco (5) Salarios Mínimos Legales Mensuales Vigentes, a título de "
                "pena, sin menoscabo del pago de la indemnización de perjuicios que pudieran "
                "ocasionarse."
                "<br><br>"
                "En caso de incumplimiento del objeto del presente contrato se podrá cobrar "
                "ejecutivamente el valor de la cláusula penal y la indemnización por perjuicios "
                "que demuestre sufrir el acreedor. Las partes aceptan que, para todos los efectos "
                "legales, el presente contrato presta mérito ejecutivo."
            ),
        ),
        ClauseTemplate(
            title="CLÁUSULA DÉCIMA SEGUNDA: AUTORIZACIÓN PARA EL TRATAMIENTO DE DATOS PERSONALES",
            body_template=(
                "EL TRABAJADOR autoriza expresamente a EL EMPLEADOR para que, en los términos del "
                "literal a) del artículo 6 de la Ley 1581 de 2012, realice la recolección, "
                "almacenamiento, uso, circulación, supresión y en general tratamiento de sus "
                "datos personales, incluyendo datos sensibles tales como huellas digitales, "
                "fotografías, videos y demás datos que puedan llegar a ser considerados sensibles "
                "de conformidad con la Ley, para que dicho tratamiento se realice con el fin de "
                "ejecutar el control, seguimiento, monitoreo, vigilancia y en general garantizar "
                "la seguridad de las instalaciones; así como para documentar las actividades "
                "empresariales y almacenar dichos datos en la base de datos y sistemas o software "
                "de la empresa."
                "<br><br>"
                "EL TRABAJADOR autoriza de manera libre y voluntaria a la empresa COINTECA SAS, "
                "identificada con NIT 900.768.648-3, al manejo de su información personal "
                "consignada en la base de datos de EL EMPLEADOR, así como el envío de "
                "comunicaciones, novedades y modificaciones de sus productos y servicios, "
                "conforme a lo previsto en la Ley 1581 de 2012 y el Decreto 1377 de 2013."
            ),
        ),
        ClauseTemplate(
            title="CLÁUSULA DÉCIMA TERCERA: MODIFICACIÓN DE LAS CONDICIONES LABORALES",
            body_template=(
                "EL TRABAJADOR acepta desde ahora expresamente todas las modificaciones de sus "
                "condiciones laborales determinadas por EL EMPLEADOR en ejercicio de su poder "
                "subordinante, tales como los turnos y jornadas de trabajo, el lugar de "
                "prestación del servicio, el cargo u oficio y/o funciones y la forma de "
                "remuneración, siempre que tales modificaciones no afecten su honor, dignidad o "
                "sus derechos mínimos, ni impliquen desmejoras sustanciales o graves perjuicios "
                "para él, de conformidad con lo dispuesto por el artículo 23 del C.S.T. "
                "modificado por el artículo 1 de la Ley 50/90. Los gastos que se originen con el "
                "traslado de lugar de prestación del servicio serán cubiertos por EL EMPLEADOR, "
                "de conformidad con el numeral 8 del artículo 57 del C.S.T."
                "<br><br>"
                "<strong>PARÁGRAFO PRIMERO:</strong> Las partes podrán convenir que el trabajo "
                "se preste en lugar distinto del inicialmente contratado, siempre que tales "
                "traslados no desmejoren las condiciones laborales o de remuneración de EL "
                "TRABAJADOR, o impliquen perjuicios para él."
            ),
        ),
        ClauseTemplate(
            title="CLÁUSULA DÉCIMA CUARTA: DIRECCIÓN PARA NOTIFICACIÓN",
            body_template=(
                "EL TRABAJADOR, para todos los efectos legales y en especial para la aplicación "
                "del parágrafo 1 del artículo 29 de la Ley 789/02, norma que modificó el artículo "
                "65 del C.S.T., se compromete a informar por escrito y de manera inmediata a EL "
                "EMPLEADOR cualquier cambio en su dirección de residencia, teniéndose en todo "
                "caso como suya la última dirección registrada en su hoja de vida."
                "<br><br>"
                "<strong>PARÁGRAFO PRIMERO:</strong> En forma expresa manifiesta EL TRABAJADOR "
                "que la información suministrada que aparece en la parte inicial de este "
                "contrato es cierta y forma parte integral del mismo."
            ),
        ),
        ClauseTemplate(
            title="CLÁUSULA DÉCIMA QUINTA: EFECTOS Y EXCLUSIÓN DE VÍNCULO ADICIONAL",
            body_template=(
                "El presente contrato reemplaza en su integridad y deja sin efecto cualquier "
                "otro contrato, verbal o escrito, celebrado entre las partes con anterioridad, "
                "pudiendo las partes convenir por escrito modificaciones al mismo, las que "
                "formarán parte integrante de este contrato, al igual que las circulares e "
                "instrucciones impartidas que complementen, adicionen o desarrollen las "
                "previsiones contenidas en el presente documento."
                "<br><br>"
                "EL TRABAJADOR no adquiere, ni adquirirá, por razón de la suscripción y "
                "ejecución del presente contrato, vínculo laboral alguno con los contratantes de "
                "EL EMPLEADOR. Toda responsabilidad derivada de este instrumento correrá a cargo "
                "exclusivo de EL TRABAJADOR."
                "<br><br>"
                "<strong>PARÁGRAFO PRIMERO:</strong> En aplicación de lo antes indicado, dada la "
                "exclusión de vínculo adicional, EL TRABAJADOR declara conocer y acepta la "
                "cláusula de indemnidad que rige el contrato suscrito entre EL EMPLEADOR y su "
                "contratante."
            ),
        ),
    ]


def build_contract_context(empleado) -> dict:
    today = date.today()
    start_date = empleado.fecha_ingreso

    contract_number = f"CT-{today.year}-{empleado.id:04d}"

    replacements = {
        "empleado_nombre": _safe_value(empleado.nombre_completo),
        "documento": _safe_value(empleado.documento),
        "cargo": _safe_value(empleado.cargo),
        "tipo_contrato": _safe_value(getattr(empleado, "get_tipo_contrato_display", lambda: empleado.tipo_contrato)()),
        "jornada": _safe_value(getattr(empleado, "get_jornada_display", lambda: empleado.jornada)()),
        "fecha_ingreso": _to_ddmmyyyy(start_date),
        "salario": _format_currency(getattr(empleado, "salario", 0)),
        "direccion": _safe_value(empleado.direccion),
        "telefono": _safe_value(empleado.telefono),
        "correo": _safe_value(empleado.correo),
        "direccion_empresa": "Carrera 8a # 49-53, Santiago de Cali",
    }

    clauses = [
        {
            "title": clause.title,
            "body": _render(clause.body_template, replacements),
            "page_break_before": clause.page_break_before,
        }
        for clause in _get_clause_templates()
    ]

    intro_template = (
        "Entre los suscritos a saber, por una parte, <strong>COINTECA SAS</strong> identificada "
        "con NIT 900.768.648-3, representada legalmente por <strong>MAYRA ALEJANDRA OCORÓ</strong>, "
        "mayor de edad y vecina del Municipio de Padilla, identificada como aparece al pie de su "
        "firma, quien en adelante se llamará <strong>“EL EMPLEADOR”</strong>, y por otra "
        "<strong>${empleado}</strong>, mayor de edad y vecino(a) de la ciudad de ${direccion}, "
        "identificado(a) con cédula de ciudadanía No. <strong>${documento}</strong>, con "
        "nacionalidad COLOMBIANA, quien actúa en nombre propio y quien en adelante se llamará "
        "<strong>“EL TRABAJADOR”</strong>, se ha celebrado el contrato de trabajo, el cual se "
        "regirá por las normas del Código Sustantivo del Trabajo, el Reglamento Interno de la "
        "empresa y por las siguientes cláusulas:"
    )
    intro = _render(
        intro_template,
        {
            "empleado": replacements["empleado_nombre"],
            "documento": replacements["documento"],
            "direccion": replacements["direccion"],
        },
    )

    return {
        "empleado": empleado,
        "is_pdf": False,
        "header": {
            "doc_type": "Formato",
            "doc_code": "RRHH-RE-01",
            "version": "3",
            "issue_date": _to_ddmmyyyy(today),
            "title": "CONTRATO INDIVIDUAL DE TRABAJO",
            "contract_number": contract_number,
        },
        "company": {
            "name": "Comercializadora de Ingeniería y Tecnologías Aplicadas S.A.S - COINTECA S.A.S",
            "nit": "900.768.648-3",
            "address": "Carrera 8a # 49-53, Santiago de Cali",
            "email": "cointecasas@hotmail.com",
            "phone": "3117121043",
            "web": "www.cointecasas.com",
            "legal_representative": "Mayra Alejandra Ocoró Possu",
        },
        "employee_rows": [
            ("Nombre del trabajador", replacements["empleado_nombre"]),
            ("Documento", replacements["documento"]),
            ("Dirección", replacements["direccion"]),
            ("Teléfono", replacements["telefono"]),
            ("Correo", replacements["correo"]),
            ("Cargo", replacements["cargo"]),
            ("Tipo de contrato", replacements["tipo_contrato"]),
            ("Fecha de ingreso", replacements["fecha_ingreso"]),
            ("Salario", replacements["salario"]),
        ],
        "intro": intro,
        "clauses": clauses,
        "signature_city": "Santiago de Cali",
        "signature_date": _to_ddmmyyyy(start_date or today),
    }
