"""
Taxonomía manual jerárquica para proyectos de ley chilenos (2020-2026).

Estructura:
  TAXONOMY[codigo_categoria] = {
    label, definition, keywords, synonyms, prototype_texts,
    subcategorias: {
      codigo_sub: {
        label, definition, keywords, synonyms, etiquetas,
        ejemplos_positivos, ejemplos_negativos, reglas_semanticas
      }
    }
  }

Nivel 1: Categoría (10)
Nivel 2: Subcategoría (3–5 por categoría)
Nivel 3: Etiquetas (tags específicas)
"""

TAXONOMY: dict = {

    # ─────────────────────────────────────────────────────────────
    "DERECHO_LABORAL_EMPLEO": {
        "label": "Derecho Laboral y Empleo",
        "definition": "Normas que regulan las relaciones entre trabajadores y empleadores, condiciones laborales, seguridad social, sindicatos y protección del empleo.",
        "keywords": [
            "contrato de trabajo", "trabajador", "empleador", "despido", "remuneración",
            "jornada laboral", "horas extra", "licencia médica", "fuero", "indemnización",
            "AFP", "pensión", "jubilación", "cotización", "seguro de cesantía",
            "sindicato", "huelga", "negociación colectiva", "convenio colectivo",
            "accidente del trabajo", "enfermedad profesional", "mutualidad",
            "trabajo doméstico", "teletrabajo", "trabajo a distancia",
            "subcontratación", "honorarios", "finiquito",
        ],
        "synonyms": ["legislación laboral", "derecho del trabajo", "empleo", "previsión social"],
        "prototype_texts": [
            "Modifica el Código del Trabajo para establecer nuevos derechos laborales.",
            "Regula el contrato de trabajo y las condiciones mínimas de empleo.",
            "Crea un seguro de desempleo para trabajadores afectados por crisis.",
            "Establece obligaciones del empleador en materia de seguridad laboral.",
        ],
        "subcategorias": {
            "CONTRATOS_LABORALES": {
                "label": "Contratos y relaciones laborales",
                "definition": "Regulación del contrato individual de trabajo, modalidades contractuales, despidos, finiquitos y protección del trabajador.",
                "keywords": [
                    "contrato de trabajo", "contrato indefinido", "contrato plazo fijo",
                    "despido injustificado", "despido", "finiquito", "indemnización por años",
                    "remuneración mínima", "salario mínimo", "jornada de trabajo",
                    "descanso", "feriado legal", "vacaciones", "licencia", "fuero maternal",
                    "teletrabajo", "trabajo a distancia", "trabajo por turnos",
                    "subcontratación", "multirut", "honorarios",
                ],
                "synonyms": ["relación laboral", "vínculo laboral", "empleador trabajador"],
                "etiquetas": ["contrato_trabajo", "despido", "remuneraciones", "jornada", "teletrabajo", "subcontratacion"],
                "ejemplos_positivos": [
                    "Modifica el artículo 159 del Código del Trabajo para regular las causales de terminación del contrato",
                    "Establece el salario mínimo garantizado para trabajadores de jornada parcial",
                    "Regula el trabajo a distancia y teletrabajo",
                ],
                "ejemplos_negativos": [
                    "Aumenta las penas para el delito de robo",
                    "Establece un programa de subsidios habitacionales",
                ],
                "reglas_semanticas": [
                    r"contrato\s+de\s+trabajo",
                    r"código\s+del\s+trabajo",
                    r"despido\s+(injustificado|procedente|improcedente)?",
                    r"(salario|sueldo|remuneración)\s+mínimo",
                    r"jornada\s+(laboral|de trabajo|ordinaria)",
                    r"teletrabajo|trabajo\s+a\s+distancia",
                    r"finiquito|indemnización\s+por\s+años",
                ],
            },
            "SEGURIDAD_SOCIAL": {
                "label": "Seguridad social y previsión",
                "definition": "Sistema de pensiones, AFPs, jubilación, cotizaciones previsionales, seguros de cesantía y salud previsional.",
                "keywords": [
                    "AFP", "pensión", "jubilación", "cotización previsional", "fondo de pensiones",
                    "seguro de cesantía", "AFC", "IPS", "pensión básica solidaria",
                    "aporte previsional solidario", "pilar solidario", "retiro de fondos",
                    "10%", "retiro AFP", "sistema previsional", "multiafiliación",
                    "bono de invierno", "pensión de vejez", "pensión de invalidez",
                ],
                "synonyms": ["previsión social", "sistema de pensiones", "AFP", "jubilación"],
                "etiquetas": ["AFP", "pensiones", "jubilacion", "cotizaciones", "seguro_cesantia"],
                "ejemplos_positivos": [
                    "Permite el retiro excepcional del 10% de los fondos acumulados en AFP",
                    "Crea el sistema de pensiones solidarias financiado por cotizaciones adicionales del empleador",
                    "Modifica la ley N°20.255 para mejorar las pensiones de vejez",
                ],
                "ejemplos_negativos": [
                    "Establece el salario mínimo en Chile",
                    "Regula el contrato de trabajo doméstico",
                ],
                "reglas_semanticas": [
                    r"\bAFP\b|\bIPS\b|\bAFC\b",
                    r"(retiro|fondos)\s+(previsionales?|de\s+pensiones?|AFP)",
                    r"pensión\s+(de\s+vejez|de\s+invalidez|básica|solidaria)?",
                    r"cotización\s+previsional",
                    r"seguro\s+de\s+cesantía",
                    r"sistema\s+previsional",
                ],
            },
            "SALUD_OCUPACIONAL": {
                "label": "Salud ocupacional y riesgos laborales",
                "definition": "Prevención de accidentes del trabajo, enfermedades profesionales, seguridad en faenas y organismos administradores.",
                "keywords": [
                    "accidente del trabajo", "enfermedad profesional", "accidente laboral",
                    "mutualidad", "ACHS", "IST", "MUSEG", "seguridad laboral",
                    "prevención de riesgos", "higiene industrial", "riesgo laboral",
                    "faenas mineras", "exposición a contaminantes", "silicosis",
                    "protocolo COVID laboral", "mesa de trabajo segura",
                ],
                "synonyms": ["seguridad laboral", "prevención de riesgos", "higiene ocupacional"],
                "etiquetas": ["accidente_trabajo", "enfermedad_profesional", "prevencion_riesgos", "mutualidades"],
                "ejemplos_positivos": [
                    "Fortalece la fiscalización de la Dirección del Trabajo en materia de seguridad",
                    "Establece protocolo de vigilancia para enfermedades profesionales por exposición a polvo de sílice",
                ],
                "ejemplos_negativos": [
                    "Regula el sistema de pensiones de vejez",
                    "Crea el seguro de desempleo",
                ],
                "reglas_semanticas": [
                    r"accidente\s+del\s+trabajo",
                    r"enfermedad\s+profesional",
                    r"mutualidad|ACHS|IST|MUSEG",
                    r"prevención\s+de\s+riesgos",
                    r"seguridad\s+(en\s+el\s+trabajo|laboral|ocupacional)",
                ],
            },
            "SINDICALISMO": {
                "label": "Sindicalismo y negociación colectiva",
                "definition": "Regulación de sindicatos, negociación colectiva, huelga, fuero sindical y relaciones colectivas de trabajo.",
                "keywords": [
                    "sindicato", "sindicato de trabajadores", "federación sindical",
                    "negociación colectiva", "contrato colectivo", "convenio colectivo",
                    "huelga", "lock-out", "mediación", "arbitraje laboral",
                    "fuero sindical", "director sindical", "afiliación sindical",
                    "CUT", "organización sindical", "práctica antisindical",
                ],
                "synonyms": ["organización sindical", "acción sindical", "colectivo laboral"],
                "etiquetas": ["sindicato", "huelga", "negociacion_colectiva", "fuero_sindical"],
                "ejemplos_positivos": [
                    "Modifica el Código del Trabajo para fortalecer la negociación colectiva ramal",
                    "Establece nuevas causales de fuero sindical para directores de sindicato",
                ],
                "ejemplos_negativos": [
                    "Establece la renta mínima garantizada",
                    "Crea el seguro de cesantía",
                ],
                "reglas_semanticas": [
                    r"\bsindicato|\bsindical\b",
                    r"negociación\s+colectiva",
                    r"contrato\s+colectivo|convenio\s+colectivo",
                    r"\bhuelga\b",
                ],
            },
            "TRABAJO_ESPECIAL": {
                "label": "Regímenes laborales especiales",
                "definition": "Trabajo doméstico, trabajadores migrantes, trabajo adolescente, temporeros, trabajo en plataformas digitales.",
                "keywords": [
                    "trabajo doméstico", "trabajadora de casa particular", "asesora del hogar",
                    "trabajador migrante", "trabajador extranjero", "visa de trabajo",
                    "trabajo infantil", "trabajo adolescente", "trabajo menores de edad",
                    "temporero", "trabajador de temporada", "trabajador agrícola",
                    "plataforma digital", "Uber", "delivery", "gig economy",
                    "trabajo a honorarios", "trabajador independiente",
                ],
                "synonyms": ["trabajo informal", "economía de plataformas", "migrantes laborales"],
                "etiquetas": ["trabajo_domestico", "migrantes", "plataformas_digitales", "temporeros"],
                "ejemplos_positivos": [
                    "Regula el contrato de trabajo de las trabajadoras de casa particular",
                    "Crea un régimen especial para trabajadores de plataformas digitales como Uber y Rappi",
                ],
                "ejemplos_negativos": [
                    "Modifica el Código Penal para sancionar el narcotráfico",
                    "Crea el sistema de pensiones solidarias",
                ],
                "reglas_semanticas": [
                    r"trabajo\s+doméstico|trabajadora\s+de\s+casa\s+particular",
                    r"trabajador(a)?\s+(migrante|extranjero|inmigrante)",
                    r"plataforma\s+digital|economía\s+de\s+plataformas",
                    r"trabajo\s+(infantil|adolescente)",
                    r"trabajador(a)?\s+independiente|honorarios",
                ],
            },
        },
    },

    # ─────────────────────────────────────────────────────────────
    "SALUD_PUBLICA": {
        "label": "Salud Pública",
        "definition": "Cobertura y acceso al sistema de salud, medicamentos, salud mental, enfermedades, regulación de profesionales sanitarios y hospitales.",
        "keywords": [
            "salud", "hospital", "clínica", "médico", "enfermera", "paciente",
            "FONASA", "ISAPRE", "GES", "AUGE", "atención médica", "urgencia",
            "medicamento", "fármaco", "receta médica", "genérico", "biosimilar",
            "salud mental", "psiquiatría", "psicología", "depresión", "suicidio",
            "pandemia", "COVID-19", "coronavirus", "cuarentena", "vacuna",
            "cáncer", "enfermedad crónica", "lista de espera",
        ],
        "synonyms": ["sistema sanitario", "atención médica", "sanidad", "salud pública"],
        "prototype_texts": [
            "Modifica el sistema FONASA para ampliar la cobertura de prestaciones de salud.",
            "Regula el precio de medicamentos y establece bioequivalencia obligatoria.",
            "Crea un plan nacional de salud mental con cobertura garantizada.",
            "Establece medidas sanitarias de emergencia ante pandemia COVID-19.",
        ],
        "subcategorias": {
            "COBERTURA_SANITARIA": {
                "label": "Acceso y cobertura sanitaria",
                "definition": "FONASA, ISAPREs, GES/AUGE, listas de espera, copagos, y acceso universal a la salud.",
                "keywords": [
                    "FONASA", "ISAPRE", "GES", "AUGE", "cobertura de salud",
                    "plan de salud", "prima de salud", "tabla de factores",
                    "lista de espera", "atención primaria", "CESFAM", "consultorio",
                    "copago", "prestación de salud", "ley de isapres",
                    "portabilidad financiera", "superación de crisis isapres",
                ],
                "synonyms": ["seguro de salud", "previsión de salud", "aseguramiento sanitario"],
                "etiquetas": ["FONASA", "ISAPRE", "GES_AUGE", "lista_espera", "cobertura"],
                "ejemplos_positivos": [
                    "Modifica la ley de ISAPREs para eliminar la tabla de factores discriminatoria",
                    "Amplía las garantías del plan GES para incluir nuevas enfermedades",
                ],
                "ejemplos_negativos": [
                    "Regula el precio de los medicamentos en farmacias",
                    "Establece el sistema de cotizaciones para AFP",
                ],
                "reglas_semanticas": [
                    r"\bFONASA\b|\bISAPRE\b",
                    r"\bGES\b|\bAUGE\b",
                    r"cobertura\s+(de\s+)?salud",
                    r"lista\s+de\s+espera",
                    r"plan\s+de\s+salud",
                    r"tabla\s+de\s+factores",
                ],
            },
            "MEDICAMENTOS": {
                "label": "Medicamentos y regulación farmacéutica",
                "definition": "Regulación de precios de medicamentos, fármacos genéricos, bioequivalencia, cadena de distribución y farmacias.",
                "keywords": [
                    "medicamento", "fármaco", "genérico", "bioequivalente", "biosimilar",
                    "precio de medicamentos", "farmacia", "ISP", "registro sanitario",
                    "prescripción", "receta médica", "venta directa", "automedicación",
                    "monopolio farmacéutico", "colusión farmacias", "banda de precios",
                    "cannabis medicinal", "cannabidiol", "CBD",
                ],
                "synonyms": ["fármacos", "medicinas", "industria farmacéutica"],
                "etiquetas": ["medicamentos", "farmacias", "genericos", "precios_farmacos", "cannabis_medicinal"],
                "ejemplos_positivos": [
                    "Establece precios máximos para medicamentos esenciales en el mercado chileno",
                    "Regula el uso medicinal del cannabis y sus derivados",
                    "Obliga a farmacias a tener stock de medicamentos genéricos",
                ],
                "ejemplos_negativos": [
                    "Crea el plan nacional de salud mental",
                    "Amplía la cobertura del GES",
                ],
                "reglas_semanticas": [
                    r"medicamento|fármaco|medicina\b",
                    r"genérico|bioequivalente|biosimilar",
                    r"precio(s)?\s+de\s+(los\s+)?medicamentos",
                    r"farmacia(s)?",
                    r"cannabis\s+medicinal|CBD|cannabidiol",
                    r"receta\s+médica",
                ],
            },
            "SALUD_MENTAL": {
                "label": "Salud mental y psiquiatría",
                "definition": "Atención en salud mental, regulación de psiquiatría, prevención del suicidio, consumo de sustancias y derechos de usuarios de salud mental.",
                "keywords": [
                    "salud mental", "salud mental comunitaria", "psiquiatría", "psicólogo",
                    "depresión", "ansiedad", "trastorno mental", "esquizofrenia",
                    "suicidio", "prevención del suicidio", "ideación suicida",
                    "consumo de drogas", "adicción", "SENDA", "COSAM",
                    "internación psiquiátrica", "hospitalización involuntaria",
                    "derechos de usuarios psiquiátricos",
                ],
                "synonyms": ["salud mental", "bienestar psicológico", "psiquiatría", "psicología clínica"],
                "etiquetas": ["salud_mental", "suicidio", "adicciones", "psiquiatria", "SENDA"],
                "ejemplos_positivos": [
                    "Crea un plan nacional de salud mental garantizado con financiamiento público",
                    "Establece protocolo de prevención del suicidio en establecimientos educacionales",
                    "Regula la internación involuntaria en establecimientos psiquiátricos",
                ],
                "ejemplos_negativos": [
                    "Amplía cobertura GES para cáncer",
                    "Regula el precio de los medicamentos",
                ],
                "reglas_semanticas": [
                    r"salud\s+mental",
                    r"\bsuicidio|\bsuicida\b",
                    r"psiquiatría|psiquiátrico|psicólogo|psicológico",
                    r"depresión|ansiedad|trastorno\s+(mental|psiquiátrico)",
                    r"\bSENDA\b|\bCOSAM\b",
                ],
            },
            "EPIDEMIAS_PANDEMIAS": {
                "label": "Enfermedades infecciosas y pandemia",
                "definition": "Respuesta a COVID-19, medidas sanitarias de emergencia, vacunas, cuarentenas y regulación de epidemias.",
                "keywords": [
                    "COVID-19", "coronavirus", "SARS-CoV-2", "pandemia", "epidemia",
                    "cuarentena", "cordón sanitario", "toque de queda", "confinamiento",
                    "vacuna", "vacunación", "inmunización", "pasaporte sanitario",
                    "emergencia sanitaria", "Estado de excepción sanitaria",
                    "teleconsulta", "telemedicina", "distanciamiento social",
                ],
                "synonyms": ["pandemia", "emergencia sanitaria", "brote infeccioso"],
                "etiquetas": ["COVID19", "pandemia", "vacunas", "cuarentena", "emergencia_sanitaria"],
                "ejemplos_positivos": [
                    "Regula las medidas de confinamiento y cuarentena ante la pandemia de COVID-19",
                    "Establece el proceso de vacunación obligatoria contra el coronavirus",
                    "Crea prestaciones especiales para trabajadores durante la emergencia sanitaria",
                ],
                "ejemplos_negativos": [
                    "Modifica el sistema de pensiones del sector público",
                    "Regula el precio de los medicamentos de uso crónico",
                ],
                "reglas_semanticas": [
                    r"COVID[-\s]?19|coronavirus|SARS[-\s]?CoV",
                    r"pandemia|epidemia",
                    r"cuarentena|confinamiento|cordón\s+sanitario",
                    r"vacuna(ción)?|inmunización",
                    r"emergencia\s+sanitaria",
                ],
            },
            "REGULACION_PROFESIONAL_SALUD": {
                "label": "Profesionales y establecimientos de salud",
                "definition": "Regulación de profesionales de la salud, habilitación de establecimientos, responsabilidad médica y carrera sanitaria.",
                "keywords": [
                    "médico", "enfermera", "matrona", "kinesiólogo", "farmacéutico",
                    "título médico", "colegio médico", "EUNACOM", "carrera funcionaria",
                    "responsabilidad médica", "negligencia médica", "mala praxis",
                    "hospital público", "clínica privada", "establecimiento de salud",
                    "acreditación hospitalaria", "guardias médicas",
                ],
                "synonyms": ["profesionales sanitarios", "personal de salud"],
                "etiquetas": ["profesionales_salud", "hospitales", "negligencia_medica", "carrera_sanitaria"],
                "ejemplos_positivos": [
                    "Establece el régimen de responsabilidad médica y obligación de informar al paciente",
                    "Crea la carrera funcionaria para médicos del sector público",
                ],
                "ejemplos_negativos": [
                    "Regula los precios de los medicamentos",
                    "Amplía el sistema GES",
                ],
                "reglas_semanticas": [
                    r"médico(s)?|enfermera(s)?|profesional(es)?\s+de\s+salud",
                    r"(título|grado)\s+(médico|profesional)\s+de\s+salud",
                    r"negligencia\s+médica|mala\s+praxis|responsabilidad\s+médica",
                    r"hospital\s+público|establecimiento(s)?\s+de\s+salud",
                ],
            },
        },
    },

    # ─────────────────────────────────────────────────────────────
    "EDUCACION": {
        "label": "Educación",
        "definition": "Sistema educativo chileno en todos sus niveles: básico, medio, superior y técnico-profesional; financiamiento, inclusión, calidad y regulación.",
        "keywords": [
            "educación", "escuela", "colegio", "liceo", "universidad", "establecimiento educacional",
            "estudiante", "alumno", "profesor", "docente", "director",
            "MINEDUC", "Mineduc", "beca", "crédito universitario", "gratuidad",
            "matrícula", "financiamiento educacional", "voucher educacional",
            "SIMCE", "PSU", "PDT", "admisión universitaria",
            "educación especial", "necesidades educativas especiales",
        ],
        "synonyms": ["sistema educativo", "instrucción", "formación académica"],
        "prototype_texts": [
            "Modifica la ley de educación para establecer nuevas normas de admisión escolar.",
            "Crea un sistema de becas para estudiantes de educación superior.",
            "Regula los establecimientos de educación técnico-profesional.",
        ],
        "subcategorias": {
            "EDUCACION_ESCOLAR": {
                "label": "Educación parvularia, básica y media",
                "definition": "Regulación de colegios, liceos, kínders, curriculum, admisión y funcionamiento de establecimientos de educación inicial, básica y media.",
                "keywords": [
                    "escuela", "colegio", "liceo", "kínder", "jardín infantil", "JUNJI",
                    "educación básica", "educación media", "educación parvularia",
                    "curriculum nacional", "plan de estudios", "jornada escolar",
                    "admisión escolar", "sistema de admisión", "SAE",
                    "sostenedor", "establecimiento educacional", "subvención escolar",
                    "matrícula", "rendimiento académico", "repitencia",
                ],
                "synonyms": ["educación preuniversitaria", "educación escolar", "colegio"],
                "etiquetas": ["colegios", "curriculum", "admision_escolar", "subvencion", "JUNJI"],
                "ejemplos_positivos": [
                    "Modifica la ley general de educación para regular el proceso de admisión escolar",
                    "Aumenta la subvención escolar para establecimientos que atienden alumnos vulnerables",
                ],
                "ejemplos_negativos": [
                    "Regula el sistema de crédito con garantía del Estado para educación superior",
                    "Establece requisitos para universidades privadas",
                ],
                "reglas_semanticas": [
                    r"educación\s+(básica|media|parvularia|escolar)",
                    r"(colegio|escuela|liceo|kínder|jardín\s+infantil)",
                    r"subvención\s+escolar",
                    r"plan\s+de\s+estudios|curriculum\s+nacional",
                    r"\bSAE\b|sistema\s+de\s+admisión\s+escolar",
                ],
            },
            "EDUCACION_SUPERIOR": {
                "label": "Educación superior",
                "definition": "Universidades, institutos profesionales, centros de formación técnica, acreditación, autonomía universitaria y regulación del sector.",
                "keywords": [
                    "universidad", "instituto profesional", "IP", "CFT", "centro de formación técnica",
                    "educación superior", "CRUCH", "CNA", "acreditación", "autonomía universitaria",
                    "rector", "aranceles", "matrícula universitaria",
                    "CNED", "SIES", "estadísticas universitarias",
                    "lucro en educación", "educación con fines de lucro",
                ],
                "synonyms": ["universidades", "estudios superiores"],
                "etiquetas": ["universidades", "acreditacion", "IP_CFT", "aranceles", "autonomia_universitaria"],
                "ejemplos_positivos": [
                    "Modifica la ley N°20.129 para fortalecer el sistema de acreditación universitaria",
                    "Regula los Institutos Profesionales y Centros de Formación Técnica",
                    "Establece requisitos mínimos para el funcionamiento de universidades privadas",
                ],
                "ejemplos_negativos": [
                    "Aumenta la subvención a colegios municipales",
                    "Crea beca para educación técnica",
                ],
                "reglas_semanticas": [
                    r"universidad(es)?|educación\s+superior",
                    r"(instituto\s+profesional|IP|CFT|centro\s+de\s+formación\s+técnica)",
                    r"\bCRUCH\b|\bCNA\b|\bCNED\b",
                    r"acreditación\s+(universitaria|institucional)",
                    r"lucro\s+en\s+educación|fines\s+de\s+lucro",
                ],
            },
            "FINANCIAMIENTO_EDUCACIONAL": {
                "label": "Financiamiento educacional",
                "definition": "Gratuidad en educación superior, becas, crédito con garantía del Estado (CAE), fondo solidario y financiamiento escolar.",
                "keywords": [
                    "gratuidad", "beca", "CAE", "crédito universitario", "fondo solidario",
                    "crédito con garantía del estado", "BAES", "becas JUNAEB",
                    "financiamiento educacional", "repactación del CAE",
                    "condonación de deudas", "deuda universitaria",
                    "beca indígena", "beca vocación de profesor",
                ],
                "synonyms": ["becas universitarias", "financiamiento estudiantil"],
                "etiquetas": ["gratuidad", "CAE", "becas", "deuda_universitaria", "financiamiento"],
                "ejemplos_positivos": [
                    "Amplía los beneficios de la gratuidad en educación superior",
                    "Crea un nuevo sistema de financiamiento estudiantil en reemplazo del CAE",
                    "Establece la condonación de deudas del crédito con garantía del Estado",
                ],
                "ejemplos_negativos": [
                    "Regula la acreditación de universidades",
                    "Modifica el curriculum de educación básica",
                ],
                "reglas_semanticas": [
                    r"\bCAE\b|crédito\s+(con\s+garantía|universitario|estudiantil)",
                    r"\bgratuidad\b",
                    r"beca(s)?\s+(JUNAEB|indígena|vocación|Bicentenario)?",
                    r"condonación\s+de\s+deudas?\s+universitaria",
                    r"financiamiento\s+(educacional|estudiantil)",
                ],
            },
            "INCLUSION_EDUCATIVA": {
                "label": "Inclusión y diversidad educativa",
                "definition": "Educación especial, necesidades educativas especiales, discapacidad, diversidad sexual, multiculturalismo e igualdad en el sistema escolar.",
                "keywords": [
                    "educación especial", "necesidades educativas especiales", "NEE",
                    "discapacidad", "inclusión educativa", "integración escolar",
                    "PIE", "programa de integración escolar",
                    "diversidad sexual", "educación no sexista",
                    "interculturalidad", "educación intercultural bilingüe",
                ],
                "synonyms": ["educación inclusiva", "diversidad en educación"],
                "etiquetas": ["educacion_especial", "NEE", "inclusion", "interculturalidad"],
                "ejemplos_positivos": [
                    "Modifica la ley de inclusión escolar para fortalecer los programas de integración",
                    "Crea un sistema de apoyo a estudiantes con necesidades educativas especiales",
                ],
                "ejemplos_negativos": [
                    "Crea el sistema de becas universitarias",
                    "Modifica el proceso de admisión a universidades",
                ],
                "reglas_semanticas": [
                    r"inclusión\s+(escolar|educativa)",
                    r"necesidades\s+educativas\s+especiales|NEE",
                    r"\bPIE\b|programa\s+de\s+integración\s+escolar",
                    r"educación\s+(intercultural|no\s+sexista|especial)",
                ],
            },
            "FORMACION_TECNICA": {
                "label": "Formación técnico-profesional y capacitación",
                "definition": "SENCE, franquicia tributaria, capacitación laboral, educación técnica y formación continua.",
                "keywords": [
                    "SENCE", "capacitación laboral", "formación profesional",
                    "educación técnico-profesional", "liceo técnico", "formación dual",
                    "franquicia tributaria", "curso de capacitación",
                    "certificación de competencias", "Chile Valora",
                    "reconversión laboral",
                ],
                "synonyms": ["capacitación", "formación para el trabajo", "educación técnica"],
                "etiquetas": ["SENCE", "capacitacion", "formacion_tecnica", "liceos_tecnicos"],
                "ejemplos_positivos": [
                    "Fortalece el sistema de formación dual en liceos técnico-profesionales",
                    "Amplía la franquicia tributaria para capacitación laboral de la PYME",
                ],
                "ejemplos_negativos": [
                    "Modifica la ley de acreditación universitaria",
                    "Crea beca para estudiantes de universidades públicas",
                ],
                "reglas_semanticas": [
                    r"\bSENCE\b",
                    r"capacitación\s+laboral|formación\s+(profesional|dual)",
                    r"liceo\s+técnico|educación\s+técnico[-\s]profesional",
                    r"franquicia\s+tributaria",
                ],
            },
        },
    },

    # ─────────────────────────────────────────────────────────────
    "MEDIO_AMBIENTE": {
        "label": "Medio Ambiente y Recursos Naturales",
        "definition": "Cambio climático, biodiversidad, recursos hídricos, minería, residuos y regulación ambiental.",
        "keywords": [
            "medio ambiente", "medioambiente", "ambiental", "ecología", "ecosistema",
            "cambio climático", "calentamiento global", "carbono", "emisiones",
            "biodiversidad", "flora", "fauna", "especie protegida",
            "agua", "río", "lago", "glaciar", "cuenca hidrográfica",
            "minería", "litio", "cobre", "oro", "CODELCO",
            "basura", "reciclaje", "plástico", "residuo", "contaminación",
            "CONAF", "SEREMI Medio Ambiente", "SEA", "SEIA",
        ],
        "synonyms": ["ecología", "recursos naturales", "sustentabilidad", "naturaleza"],
        "prototype_texts": [
            "Establece normas para la protección de glaciares y zonas periglaciales.",
            "Regula las emisiones de gases de efecto invernadero para alcanzar la carbono-neutralidad.",
            "Modifica la ley de bases del medio ambiente para fortalecer el SEIA.",
        ],
        "subcategorias": {
            "CAMBIO_CLIMATICO": {
                "label": "Cambio climático y transición energética",
                "definition": "Reducción de emisiones, economía circular, energías renovables, descarbonización y compromisos climáticos internacionales.",
                "keywords": [
                    "cambio climático", "calentamiento global", "gases de efecto invernadero",
                    "CO2", "dióxido de carbono", "carbono neutro", "carbono neutralidad",
                    "huella de carbono", "descarbonización", "impuesto al carbono",
                    "energía renovable", "energía solar", "energía eólica",
                    "economía circular", "NDC", "Acuerdo de París", "COP",
                    "electromovilidad", "vehículo eléctrico",
                ],
                "synonyms": ["crisis climática", "descarbonización", "carbono"],
                "etiquetas": ["cambio_climatico", "emisiones_CO2", "energias_renovables", "descarbonizacion"],
                "ejemplos_positivos": [
                    "Establece el marco de acción climática para alcanzar la carbono-neutralidad al 2050",
                    "Crea un impuesto a las emisiones de gases de efecto invernadero",
                    "Regula la transición energética hacia fuentes renovables no convencionales",
                ],
                "ejemplos_negativos": [
                    "Regula la extracción de agua en cuencas hidrográficas",
                    "Establece normas para la gestión de residuos sólidos",
                ],
                "reglas_semanticas": [
                    r"cambio\s+climático|calentamiento\s+global",
                    r"gases?\s+de\s+efecto\s+invernadero|\bCO2\b",
                    r"carbono\s+(neutro|neutralidad)|huella\s+de\s+carbono",
                    r"energía\s+(renovable|solar|eólica|limpia)",
                    r"Acuerdo\s+de\s+París|\bCOP\d+\b|\bNDC\b",
                ],
            },
            "BIODIVERSIDAD": {
                "label": "Biodiversidad y áreas silvestres protegidas",
                "definition": "Protección de flora y fauna nativa, parques nacionales, reservas naturales y servicios ecosistémicos.",
                "keywords": [
                    "biodiversidad", "especie protegida", "especie en peligro",
                    "flora nativa", "fauna silvestre", "humedal", "borde costero",
                    "parque nacional", "reserva natural", "área silvestre protegida",
                    "CONAF", "SAG", "Servicio de Biodiversidad",
                    "tráfico de fauna", "caza furtiva", "pesca ilegal",
                    "turba", "turbera",
                ],
                "synonyms": ["flora y fauna", "parques nacionales", "conservación"],
                "etiquetas": ["biodiversidad", "areas_protegidas", "CONAF", "fauna_silvestre"],
                "ejemplos_positivos": [
                    "Crea el Servicio de Biodiversidad y Áreas Silvestres Protegidas",
                    "Prohíbe la extracción de turba en humedales protegidos",
                ],
                "ejemplos_negativos": [
                    "Regula las emisiones de gases de efecto invernadero",
                    "Modifica el código de aguas",
                ],
                "reglas_semanticas": [
                    r"biodiversidad|especie(s)?\s+(protegida|en\s+peligro|amenazada)",
                    r"parque\s+nacional|área(s)?\s+silvestre(s)?\s+protegida(s)?",
                    r"\bCONAF\b|servicio\s+de\s+biodiversidad",
                    r"humedal|turbera|borde\s+costero",
                    r"flora\s+nativa|fauna\s+silvestre",
                ],
            },
            "RECURSOS_HIDRICOS": {
                "label": "Agua y recursos hídricos",
                "definition": "Código de Aguas, derechos de aprovechamiento, glaciares, cuencas hidrográficas y acceso al agua como derecho humano.",
                "keywords": [
                    "código de aguas", "derechos de aprovechamiento de aguas",
                    "agua potable", "agua subterránea", "acuífero", "napa",
                    "glaciar", "zona periglacial", "permafrost",
                    "cuenca hidrográfica", "río", "lago", "laguna", "embalse",
                    "DGA", "Dirección General de Aguas", "derechos de agua",
                    "escasez hídrica", "sequía", "derecho humano al agua",
                ],
                "synonyms": ["gestión del agua", "hídrico", "recursos hídricos"],
                "etiquetas": ["agua", "codigo_aguas", "glaciares", "DGA", "sequía"],
                "ejemplos_positivos": [
                    "Modifica el Código de Aguas para reconocer el agua como bien nacional de uso público",
                    "Establece la protección de glaciares y zonas periglaciales",
                    "Crea el sistema de pago por servicios ecosistémicos hídricos",
                ],
                "ejemplos_negativos": [
                    "Establece normas para la gestión de residuos sólidos domiciliarios",
                    "Regula la extracción de litio",
                ],
                "reglas_semanticas": [
                    r"código\s+de\s+aguas|derechos?\s+de\s+(aprovechamiento\s+de\s+)?aguas?",
                    r"glaciar|zona\s+periglacial",
                    r"\bDGA\b|dirección\s+general\s+de\s+aguas",
                    r"escasez\s+hídrica|sequía|cuenca\s+hidrográfica",
                    r"agua(s)?\s+(subterránea|potable|como\s+derecho)",
                ],
            },
            "MINERIA_EXTRACTIVAS": {
                "label": "Minería y recursos extractivos",
                "definition": "Regulación minera, concesiones, royalty, litio, cobre, CODELCO y extracción de recursos naturales.",
                "keywords": [
                    "minería", "concesión minera", "royalty minero", "impuesto minero",
                    "litio", "cobre", "oro", "plata", "hierro", "molibdeno",
                    "CODELCO", "empresa minera", "gran minería", "pequeña minería",
                    "Código de Minería", "SERNAGEOMIN", "faena minera",
                    "pasivo ambiental minero", "cierre de faena",
                ],
                "synonyms": ["industria extractiva", "recursos mineros", "royalty"],
                "etiquetas": ["mineria", "royalty", "litio", "CODELCO", "concesiones_mineras"],
                "ejemplos_positivos": [
                    "Establece un royalty minero sobre la explotación del cobre y el litio",
                    "Crea la empresa nacional del litio para la explotación estratégica del recurso",
                    "Modifica el Código de Minería para actualizar el régimen de concesiones",
                ],
                "ejemplos_negativos": [
                    "Modifica el Código de Aguas para proteger glaciares",
                    "Establece normas sobre residuos industriales",
                ],
                "reglas_semanticas": [
                    r"\bminería\b|concesión\s+minera|faena\s+minera",
                    r"royalty\s+minero|impuesto\s+minero",
                    r"\blitio\b|\bcobre\b|\bCODELCO\b",
                    r"código\s+de\s+minería|\bSERNAGEOMIN\b",
                ],
            },
            "CONTAMINACION_RESIDUOS": {
                "label": "Contaminación y gestión de residuos",
                "definition": "Residuos sólidos, reciclaje, plásticos, contaminación del aire, agua y suelo, y responsabilidad extendida del productor.",
                "keywords": [
                    "residuo", "basura", "reciclaje", "relleno sanitario",
                    "plástico", "microplástico", "bolsa plástica", "desechable",
                    "contaminación del aire", "norma de emisiones", "zona de sacrificio",
                    "REP", "responsabilidad extendida del productor",
                    "CONAMA", "MMA", "zona saturada de contaminación",
                ],
                "synonyms": ["basura", "desechos", "polución", "reciclaje"],
                "etiquetas": ["residuos", "reciclaje", "plasticos", "contaminacion_aire", "REP"],
                "ejemplos_positivos": [
                    "Establece la ley REP sobre responsabilidad extendida del productor de plásticos",
                    "Prohíbe la entrega gratuita de bolsas plásticas en el comercio",
                    "Declara zona saturada de contaminación atmosférica la ciudad de Quintero-Puchuncaví",
                ],
                "ejemplos_negativos": [
                    "Establece un royalty minero",
                    "Modifica el Código de Aguas",
                ],
                "reglas_semanticas": [
                    r"residuo(s)?|basura|desecho(s)?|relleno\s+sanitario",
                    r"reciclaje|reciclado|economía\s+circular",
                    r"plástico(s)?|microplástico|bolsa\s+plástica",
                    r"\bREP\b|responsabilidad\s+extendida\s+del\s+productor",
                    r"zona\s+(de\s+sacrificio|saturada|contaminad)",
                ],
            },
        },
    },

    # ─────────────────────────────────────────────────────────────
    "SEGURIDAD_JUSTICIA": {
        "label": "Seguridad Pública y Justicia",
        "definition": "Delitos, penas, sistema penal, crimen organizado, violencia, fuerzas de orden y sistema de justicia.",
        "keywords": [
            "delito", "crimen", "pena", "condena", "prisión", "cárcel", "reclusión",
            "Código Penal", "Código Procesal Penal", "Ministerio Público",
            "Defensoría Penal Pública", "fiscal", "imputado", "víctima",
            "narcotráfico", "droga", "SENDA", "lavado de activos",
            "violencia intrafamiliar", "VIF", "femicidio", "violencia de género",
            "Carabineros", "PDI", "Fuerzas Armadas", "Gendarmería",
        ],
        "synonyms": ["justicia penal", "sistema judicial", "orden público", "seguridad ciudadana"],
        "prototype_texts": [
            "Modifica el Código Penal para aumentar las penas por delitos de narcotráfico.",
            "Crea nuevas causales de detención y formalización en el proceso penal.",
            "Establece medidas de protección para víctimas de violencia intrafamiliar.",
        ],
        "subcategorias": {
            "DELITOS_PENAS": {
                "label": "Delitos y sanciones penales",
                "definition": "Tipificación de delitos, modificación de penas, agravantes, atenuantes y política criminal.",
                "keywords": [
                    "delito", "pena", "sanción penal", "tipificar", "Código Penal",
                    "reclusión", "presidio", "multa", "pena alternativa",
                    "delito de cuello blanco", "corrupción", "soborno",
                    "hurto", "robo", "estafa", "apropiación indebida",
                    "homicidio", "lesiones", "secuestro", "tráfico de personas",
                    "reincidencia", "agravante", "atenuante",
                ],
                "synonyms": ["derecho penal", "tipificación de delitos", "política criminal"],
                "etiquetas": ["Codigo_Penal", "delitos", "penas", "corrupcion", "tipificacion"],
                "ejemplos_positivos": [
                    "Agrava las penas para delitos cometidos contra menores de edad",
                    "Tipifica como delito la corrupción entre privados",
                    "Modifica el Código Penal para crear el delito de negacionismo",
                ],
                "ejemplos_negativos": [
                    "Crea el tribunal de familia para conocer causas de VIF",
                    "Regula el proceso de detención por carabineros",
                ],
                "reglas_semanticas": [
                    r"código\s+penal",
                    r"(pena|sanción)\s+(de\s+)?( presidio|reclusión|multa)?",
                    r"tipifica(r|ción)?\s+(como\s+)?delito",
                    r"(hurto|robo|estafa|homicidio|lesiones|secuestro)\s",
                    r"agravante|atenuante|reincidencia",
                ],
            },
            "PROCEDIMIENTO_PENAL": {
                "label": "Procedimiento penal y sistema judicial",
                "definition": "Código Procesal Penal, Ministerio Público, Defensoría, juicios orales, medidas cautelares, derechos del imputado.",
                "keywords": [
                    "Código Procesal Penal", "proceso penal", "juicio oral",
                    "Ministerio Público", "fiscal", "defensor", "Defensoría Penal",
                    "imputado", "formalización", "prisión preventiva",
                    "medida cautelar", "cautela de garantías",
                    "salida alternativa", "acuerdo reparatorio", "suspensión condicional",
                    "recurso de apelación", "casación", "nulidad procesal",
                ],
                "synonyms": ["justicia penal", "proceso criminal", "sistema acusatorio"],
                "etiquetas": ["CPP", "Ministerio_Publico", "proceso_penal", "prision_preventiva"],
                "ejemplos_positivos": [
                    "Modifica el Código Procesal Penal para agilizar los procedimientos de investigación",
                    "Amplía los plazos de prisión preventiva para delitos de alta connotación social",
                ],
                "ejemplos_negativos": [
                    "Aumenta las penas del Código Penal",
                    "Crea medidas de protección para víctimas de violencia intrafamiliar",
                ],
                "reglas_semanticas": [
                    r"código\s+procesal\s+penal",
                    r"(ministerio\s+público|defensoría\s+penal|fiscal(ía)?)",
                    r"prisión\s+preventiva|medida\s+cautelar",
                    r"juicio\s+oral|formalización\s+(de\s+)?la\s+investigación",
                    r"imputado|defensor\s+penal",
                ],
            },
            "CRIMEN_ORGANIZADO": {
                "label": "Crimen organizado y narcotráfico",
                "definition": "Narcotráfico, lavado de activos, tráfico de personas, asociación ilícita, terrorismo y crimen organizado.",
                "keywords": [
                    "narcotráfico", "tráfico de drogas", "drogas", "estupefacientes",
                    "lavado de activos", "lavado de dinero", "blanqueo",
                    "tráfico de personas", "trata de personas",
                    "asociación ilícita", "banda organizada", "crimen organizado",
                    "terrorismo", "financiamiento del terrorismo",
                    "arma de fuego", "porte de armas", "tráfico de armas",
                ],
                "synonyms": ["narco", "crimen organizado", "tráfico"],
                "etiquetas": ["narcotrafico", "lavado_activos", "trafico_personas", "terrorismo", "armas"],
                "ejemplos_positivos": [
                    "Fortalece las medidas contra el narcotráfico y lavado de activos",
                    "Aumenta las penas por tráfico de armas de fuego",
                    "Crea la Unidad Especializada Antilavado de Activos del Ministerio Público",
                ],
                "ejemplos_negativos": [
                    "Regula los procedimientos de detención policial",
                    "Establece medidas de protección para víctimas de VIF",
                ],
                "reglas_semanticas": [
                    r"narcotráfico|tráfico\s+de\s+drogas?",
                    r"lavado\s+de\s+(activos|dinero|bienes)|blanqueo",
                    r"tráfico\s+de\s+personas|trata\s+de\s+personas",
                    r"asociación\s+ilícita|banda\s+organizada|crimen\s+organizado",
                    r"terrorismo|financiamiento\s+del\s+terrorismo",
                    r"tráfico\s+de\s+armas|porte\s+ilegal\s+de\s+armas",
                ],
            },
            "VIOLENCIA_GENERO": {
                "label": "Violencia intrafamiliar y de género",
                "definition": "Femicidio, violencia doméstica, violencia intrafamiliar (VIF), abuso sexual, acoso, y protección de víctimas.",
                "keywords": [
                    "violencia intrafamiliar", "VIF", "violencia doméstica",
                    "femicidio", "feminicidio", "violencia de género", "ley Karin",
                    "acoso laboral", "acoso sexual", "abuso sexual", "violación",
                    "maltrato infantil", "maltrato de menores", "abuso en la infancia",
                    "medida de protección", "orden de alejamiento", "prohibición de acercamiento",
                    "víctima de violencia", "agresor",
                ],
                "synonyms": ["femicidio", "violencia doméstica", "abuso", "acoso"],
                "etiquetas": ["VIF", "femicidio", "violencia_genero", "acoso", "abuso_sexual"],
                "ejemplos_positivos": [
                    "Tipifica como femicidio el homicidio de una mujer por razones de género",
                    "Crea medidas cautelares urgentes para proteger a víctimas de violencia intrafamiliar",
                    "Regula el acoso laboral y sexual en el trabajo (ley Karin)",
                ],
                "ejemplos_negativos": [
                    "Aumenta las penas por narcotráfico",
                    "Modifica el Código Procesal Penal en materia de prisión preventiva",
                ],
                "reglas_semanticas": [
                    r"violencia\s+intrafamiliar|\bVIF\b",
                    r"femicidio|feminicidio",
                    r"violencia\s+(de\s+)?género",
                    r"acoso\s+(laboral|sexual)|abuso\s+sexual",
                    r"ley\s+Karin|maltrato\s+(infantil|menor)",
                ],
            },
            "ORDEN_SEGURIDAD": {
                "label": "Fuerzas de orden, seguridad y uso de la fuerza",
                "definition": "Carabineros, PDI, Fuerzas Armadas, Gendarmería, uso de la fuerza, protocolo policial y reforma policial.",
                "keywords": [
                    "Carabineros", "PDI", "policía", "Fuerzas Armadas",
                    "Gendarmería", "FFAA", "Ejército", "Armada", "Fuerza Aérea",
                    "uso de la fuerza", "detención", "allanamiento",
                    "protocolo policial", "reforma policial", "control de identidad",
                    "Estado de emergencia", "Estado de excepción",
                    "seguridad ciudadana", "delincuencia", "orden público",
                ],
                "synonyms": ["policía", "carabineros", "fuerzas de orden"],
                "etiquetas": ["Carabineros", "PDI", "FFAA", "uso_fuerza", "reforma_policial"],
                "ejemplos_positivos": [
                    "Regula el uso de la fuerza y los protocolos de detención de Carabineros",
                    "Establece una nueva institucionalidad para la PDI",
                    "Moderniza la Ley Orgánica Constitucional de Carabineros",
                ],
                "ejemplos_negativos": [
                    "Aumenta las penas por delitos violentos",
                    "Tipifica el femicidio como agravante",
                ],
                "reglas_semanticas": [
                    r"\bCarabineros\b|\bPDI\b|\bGendarmería\b",
                    r"fuerzas?\s+(armadas?|de\s+orden)",
                    r"uso\s+de\s+la\s+fuerza|protocolo\s+policial",
                    r"estado\s+de\s+(emergencia|excepción|sitio)",
                    r"control\s+de\s+identidad|detención\s+policial",
                ],
            },
        },
    },

    # ─────────────────────────────────────────────────────────────
    "ECONOMIA_FINANZAS": {
        "label": "Economía, Finanzas y Tributación",
        "definition": "Política fiscal, impuestos, sistema financiero, libre competencia, presupuesto público y regulación económica.",
        "keywords": [
            "impuesto", "tributación", "IVA", "renta", "SII", "TGR",
            "banco", "sistema financiero", "CMF", "crédito", "tasa de interés",
            "libre competencia", "TDLC", "FNE", "monopolio", "cartel",
            "PYME", "empresa", "emprendimiento", "pequeña empresa",
            "presupuesto", "ley de presupuesto", "deuda pública", "erario",
            "exportación", "importación", "arancel", "TLC",
        ],
        "synonyms": ["finanzas públicas", "política fiscal", "economía", "tributario"],
        "prototype_texts": [
            "Modifica la ley de impuesto a la renta para establecer nuevas tasas.",
            "Crea un sistema de crédito garantizado por el Estado para PyMEs.",
            "Establece nuevas normas de libre competencia para el mercado financiero.",
        ],
        "subcategorias": {
            "TRIBUTACION": {
                "label": "Tributación e impuestos",
                "definition": "Impuesto a la renta, IVA, tributación de empresas, evasión y elusión fiscal, SII y reforma tributaria.",
                "keywords": [
                    "impuesto a la renta", "renta", "tributación", "IVA",
                    "reforma tributaria", "impuesto corporativo", "pago de impuestos",
                    "evasión fiscal", "elusión tributaria", "planificación tributaria agresiva",
                    "SII", "Servicio de Impuestos Internos", "TGR", "Tesorería",
                    "declaración de renta", "devolución de impuestos", "crédito fiscal",
                    "impuesto al patrimonio", "impuesto a los súper ricos",
                ],
                "synonyms": ["reforma tributaria", "impuestos", "sistema tributario"],
                "etiquetas": ["impuestos", "IVA", "renta", "SII", "reforma_tributaria", "evasion"],
                "ejemplos_positivos": [
                    "Establece un impuesto al patrimonio para personas con activos superiores a 5 millones de dólares",
                    "Modifica el impuesto corporativo para financiar la reforma previsional",
                    "Fortalece las facultades del SII para combatir la evasión tributaria",
                ],
                "ejemplos_negativos": [
                    "Regula el sistema financiero y bancario",
                    "Establece el presupuesto de la nación para el año siguiente",
                ],
                "reglas_semanticas": [
                    r"impuesto\s+(a\s+la\s+renta|al\s+valor\s+agregado|IVA|al\s+patrimonio)",
                    r"reforma\s+tributaria|sistema\s+tributario",
                    r"\bSII\b|servicio\s+de\s+impuestos\s+internos",
                    r"evasión\s+(fiscal|tributaria)|elusión\s+tributaria",
                    r"tributación|carga\s+tributaria",
                ],
            },
            "SISTEMA_FINANCIERO": {
                "label": "Sistema financiero y bancario",
                "definition": "Regulación bancaria, CMF, tasas máximas convencionales, sobreendeudamiento, cooperativas de ahorro y crédito.",
                "keywords": [
                    "banco", "sistema bancario", "CMF", "Comisión para el Mercado Financiero",
                    "Banco Central", "tasa de interés", "tasa máxima convencional",
                    "crédito de consumo", "tarjeta de crédito", "deuda de consumo",
                    "sobreendeudamiento", "quiebra personal", "insolvencia",
                    "cooperativa de ahorro", "seguro", "mercado de valores", "bolsa",
                    "fintech", "criptomoneda", "bitcoin",
                ],
                "synonyms": ["banca", "sistema bancario", "mercado financiero"],
                "etiquetas": ["bancos", "CMF", "tasas_interes", "sobreendeudamiento", "fintech"],
                "ejemplos_positivos": [
                    "Modifica la tasa máxima convencional para proteger a los deudores de consumo",
                    "Regula las empresas fintech y los activos digitales en el mercado financiero",
                    "Crea un procedimiento simplificado de insolvencia para personas naturales",
                ],
                "ejemplos_negativos": [
                    "Establece reforma tributaria con nuevo impuesto corporativo",
                    "Regula la libre competencia en el mercado de telecomunicaciones",
                ],
                "reglas_semanticas": [
                    r"\bCMF\b|comisión\s+para\s+el\s+mercado\s+financiero",
                    r"banco(s)?\s+(central|comercial)|sistema\s+bancario",
                    r"tasa\s+(de\s+interés|máxima\s+convencional)",
                    r"sobreendeudamiento|quiebra\s+personal|insolvencia",
                    r"fintech|criptomoneda|activos?\s+digitales?",
                ],
            },
            "LIBRE_COMPETENCIA": {
                "label": "Libre competencia y regulación de mercados",
                "definition": "Defensa de la competencia, carteles, colusión, TDLC, FNE y regulación de monopolios.",
                "keywords": [
                    "libre competencia", "competencia desleal", "colusión", "cartel",
                    "TDLC", "Tribunal de Defensa de la Libre Competencia",
                    "FNE", "Fiscalía Nacional Económica",
                    "monopolio", "posición dominante", "fusión", "adquisición",
                    "concentración económica", "mercado relevante",
                    "delator compensado", "programa de clemencia",
                ],
                "synonyms": ["antimonopolio", "antitrust", "defensa de la competencia"],
                "etiquetas": ["libre_competencia", "colusión", "TDLC", "FNE", "monopolio"],
                "ejemplos_positivos": [
                    "Fortalece la investigación y persecución de carteles y aumenta su pena",
                    "Amplía las facultades de la FNE para investigar conductas anticompetitivas",
                ],
                "ejemplos_negativos": [
                    "Reforma el sistema tributario chileno",
                    "Regula el sistema de pensiones",
                ],
                "reglas_semanticas": [
                    r"libre\s+competencia|competencia\s+desleal",
                    r"colusión|cartel|monopolio|posición\s+dominante",
                    r"\bTDLC\b|\bFNE\b",
                    r"delator\s+compensado|programa\s+de\s+clemencia",
                ],
            },
            "PYMES_EMPRENDIMIENTO": {
                "label": "PyMEs, emprendimiento e inversión",
                "definition": "Pequeñas y medianas empresas, simplificación de trámites, Start-Up Chile, CORFO y fomento productivo.",
                "keywords": [
                    "PYME", "pequeña empresa", "mediana empresa", "microempresa",
                    "emprendimiento", "emprendedor", "StartUp Chile", "CORFO",
                    "fomento productivo", "capital de riesgo", "subsidio empresarial",
                    "simplificación tributaria", "trámite empresa",
                    "quiebra PYME", "reorganización empresarial",
                    "franquicia tributaria", "IVA exportador",
                ],
                "synonyms": ["pequeñas empresas", "emprendedores", "mipymes"],
                "etiquetas": ["PYME", "CORFO", "emprendimiento", "startup", "fomento_productivo"],
                "ejemplos_positivos": [
                    "Crea un régimen tributario simplificado para pequeñas y medianas empresas",
                    "Amplía los fondos CORFO para capital de riesgo de startups",
                ],
                "ejemplos_negativos": [
                    "Reforma el sistema tributario para grandes empresas",
                    "Regula la libre competencia en el mercado",
                ],
                "reglas_semanticas": [
                    r"\bPYME|\bPyme|pequeña(s)?\s+(y\s+mediana(s)?)?\s+empresa(s)?",
                    r"\bCORFO\b|fomento\s+productivo",
                    r"emprendimiento|emprendedor|startup",
                    r"capital\s+de\s+riesgo|inversión\s+(extranjera|nacional)",
                ],
            },
            "PRESUPUESTO_FISCAL": {
                "label": "Presupuesto fiscal y gasto público",
                "definition": "Ley de presupuesto, deuda pública, regla fiscal, transferencias, bonos fiscales y política fiscal contracíclica.",
                "keywords": [
                    "presupuesto", "ley de presupuesto", "gasto público",
                    "deuda pública", "déficit fiscal", "superávit",
                    "regla fiscal", "balance estructural", "FEES", "FONDO SOBERANO",
                    "transferencias corrientes", "bono", "IFE", "ingreso familiar de emergencia",
                    "Dipres", "DIPRES", "política fiscal",
                ],
                "synonyms": ["presupuesto nacional", "finanzas públicas", "política fiscal"],
                "etiquetas": ["presupuesto", "gasto_publico", "deuda_publica", "IFE", "DIPRES"],
                "ejemplos_positivos": [
                    "Aprueba la ley de presupuesto del sector público para el ejercicio siguiente",
                    "Crea el Ingreso Familiar de Emergencia para familias vulnerables",
                    "Establece un bono de invierno permanente para jubilados de bajos recursos",
                ],
                "ejemplos_negativos": [
                    "Reforma el sistema tributario",
                    "Regula el sistema financiero y bancario",
                ],
                "reglas_semanticas": [
                    r"ley\s+de\s+presupuesto|presupuesto\s+del\s+(sector\s+)?público",
                    r"gasto\s+público|déficit\s+fiscal",
                    r"\bIFE\b|ingreso\s+familiar\s+de\s+emergencia",
                    r"\bDIPRES\b|regla\s+fiscal",
                    r"bono\s+(de\s+invierno|covid|marzo|clase\s+media)?",
                ],
            },
        },
    },

    # ─────────────────────────────────────────────────────────────
    "DERECHOS_FUNDAMENTALES": {
        "label": "Derechos Fundamentales y Constitucionales",
        "definition": "Derechos humanos, igualdad, no discriminación, derechos de infancia, pueblos indígenas, derechos de la mujer y libertades civiles.",
        "keywords": [
            "derechos fundamentales", "derechos humanos", "derechos constitucionales",
            "igualdad", "no discriminación", "discriminación arbitraria",
            "pueblo indígena", "Mapuche", "CONADI", "tierra indígena",
            "género", "igualdad de género", "paridad", "mujer",
            "niño", "niña", "infancia", "adolescente", "SENAME",
            "libertad de expresión", "libertad de prensa", "religión",
        ],
        "synonyms": ["derechos civiles", "libertades fundamentales", "garantías constitucionales"],
        "prototype_texts": [
            "Modifica la Constitución para garantizar la igualdad ante la ley sin discriminación.",
            "Crea un sistema de protección integral de los derechos de la infancia.",
            "Reconoce los derechos territoriales de los pueblos originarios.",
        ],
        "subcategorias": {
            "IGUALDAD_NO_DISCRIMINACION": {
                "label": "Igualdad y no discriminación",
                "definition": "Ley Zamudio, discriminación por raza, género, orientación sexual, discapacidad, edad y otras categorías protegidas.",
                "keywords": [
                    "discriminación", "ley Zamudio", "ley antidiscriminación",
                    "orientación sexual", "identidad de género", "LGBTQ+",
                    "matrimonio igualitario", "acuerdo de unión civil", "AUC",
                    "discapacidad", "inclusión", "igualdad de trato",
                    "racismo", "xenofobia", "discriminación laboral",
                ],
                "synonyms": ["antidiscriminación", "igualdad de trato"],
                "etiquetas": ["discriminacion", "LGBTQ", "matrimonio_igualitario", "discapacidad", "ley_Zamudio"],
                "ejemplos_positivos": [
                    "Modifica la ley antidiscriminación para incluir la identidad de género",
                    "Crea el matrimonio igualitario para parejas del mismo sexo",
                    "Establece cuotas de inclusión laboral para personas con discapacidad",
                ],
                "ejemplos_negativos": [
                    "Regula la adopción de menores por parte de parejas",
                    "Establece derechos territoriales para pueblos indígenas",
                ],
                "reglas_semanticas": [
                    r"ley\s+Zamudio|ley\s+antidiscriminación",
                    r"discriminación\s+(arbitraria|por\s+género|racial|laboral)",
                    r"matrimonio\s+igualitario|AUC|acuerdo\s+de\s+unión\s+civil",
                    r"LGBTQ?|orientación\s+sexual|identidad\s+de\s+género",
                    r"discapacidad|inclusión\s+(laboral|social)",
                ],
            },
            "DERECHOS_INFANCIA": {
                "label": "Derechos de la infancia y adolescencia",
                "definition": "Protección de menores, SENAME, adopción, responsabilidad penal adolescente, maltrato y trabajo infantil.",
                "keywords": [
                    "niño", "niña", "infancia", "adolescente", "menor de edad",
                    "SENAME", "Servicio Nacional de Menores", "Mejor Niñez",
                    "adopción", "sistema de adopción", "tutela", "curaduría",
                    "responsabilidad penal adolescente", "LRPA",
                    "maltrato infantil", "explotación infantil",
                    "pensión de alimentos", "alimentos",
                ],
                "synonyms": ["protección de menores", "niñez", "infancia"],
                "etiquetas": ["SENAME", "infancia", "adopcion", "pension_alimentos", "menores"],
                "ejemplos_positivos": [
                    "Crea el Servicio Nacional de Protección Especializada de la Niñez en reemplazo del SENAME",
                    "Modifica la ley de adopción para fortalecer el sistema de protección",
                    "Establece sanciones para el no pago de pensiones de alimentos",
                ],
                "ejemplos_negativos": [
                    "Establece la paridad de género en cargos públicos",
                    "Crea el matrimonio igualitario",
                ],
                "reglas_semanticas": [
                    r"\bSENAME\b|servicio\s+nacional\s+de\s+(menores|protección)",
                    r"\badopción\b",
                    r"pensión\s+de\s+alimentos|alimentos\s+(de\s+menores)?",
                    r"(infancia|niñez|menor(es)?\s+de\s+edad)",
                    r"responsabilidad\s+penal\s+adolescente|\bLRPA\b",
                ],
            },
            "DERECHOS_MUJER_GENERO": {
                "label": "Derechos de la mujer e igualdad de género",
                "definition": "Paridad de género, aborto, brecha salarial, licencia de maternidad y paternidad, SERNAM y violencia de género.",
                "keywords": [
                    "mujer", "género", "igualdad de género", "paridad de género",
                    "SERNAM", "SERNAMEG", "Ministerio de la Mujer",
                    "aborto", "interrupción del embarazo", "IVE", "tres causales",
                    "maternidad", "licencia maternal", "fuero maternal",
                    "brecha salarial", "igual salario", "salario igual",
                    "cuotas de género", "paridad en listas",
                ],
                "synonyms": ["feminismo", "igualdad de género", "derechos de la mujer"],
                "etiquetas": ["genero", "paridad", "aborto", "SERNAMEG", "brecha_salarial"],
                "ejemplos_positivos": [
                    "Establece la paridad de género en el sistema electoral y cargos públicos",
                    "Amplía las causales del aborto no punible más allá de las tres causales",
                    "Crea la ley de igualdad salarial entre hombres y mujeres",
                ],
                "ejemplos_negativos": [
                    "Modifica el sistema de adopción de menores",
                    "Crea medidas de protección para víctimas de VIF",
                ],
                "reglas_semanticas": [
                    r"paridad\s+(de\s+)?género|igualdad\s+(de\s+)?género",
                    r"\baborto\b|interrupción\s+(voluntaria\s+)?del\s+embarazo|\bIVE\b",
                    r"\bSERNAMEG?\b|ministerio\s+de\s+la\s+mujer",
                    r"brecha\s+salarial|igual\s+salario|salario\s+igual",
                    r"licencia\s+(maternal|de\s+maternidad|de\s+paternidad)",
                ],
            },
            "PUEBLOS_INDIGENAS": {
                "label": "Pueblos indígenas y etnias",
                "definition": "Derechos territoriales Mapuche, CONADI, consulta indígena, Convenio 169 OIT, plurinacionalidad y reconocimiento constitucional.",
                "keywords": [
                    "pueblo indígena", "Mapuche", "Aymara", "Rapa Nui", "Atacameño",
                    "tierra indígena", "territorio indígena", "CONADI",
                    "Convenio 169 OIT", "consulta indígena", "consulta previa",
                    "autonomía indígena", "reconocimiento constitucional",
                    "plurinacionalidad", "interculturalidad",
                    "Wallmapu", "conflicto mapuche",
                ],
                "synonyms": ["pueblos originarios", "comunidades indígenas", "etnias chilenas"],
                "etiquetas": ["indigenas", "Mapuche", "CONADI", "consulta_indigena", "tierras_indigenas"],
                "ejemplos_positivos": [
                    "Modifica la ley indígena para fortalecer los mecanismos de consulta previa",
                    "Crea el Ministerio de Asuntos Indígenas y reforma la CONADI",
                    "Establece el reconocimiento constitucional de los pueblos originarios",
                ],
                "ejemplos_negativos": [
                    "Regula la igualdad de género en el sector público",
                    "Crea el matrimonio igualitario en Chile",
                ],
                "reglas_semanticas": [
                    r"pueblo(s)?\s+indígena(s)?|pueblo(s)?\s+originario(s)?",
                    r"\bMapuche\b|\bAymara\b|\bRapa\s+Nui\b",
                    r"\bCONADI\b|tierra(s)?\s+indígena(s)?",
                    r"convenio\s+169|consulta\s+(indígena|previa)",
                    r"plurinacionalidad|reconocimiento\s+constitucional",
                ],
            },
            "LIBERTADES_CIVILES": {
                "label": "Libertades civiles y derechos políticos",
                "definition": "Libertad de expresión, libertad de prensa, libertad religiosa, reunión, asociación y derechos políticos.",
                "keywords": [
                    "libertad de expresión", "libertad de prensa", "censura",
                    "libertad religiosa", "laicidad del Estado",
                    "derecho de reunión", "manifestación pública", "marcha",
                    "libertad de asociación", "partido político",
                    "privacidad", "datos personales", "hábeas corpus",
                    "recurso de amparo", "recurso de protección",
                ],
                "synonyms": ["libertades individuales", "derechos civiles", "garantías individuales"],
                "etiquetas": ["libertad_expresion", "libertad_prensa", "privacidad", "amparo"],
                "ejemplos_positivos": [
                    "Modifica la ley sobre libertades de opinión e información para proteger el periodismo",
                    "Regula el ejercicio del derecho de manifestación y reunión en espacios públicos",
                ],
                "ejemplos_negativos": [
                    "Establece el reconocimiento constitucional de los pueblos indígenas",
                    "Crea la ley de igualdad salarial",
                ],
                "reglas_semanticas": [
                    r"libertad\s+de\s+(expresión|prensa|información|reunión|asociación)",
                    r"censura|derecho\s+a\s+la\s+información",
                    r"recurso\s+de\s+(amparo|protección)|hábeas\s+corpus",
                    r"privacidad|datos\s+personales",
                    r"laicidad|libertad\s+religiosa",
                ],
            },
        },
    },

    # ─────────────────────────────────────────────────────────────
    "VIVIENDA_URBANISMO": {
        "label": "Vivienda y Urbanismo",
        "definition": "Acceso a la vivienda, política habitacional, planificación territorial, arriendos y servicios básicos.",
        "keywords": [
            "vivienda", "casa", "departamento", "habitación", "hogar",
            "subsidio habitacional", "SERVIU", "MINVU", "campamento",
            "arriendo", "arrendatario", "arrendador", "desalojo",
            "plan regulador", "uso de suelo", "urbanismo", "ciudad",
            "agua potable", "alcantarillado", "electricidad", "gas",
        ],
        "synonyms": ["política habitacional", "hábitat", "urbanismo", "planificación territorial"],
        "prototype_texts": [
            "Modifica la ley de urbanismo para regular el uso de suelo en zonas costeras.",
            "Crea un subsidio habitacional para familias en situación de campamento.",
            "Regula el contrato de arriendo y las condiciones para el desalojo de arrendatarios.",
        ],
        "subcategorias": {
            "ACCESO_VIVIENDA": {
                "label": "Acceso a la vivienda y política habitacional",
                "definition": "Subsidios habitacionales, SERVIU, campamentos, allegados y programas de vivienda para sectores vulnerables.",
                "keywords": [
                    "subsidio habitacional", "subsidio de vivienda", "SERVIU",
                    "MINVU", "campamento", "allegados", "toma de terreno",
                    "vivienda social", "vivienda de emergencia", "casa propia",
                    "DS19", "DS49", "DS1", "fondo solidario de vivienda",
                    "programa habitacional", "política habitacional",
                ],
                "synonyms": ["subsidio vivienda", "vivienda social", "política habitacional"],
                "etiquetas": ["subsidio_habitacional", "SERVIU", "campamentos", "vivienda_social"],
                "ejemplos_positivos": [
                    "Crea un programa de erradicación de campamentos con subsidios habitacionales",
                    "Aumenta el monto del subsidio habitacional para familias vulnerables",
                    "Modifica la ley del MINVU para agilizar la construcción de viviendas sociales",
                ],
                "ejemplos_negativos": [
                    "Regula el contrato de arriendo entre privados",
                    "Modifica el plan regulador comunal",
                ],
                "reglas_semanticas": [
                    r"subsidio\s+(habitacional|de\s+vivienda)",
                    r"\bSERVIU\b|\bMINVU\b",
                    r"campamento(s)?|allegado(s)?|toma\s+de\s+terreno",
                    r"vivienda\s+(social|de\s+emergencia|popular)",
                    r"fondo\s+solidario\s+de\s+vivienda",
                ],
            },
            "ARRIENDO_PROPIEDAD": {
                "label": "Arriendo, propiedad y copropiedad",
                "definition": "Contratos de arriendo, ley del arrendatario, desalojo, copropiedad inmobiliaria y propiedad horizontal.",
                "keywords": [
                    "arriendo", "arrendamiento", "arrendatario", "arrendador",
                    "contrato de arriendo", "desalojo", "lanzamiento", "morosidad",
                    "copropiedad inmobiliaria", "propiedad horizontal", "condominio",
                    "administración de condominios", "gastos comunes",
                    "alzamiento de hipoteca", "bienes raíces", "propiedad raíz",
                ],
                "synonyms": ["arrendatarios", "alquiler", "copropiedad"],
                "etiquetas": ["arriendo", "desalojo", "copropiedad", "arrendatarios"],
                "ejemplos_positivos": [
                    "Modifica la ley de arriendo para proteger a los arrendatarios durante emergencias",
                    "Actualiza la ley de copropiedad inmobiliaria para regular los condominios",
                    "Establece un procedimiento especial de desalojo por no pago de arriendo",
                ],
                "ejemplos_negativos": [
                    "Crea subsidios habitacionales para familias vulnerables",
                    "Modifica el plan regulador comunal",
                ],
                "reglas_semanticas": [
                    r"(contrato\s+de\s+)?arriendo|arrendamiento",
                    r"arrendatario|arrendador|locatario",
                    r"desalojo|lanzamiento",
                    r"copropiedad\s+inmobiliaria|propiedad\s+horizontal|condominio",
                ],
            },
            "PLANIFICACION_TERRITORIAL": {
                "label": "Planificación urbana y territorial",
                "definition": "Plan regulador, uso de suelo, urbanización, densificación, OGUC y ordenamiento territorial.",
                "keywords": [
                    "plan regulador", "uso de suelo", "zonificación", "OGUC",
                    "urbanización", "loteo", "subdivisión", "densificación",
                    "permiso de edificación", "recepción municipal",
                    "MINVU", "SEREMI de Vivienda", "DOM",
                    "área verde", "espacio público",
                    "límite urbano", "área rural", "borde costero",
                ],
                "synonyms": ["urbanismo", "ordenamiento territorial", "planificación urbana"],
                "etiquetas": ["plan_regulador", "urbanismo", "OGUC", "densificacion", "ordenamiento"],
                "ejemplos_positivos": [
                    "Modifica la Ley General de Urbanismo y Construcciones para agilizar permisos de edificación",
                    "Establece nuevas normas de densificación en zonas urbanas con transporte público",
                ],
                "ejemplos_negativos": [
                    "Crea subsidios habitacionales para erradicación de campamentos",
                    "Modifica la ley de arriendo",
                ],
                "reglas_semanticas": [
                    r"plan\s+regulador|uso\s+de\s+suelo|zonificación",
                    r"\bOGUC\b|ley\s+general\s+de\s+urbanismo",
                    r"densificación|urbanización",
                    r"permiso\s+de\s+(edificación|construcción)",
                ],
            },
            "SERVICIOS_BASICOS": {
                "label": "Servicios básicos y concesiones",
                "definition": "Agua potable, alcantarillado, electricidad, gas, telecomunicaciones básicas y regulación de concesionarias.",
                "keywords": [
                    "agua potable", "alcantarillado", "empresa de agua", "SISS",
                    "electricidad", "empresa eléctrica", "tarifa eléctrica", "CNE",
                    "corte de suministro", "corte de luz", "corte de agua",
                    "gas", "gaseoducto", "concesionaria", "tarifa",
                    "acceso a servicios básicos", "pobreza energética",
                ],
                "synonyms": ["utilidades", "servicios públicos", "concesiones"],
                "etiquetas": ["agua_potable", "electricidad", "servicios_basicos", "tarifas"],
                "ejemplos_positivos": [
                    "Prohíbe el corte de agua potable y luz a familias vulnerables",
                    "Regula las tarifas de electricidad para usuarios residenciales",
                ],
                "ejemplos_negativos": [
                    "Modifica la ley de arriendo",
                    "Crea el subsidio habitacional",
                ],
                "reglas_semanticas": [
                    r"agua\s+potable|alcantarillado|\bSISS\b",
                    r"tarifa\s+(eléctrica|de\s+agua|de\s+gas)|\bCNE\b",
                    r"corte\s+de\s+(suministro|luz|agua|gas)",
                    r"pobreza\s+energética|concesionaria",
                ],
            },
        },
    },

    # ─────────────────────────────────────────────────────────────
    "TECNOLOGIA_INNOVACION": {
        "label": "Tecnología, Innovación y Datos",
        "definition": "Protección de datos personales, delitos informáticos, telecomunicaciones, innovación y regulación de tecnologías emergentes.",
        "keywords": [
            "datos personales", "privacidad", "protección de datos",
            "ciberseguridad", "delito informático", "hackeo", "phishing",
            "internet", "telecomunicaciones", "5G", "fibra óptica",
            "innovación", "I+D", "investigación y desarrollo",
            "inteligencia artificial", "IA", "automatización",
            "criptomoneda", "blockchain", "activos digitales",
        ],
        "synonyms": ["digital", "tecnológico", "datos", "innovación"],
        "prototype_texts": [
            "Modifica la ley de protección de datos personales para adecuarla al GDPR.",
            "Tipifica nuevos delitos informáticos y regula la ciberseguridad nacional.",
            "Regula el uso de inteligencia artificial en el sector público.",
        ],
        "subcategorias": {
            "DATOS_PERSONALES": {
                "label": "Protección de datos personales y privacidad",
                "definition": "Regulación del tratamiento de datos personales, derechos ARCO, privacidad digital y adecuación normativa.",
                "keywords": [
                    "datos personales", "protección de datos", "ley de datos personales",
                    "privacidad", "privacidad digital", "datos sensibles",
                    "tratamiento de datos", "derechos ARCO", "acceso", "rectificación",
                    "cancelación", "oposición", "consentimiento informado",
                    "GDPR", "RGPD", "Agencia de Protección de Datos",
                    "transferencia internacional de datos",
                ],
                "synonyms": ["privacidad de datos", "GDPR chileno", "datos sensibles"],
                "etiquetas": ["datos_personales", "privacidad", "GDPR", "derechos_ARCO"],
                "ejemplos_positivos": [
                    "Actualiza la ley N°19.628 sobre protección de datos personales",
                    "Crea la Agencia de Protección de Datos Personales",
                    "Regula el tratamiento de datos biométricos y datos sensibles",
                ],
                "ejemplos_negativos": [
                    "Tipifica delitos informáticos",
                    "Regula el uso de inteligencia artificial",
                ],
                "reglas_semanticas": [
                    r"datos\s+personales|protección\s+de\s+datos",
                    r"\bGDPR\b|\bRGPD\b|ley\s+de\s+datos\s+personales",
                    r"derechos?\s+ARCO|consentimiento\s+informado",
                    r"agencia\s+de\s+protección\s+de\s+datos",
                    r"datos\s+sensibles|biométrico(s)?",
                ],
            },
            "CIBERSEGURIDAD": {
                "label": "Ciberseguridad y delitos informáticos",
                "definition": "Delitos computacionales, ransomware, sabotaje informático, marco nacional de ciberseguridad y protección de infraestructura crítica.",
                "keywords": [
                    "ciberseguridad", "delito informático", "computacional",
                    "hackeo", "hacking", "ransomware", "malware", "phishing",
                    "sabotaje informático", "infraestructura crítica",
                    "CSIRT", "Agencia Nacional de Ciberseguridad",
                    "ley de delitos informáticos",
                    "acceso no autorizado", "interceptación ilegal",
                ],
                "synonyms": ["seguridad informática", "cibercrimen", "delitos computacionales"],
                "etiquetas": ["ciberseguridad", "delitos_informaticos", "CSIRT", "infraestructura_critica"],
                "ejemplos_positivos": [
                    "Crea el marco regulatorio de ciberseguridad y la Agencia Nacional de Ciberseguridad",
                    "Actualiza la ley de delitos informáticos para incluir ransomware y ataques de phishing",
                ],
                "ejemplos_negativos": [
                    "Regula la protección de datos personales",
                    "Establece el uso de IA en el sector público",
                ],
                "reglas_semanticas": [
                    r"ciberseguridad|seguridad\s+(informática|digital|cibernética)",
                    r"delito\s+informático|computacional",
                    r"ransomware|malware|phishing|hackeo",
                    r"\bCSIRT\b|agencia\s+(nacional\s+de\s+)?ciberseguridad",
                    r"infraestructura\s+crítica",
                ],
            },
            "TELECOMUNICACIONES": {
                "label": "Telecomunicaciones e infraestructura digital",
                "definition": "Internet, 5G, fibra óptica, radiodifusión, SUBTEL, espectro radioeléctrico y conectividad.",
                "keywords": [
                    "telecomunicaciones", "internet", "banda ancha", "fibra óptica",
                    "5G", "4G", "espectro radioeléctrico", "SUBTEL",
                    "operador de telecomunicaciones", "Movistar", "Entel", "Claro",
                    "neutralidad de la red", "acceso a internet",
                    "televisión digital", "TDT", "radiodifusión",
                    "brecha digital", "conectividad rural",
                ],
                "synonyms": ["telecomunicaciones", "conectividad", "espectro"],
                "etiquetas": ["telecomunicaciones", "internet", "5G", "SUBTEL", "brecha_digital"],
                "ejemplos_positivos": [
                    "Modifica la ley de telecomunicaciones para licitar el espectro de 5G",
                    "Crea un programa de conectividad rural para reducir la brecha digital",
                    "Establece la neutralidad de la red como principio obligatorio",
                ],
                "ejemplos_negativos": [
                    "Regula la ciberseguridad nacional",
                    "Crea la ley de datos personales",
                ],
                "reglas_semanticas": [
                    r"telecomunicaciones|\bSUBTEL\b",
                    r"\b5G\b|fibra\s+óptica|banda\s+ancha",
                    r"espectro\s+radioeléctrico|conectividad\s+(rural|digital)",
                    r"neutralidad\s+de\s+(la\s+)?red",
                ],
            },
            "IA_AUTOMATIZACION": {
                "label": "Inteligencia artificial y automatización",
                "definition": "Regulación de IA, sistemas algorítmicos, automatización del trabajo, derechos en la era digital.",
                "keywords": [
                    "inteligencia artificial", "IA", "machine learning",
                    "sistema algorítmico", "algoritmo", "automatización",
                    "robot", "automatización del trabajo",
                    "deepfake", "desinformación digital",
                    "ética de la IA", "sesgo algorítmico",
                    "regulación de IA",
                ],
                "synonyms": ["IA", "algoritmos", "automatización", "machine learning"],
                "etiquetas": ["inteligencia_artificial", "automatizacion", "algoritmos", "regulacion_IA"],
                "ejemplos_positivos": [
                    "Establece un marco regulatorio para el uso de inteligencia artificial en el sector público",
                    "Prohíbe el uso de sistemas de reconocimiento facial sin autorización judicial",
                    "Crea un registro de sistemas de IA de alto riesgo",
                ],
                "ejemplos_negativos": [
                    "Regula la protección de datos personales",
                    "Modifica la ley de telecomunicaciones",
                ],
                "reglas_semanticas": [
                    r"inteligencia\s+artificial|\bIA\b|machine\s+learning",
                    r"sistema(s)?\s+algorítmico(s)?|algoritmo(s)?",
                    r"automatización\s+(del\s+)?trabajo|robot(ización)?",
                    r"deepfake|reconocimiento\s+facial",
                ],
            },
        },
    },

    # ─────────────────────────────────────────────────────────────
    "INSTITUCIONALIDAD_ESTADO": {
        "label": "Institucionalidad y Administración del Estado",
        "definition": "Reforma constitucional, descentralización, transparencia, sistema electoral, función pública y estructura del Estado.",
        "keywords": [
            "constitución", "reforma constitucional", "nueva constitución",
            "plebiscito", "convención constitucional",
            "municipio", "alcalde", "gobernador regional", "descentralización",
            "transparencia", "probidad", "lobby", "declaración de intereses",
            "elecciones", "Servel", "partido político",
            "función pública", "empleado público", "contrata",
        ],
        "synonyms": ["reforma del Estado", "instituciones", "democracia", "gobernanza"],
        "prototype_texts": [
            "Convoca a un plebiscito para el proceso de nueva constitución.",
            "Reforma el sistema electoral para incorporar el voto de los chilenos en el extranjero.",
            "Establece nuevas normas de transparencia y acceso a la información pública.",
        ],
        "subcategorias": {
            "REFORMA_CONSTITUCIONAL": {
                "label": "Reforma constitucional y proceso constituyente",
                "definition": "Nueva Constitución, plebiscito, convención constitucional, reforma a la Carta Magna y proceso constituyente.",
                "keywords": [
                    "constitución", "nueva constitución", "reforma constitucional",
                    "plebiscito", "convención constitucional", "asamblea constituyente",
                    "carta fundamental", "carta magna",
                    "apruebo", "rechazo", "proceso constituyente",
                    "artículo constitucional", "ley orgánica constitucional",
                ],
                "synonyms": ["proceso constituyente", "nueva carta magna", "reforma constitucional"],
                "etiquetas": ["constitucion", "plebiscito", "convencion_constitucional", "reforma_constitucional"],
                "ejemplos_positivos": [
                    "Convoca a plebiscito para iniciar el proceso de nueva constitución",
                    "Establece el mecanismo de reforma constitucional mediante convención mixta",
                    "Modifica la Constitución Política de la República para reconocer nuevos derechos",
                ],
                "ejemplos_negativos": [
                    "Reforma el sistema electoral para elecciones parlamentarias",
                    "Modifica la ley orgánica de municipalidades",
                ],
                "reglas_semanticas": [
                    r"(nueva\s+)?constitución|reforma\s+constitucional",
                    r"plebiscito|convención\s+constitucional|asamblea\s+constituyente",
                    r"carta\s+(fundamental|magna)",
                    r"ley\s+orgánica\s+constitucional",
                ],
            },
            "DESCENTRALIZACION": {
                "label": "Descentralización y gobiernos regionales y locales",
                "definition": "Municipios, alcaldes, gobernadores regionales, traspaso de competencias y autonomía regional.",
                "keywords": [
                    "municipio", "municipalidad", "alcalde", "concejo municipal",
                    "gobernador regional", "gobierno regional", "GORE",
                    "descentralización", "traspaso de competencias",
                    "autonomía regional", "desarrollo regional",
                    "ley orgánica de municipalidades", "Subdere",
                    "Fondo Común Municipal", "FCM",
                ],
                "synonyms": ["municipalidades", "gobierno local", "región", "descentralización"],
                "etiquetas": ["municipios", "gobernadores", "descentralizacion", "GORE"],
                "ejemplos_positivos": [
                    "Traspasa competencias desde el nivel central a los Gobiernos Regionales",
                    "Modifica la ley orgánica de municipalidades para ampliar sus atribuciones",
                    "Crea el sistema de traspaso de servicios al GORE",
                ],
                "ejemplos_negativos": [
                    "Establece la nueva Constitución del país",
                    "Modifica el sistema electoral y los partidos políticos",
                ],
                "reglas_semanticas": [
                    r"municipio|municipalidad|alcalde",
                    r"gobernador\s+regional|\bGORE\b",
                    r"descentralización|traspaso\s+de\s+competencias",
                    r"Fondo\s+Común\s+Municipal|\bFCM\b|\bSubdere\b",
                ],
            },
            "TRANSPARENCIA_PROBIDAD": {
                "label": "Transparencia, probidad y anticorrupción",
                "definition": "Ley de transparencia, lobby, declaración de patrimonio, conflicto de interés y control del tráfico de influencias.",
                "keywords": [
                    "transparencia", "probidad", "lobby", "gestor de intereses",
                    "declaración de patrimonio", "declaración de intereses",
                    "conflicto de interés", "inhabilidad", "incompatibilidad",
                    "Consejo para la Transparencia", "CPLT",
                    "acceso a la información pública", "ley de lobby",
                    "puerta giratoria", "financiamiento político",
                    "corrupción pública", "cohecho", "soborno",
                ],
                "synonyms": ["anticorrupción", "acceso a la información", "probidad pública"],
                "etiquetas": ["transparencia", "lobby", "probidad", "anticorrupcion", "CPLT"],
                "ejemplos_positivos": [
                    "Fortalece la ley de lobby para transparentar la gestión de intereses ante funcionarios",
                    "Crea la obligación de declaración patrimonial para autoridades públicas",
                    "Aumenta las penas para delitos de corrupción de funcionarios públicos",
                ],
                "ejemplos_negativos": [
                    "Modifica el sistema electoral",
                    "Crea la nueva Constitución",
                ],
                "reglas_semanticas": [
                    r"transparencia|probidad|acceso\s+a\s+la\s+información\s+pública",
                    r"\blobby\b|gestor\s+de\s+intereses|ley\s+de\s+lobby",
                    r"declaración\s+de\s+(patrimonio|intereses)",
                    r"\bCPLT\b|consejo\s+para\s+la\s+transparencia",
                    r"corrupción\s+pública|cohecho|soborno",
                ],
            },
            "SISTEMA_ELECTORAL": {
                "label": "Sistema electoral y partidos políticos",
                "definition": "Ley electoral, sistema de partidos, financiamiento político, Servel, voto en el extranjero y paridad en listas.",
                "keywords": [
                    "sistema electoral", "elecciones", "Servel",
                    "partido político", "primarias", "independiente",
                    "financiamiento de la política", "gasto electoral",
                    "voto en el extranjero", "voto migrante",
                    "diputado", "senador", "circunscripción", "distrito",
                    "paridad en listas electorales",
                ],
                "synonyms": ["elecciones", "sistema de partidos", "legislativo"],
                "etiquetas": ["elecciones", "Servel", "partidos_politicos", "voto_extranjero", "paridad_listas"],
                "ejemplos_positivos": [
                    "Modifica el sistema electoral para establecer paridad de género en las listas",
                    "Crea el voto obligatorio para las elecciones presidenciales",
                    "Regula el financiamiento privado de los partidos políticos",
                ],
                "ejemplos_negativos": [
                    "Modifica la ley orgánica de municipalidades",
                    "Establece nuevas normas de transparencia",
                ],
                "reglas_semanticas": [
                    r"sistema\s+electoral|elecciones\s+(presidenciales|parlamentarias|municipales)",
                    r"\bServel\b|partido\s+político",
                    r"voto\s+(en\s+el\s+)?extranjero|voto\s+migrante|voto\s+obligatorio",
                    r"paridad\s+(de\s+género\s+)?en\s+(las\s+)?listas",
                    r"financiamiento\s+(de\s+la\s+política|político|electoral)",
                ],
            },
            "FUNCION_PUBLICA": {
                "label": "Función pública y empleados del Estado",
                "definition": "Estatuto administrativo, carrera funcionaria, contratas, personal a honorarios del sector público y modernización del Estado.",
                "keywords": [
                    "función pública", "funcionario público", "empleado público",
                    "estatuto administrativo", "carrera funcionaria", "concurso público",
                    "contrata", "honorarios en el Estado", "planta",
                    "modernización del Estado", "digitalización del Estado",
                    "servicio civil", "ADP", "alta dirección pública",
                    "Contraloría", "CGR",
                ],
                "synonyms": ["servicio público", "empleados del Estado", "administración pública"],
                "etiquetas": ["funcionarios_publicos", "estatuto_administrativo", "ADP", "Contraloria"],
                "ejemplos_positivos": [
                    "Modifica el estatuto administrativo para regularizar a los trabajadores a honorarios",
                    "Fortalece el sistema de alta dirección pública",
                    "Amplía las facultades de la Contraloría General de la República",
                ],
                "ejemplos_negativos": [
                    "Modifica la ley de partidos políticos",
                    "Reforma el sistema municipal",
                ],
                "reglas_semanticas": [
                    r"función\s+pública|funcionario(s)?\s+público(s)?",
                    r"estatuto\s+administrativo|carrera\s+funcionaria",
                    r"\bADP\b|alta\s+dirección\s+pública",
                    r"\bContraloría\b|\bCGR\b",
                    r"contratas?\s+(del\s+)?sector\s+público|honorarios\s+(en\s+el\s+)?Estado",
                ],
            },
        },
    },
}


# ─── Índice plano para búsqueda rápida ───────────────────────────────────────

def get_all_categories() -> list[str]:
    return list(TAXONOMY.keys())


def get_all_subcategories() -> list[tuple[str, str]]:
    result = []
    for cat_code, cat_data in TAXONOMY.items():
        for sub_code in cat_data["subcategorias"]:
            result.append((cat_code, sub_code))
    return result


def get_category_keywords(cat_code: str) -> list[str]:
    cat = TAXONOMY.get(cat_code, {})
    kws = list(cat.get("keywords", []))
    for sub in cat.get("subcategorias", {}).values():
        kws.extend(sub.get("keywords", []))
    return list(set(kws))


def get_prototype_texts(cat_code: str) -> list[str]:
    cat = TAXONOMY.get(cat_code, {})
    texts = list(cat.get("prototype_texts", []))
    for sub in cat.get("subcategorias", {}).values():
        texts.extend(sub.get("ejemplos_positivos", []))
    return texts
