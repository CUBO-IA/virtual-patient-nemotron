"""Script para enriquecer casos.json con pruebas, plan_esperado, evolucion y revision_clinica (SEGUIMIENTO.md)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASOS_PATH = ROOT / "data" / "casos.json"

ENRIQUECIMIENTO = {
    "c_dengue_01": {
        "revision_clinica": {
            "estado": "pendiente",
            "revisado_por": None,
            "fecha": None,
            "fuente": None,
            "observaciones": "Contenido de pruebas, plan y evolución redactado con ayuda de IA. Pendiente de revisión por un profesional de la salud antes de presentarse como validado."
        },
        "pruebas": {
            "resultado_defecto": "Sin alteraciones valorables para el cuadro clínico actual.",
            "resultados": {
                "hemograma": {
                    "pertinencia": "esencial",
                    "informe": "Leucopenia y trombocitopenia acentuada con elevación de hematocrito.",
                    "valores": [
                        {"analito": "Leucocitos", "valor": "3 100", "unidad": "/µL", "referencia": "4 500-11 000", "estado": "bajo"},
                        {"analito": "Plaquetas", "valor": "78 000", "unidad": "/µL", "referencia": "150 000-450 000", "estado": "bajo"},
                        {"analito": "Hematocrito", "valor": "49", "unidad": "%", "referencia": "37-47", "estado": "alto"}
                    ]
                },
                "prueba_dengue": {
                    "pertinencia": "esencial",
                    "informe": "Antígeno NS1: Positivo reactivo. Anticuerpos IgM: Positivo débil. Anticuerpos IgG: Negativo."
                },
                "transaminasas": {
                    "pertinencia": "util",
                    "informe": "TGO/AST 88 U/L (elevada), TGP/ALT 65 U/L (levemente elevada).",
                    "valores": [
                        {"analito": "TGO (AST)", "valor": "88", "unidad": "U/L", "referencia": "10-40", "estado": "alto"},
                        {"analito": "TGP (ALT)", "valor": "65", "unidad": "U/L", "referencia": "10-40", "estado": "alto"}
                    ]
                },
                "quimica_sanguinea": {
                    "pertinencia": "util",
                    "informe": "Glucosa 94 mg/dL, Creatinina 0.9 mg/dL, Urea 28 mg/dL. Parámetros normales."
                },
                "ecografia_abdominal": {
                    "pertinencia": "util",
                    "informe": "Engrosamiento de pared vesicular (4.2 mm) y escaso líquido libre en espacio de Morrison."
                },
                "rx_torax": {
                    "pertinencia": "innecesaria",
                    "informe": "Campos pulmonares libres de consolidaciones. Senos costofrénicos conservados."
                },
                "ego": {
                    "pertinencia": "innecesaria",
                    "informe": "Sedimento urinario limpio, sin proteinuria ni hematuria."
                }
            },
            "esenciales": ["hemograma", "prueba_dengue"]
        },
        "plan_esperado": {
            "disposicion": {
                "correcta": ["referencia", "emergencia"],
                "aceptable": ["observacion"]
            },
            "medicamentos": {
                "adecuados": [
                    {"id": "acetaminofen", "nota": "Antipirético y analgésico de elección en sospecha de flavivirus."}
                ],
                "aceptables": [
                    {"id": "suero_fisiologico_iv", "nota": "Hidratación endovenosa guiada para reposición de volumen."}
                ],
                "contraindicados": [
                    {"id": "ibuprofeno", "motivo": "AINE contraindicado por riesgo crítico de hemorragia y disfunción plaquetaria."},
                    {"id": "aspirina", "motivo": "Riesgo de sangrado grave y síndrome de Reye."}
                ]
            },
            "indicaciones": {
                "esenciales": ["hidratacion", "signos_alarma", "control", "evitar_ains"]
            },
            "alergias_trampa": []
        },
        "evolucion": {
            "control_en_dias": 2,
            "ramas": {
                "empeora": {
                    "condicion": "hay_contraindicado o disposicion_insuficiente",
                    "relato": "Mire doctor, me he puesto peor... anoche me empezó a salir sangre por las encías y tengo un dolor insoportable en la boca del estómago."
                },
                "parcial": {
                    "condicion": "disposicion_aceptable o faltan_indicaciones_esenciales",
                    "relato": "Fíjese que sigo algo decaído y con basca, pero al menos la calentura no me ha subido tanto. No me siento al cien."
                },
                "mejora": {
                    "condicion": "disposicion_correcta y sin_contraindicados y indicaciones_esenciales_completas",
                    "relato": "Ya me siento mucho más aliviado, doctor. Me tuvieron en observación con suerito, la fiebre cedió y ya tolero los frescos."
                }
            }
        }
    },
    "c_erc_01": {
        "revision_clinica": {
            "estado": "pendiente",
            "revisado_por": None,
            "fecha": None,
            "fuente": None,
            "observaciones": "Contenido de pruebas, plan y evolución redactado con ayuda de IA. Pendiente de revisión por un profesional de la salud antes de presentarse como validado."
        },
        "pruebas": {
            "resultado_defecto": "Parámetros dentro de rangos esperables para la condición basal.",
            "resultados": {
                "quimica_sanguinea": {
                    "pertinencia": "esencial",
                    "informe": "Creatinina sérica 3.8 mg/dL, Nitrógeno de urea (BUN) 48 mg/dL, Glucosa 102 mg/dL. TFG estimada por CKD-EPI: 16 mL/min/1.73m².",
                    "valores": [
                        {"analito": "Creatinina", "valor": "3.8", "unidad": "mg/dL", "referencia": "0.7-1.3", "estado": "alto"},
                        {"analito": "Urea", "valor": "103", "unidad": "mg/dL", "referencia": "15-45", "estado": "alto"}
                    ]
                },
                "ego": {
                    "pertinencia": "esencial",
                    "informe": "Proteinuria de 300 mg/dL (+++), densidad 1.010, cilindros céreos granulosos en sedimento.",
                    "valores": [
                        {"analito": "Proteínas en orina", "valor": "300", "unidad": "mg/dL", "referencia": "0-15", "estado": "alto"},
                        {"analito": "Densidad", "valor": "1.010", "unidad": "", "referencia": "1.015-1.025", "estado": "bajo"}
                    ]
                },
                "electrolitos": {
                    "pertinencia": "esencial",
                    "informe": "Potasio sérico 5.6 mEq/L (hiperpotasemia leve), Sodio 137 mEq/L, Cloro 104 mEq/L.",
                    "valores": [
                        {"analito": "Potasio", "valor": "5.6", "unidad": "mEq/L", "referencia": "3.5-5.0", "estado": "alto"},
                        {"analito": "Sodio", "valor": "137", "unidad": "mEq/L", "referencia": "135-145", "estado": "normal"}
                    ]
                },
                "hemograma": {
                    "pertinencia": "util",
                    "informe": "Hemoglobina 9.2 g/dL, Hematocrito 28 %, Leucocitos 6 800/µL, Plaquetas 210 000/µL. Anemia normocítica normocrómica.",
                    "valores": [
                        {"analito": "Hemoglobina", "valor": "9.2", "unidad": "g/dL", "referencia": "13.0-17.0", "estado": "bajo"}
                    ]
                },
                "ecografia_abdominal": {
                    "pertinencia": "util",
                    "informe": "Riñones de tamaño disminuido bilateralmente con pérdida de la diferenciación corticomedular y aumento difuso de ecogenicidad."
                },
                "gasometria": {
                    "pertinencia": "util",
                    "informe": "pH 7.31, HCO3 18 mEq/L, pCO2 36 mmHg. Acidosis metabólica leve con anión gap normal."
                },
                "rx_torax": {
                    "pertinencia": "innecesaria",
                    "informe": "Índice cardiotorácico en límite superior, sin derrame pleural visible."
                }
            },
            "esenciales": ["quimica_sanguinea", "ego", "electrolitos"]
        },
        "plan_esperado": {
            "disposicion": {
                "correcta": ["referencia"],
                "aceptable": ["ambulatorio", "observacion"]
            },
            "medicamentos": {
                "adecuados": [
                    {"id": "amlodipino", "nota": "Antihipertensivo de elección seguro que no compromete hemodinámica glomerular."}
                ],
                "aceptables": [
                    {"id": "losartan", "nota": "Nefroprotector con precaución y vigilancia estricta de potasio sérico."},
                    {"id": "enalapril", "nota": "IECA para control de tensión con monitoreo estricto de función renal."}
                ],
                "contraindicados": [
                    {"id": "ibuprofeno", "motivo": "Los AINEs precipitan deterioro agudo sobre crónica y elevan el potasio."},
                    {"id": "aspirina", "motivo": "Riesgo de hemorragia gastrointestinal y daño a la perfusión renal."}
                ]
            },
            "indicaciones": {
                "esenciales": ["dieta", "monitoreo_presion", "control", "evitar_ains"]
            },
            "alergias_trampa": []
        },
        "evolucion": {
            "control_en_dias": 7,
            "ramas": {
                "empeora": {
                    "condicion": "hay_contraindicado o disposicion_insuficiente",
                    "relato": "Mire doctor, me he hinchado todo de la cara y los pies, casi no estoy orinando y me siento sumamente mareado y con asco."
                },
                "parcial": {
                    "condicion": "disposicion_aceptable o faltan_indicaciones_esenciales",
                    "relato": "He seguido un poco pesado de las piernas, doctor. La presión ha bajado poquito pero todavía me siento desganado para comer."
                },
                "mejora": {
                    "condicion": "disposicion_correcta y sin_contraindicados y indicaciones_esenciales_completas",
                    "relato": "Gracias a Dios ya me siento más despejado, doctor. Con la dieta sin sal y las pastillas la presión se me normalizó y ya tengo cita con el especialista."
                }
            }
        }
    },
    "c_dm2_01": {
        "revision_clinica": {
            "estado": "pendiente",
            "revisado_por": None,
            "fecha": None,
            "fuente": None,
            "observaciones": "Contenido de pruebas, plan y evolución redactado con ayuda de IA. Pendiente de revisión por un profesional de la salud antes de presentarse como validado."
        },
        "pruebas": {
            "resultado_defecto": "Valores en rango fisiológico normal.",
            "resultados": {
                "glucosa_capilar": {
                    "pertinencia": "esencial",
                    "informe": "Glucemia capilar casual en ayunas: 245 mg/dL.",
                    "valores": [
                        {"analito": "Glucosa capilar", "valor": "245", "unidad": "mg/dL", "referencia": "70-100", "estado": "alto"}
                    ]
                },
                "quimica_sanguinea": {
                    "pertinencia": "esencial",
                    "informe": "Glucosa sérica en ayunas 238 mg/dL, Creatinina 0.8 mg/dL, Urea 26 mg/dL.",
                    "valores": [
                        {"analito": "Glucosa", "valor": "238", "unidad": "mg/dL", "referencia": "70-100", "estado": "alto"},
                        {"analito": "Creatinina", "valor": "0.8", "unidad": "mg/dL", "referencia": "0.6-1.1", "estado": "normal"}
                    ]
                },
                "ego": {
                    "pertinencia": "esencial",
                    "informe": "Glucosuria (+++), cetonas negativas, sin proteinuria ni signos de infección activa.",
                    "valores": [
                        {"analito": "Glucosa en orina", "valor": "+++", "unidad": "", "referencia": "Negativo", "estado": "alto"},
                        {"analito": "Cetonas en orina", "valor": "Negativo", "unidad": "", "referencia": "Negativo", "estado": "normal"}
                    ]
                },
                "perfil_lipidico": {
                    "pertinencia": "util",
                    "informe": "Triglicéridos 220 mg/dL (elevados), Colesterol total 215 mg/dL, HDL 38 mg/dL, LDL 133 mg/dL.",
                    "valores": [
                        {"analito": "Triglicéridos", "valor": "220", "unidad": "mg/dL", "referencia": "<150", "estado": "alto"}
                    ]
                },
                "hemograma": {
                    "pertinencia": "innecesaria",
                    "informe": "Glóbulos blancos 7 200/µL, Hemoglobina 14.1 g/dL, Plaquetas 240 000/µL."
                },
                "rx_torax": {
                    "pertinencia": "innecesaria",
                    "informe": "Silueta cardiovascular y parénquima pulmonar normales."
                }
            },
            "esenciales": ["glucosa_capilar", "quimica_sanguinea", "ego"]
        },
        "plan_esperado": {
            "disposicion": {
                "correcta": ["ambulatorio"],
                "aceptable": ["observacion"]
            },
            "medicamentos": {
                "adecuados": [
                    {"id": "metformina", "nota": "Fármaco de primera línea para control glucémico y reducción de resistencia insulínica."}
                ],
                "aceptables": [],
                "contraindicados": []
            },
            "indicaciones": {
                "esenciales": ["dieta", "monitoreo_glucosa", "control", "adherencia_tratamiento"]
            },
            "alergias_trampa": []
        },
        "evolucion": {
            "control_en_dias": 7,
            "ramas": {
                "empeora": {
                    "condicion": "hay_contraindicado o faltan_medicamentos_adecuados",
                    "relato": "Mire doctor, sigo con aquella gran sed que no se me quita y levantándome a cada rato en la noche a orinar, paso bien desganado."
                },
                "parcial": {
                    "condicion": "disposicion_aceptable o faltan_indicaciones_esenciales",
                    "relato": "Me he tomado la pastilla, pero la verdad me ha costado dejar el pancito dulce y las gaseosas. Ya no tengo tanta sequedad en la boca."
                },
                "mejora": {
                    "condicion": "disposicion_correcta y sin_contraindicados y medicacion_adecuada_completa y indicaciones_esenciales_completas",
                    "relato": "Fíjese doctor que me siento con más energía. Con la dieta y la medicina ya no tengo tanta sed y el pinchoncito del azúcar me sale mucho mejor."
                }
            }
        }
    },
    "c_hta_01": {
        "revision_clinica": {
            "estado": "pendiente",
            "revisado_por": None,
            "fecha": None,
            "fuente": None,
            "observaciones": "Contenido de pruebas, plan y evolución redactado con ayuda de IA. Pendiente de revisión por un profesional de la salud antes de presentarse como validado."
        },
        "pruebas": {
            "resultado_defecto": "Estudio sin datos de daño agudo de órgano blanco.",
            "resultados": {
                "ecg": {
                    "pertinencia": "esencial",
                    "informe": "Ritmo sinusal a 88 lpm. Signos de sobrecarga sistólica ventricular izquierda (Sokolow-Lyon positivo: 38 mm), sin elevación de segmento ST."
                },
                "quimica_sanguinea": {
                    "pertinencia": "esencial",
                    "informe": "Creatinina 1.1 mg/dL, Urea 34 mg/dL, Glucosa 108 mg/dL. Sin deterioro de función renal basal."
                },
                "ego": {
                    "pertinencia": "esencial",
                    "informe": "Densidad 1.020, proteínas trazas, sedimento sin hematíes dismórficos ni cilindros celulares."
                },
                "rx_torax": {
                    "pertinencia": "util",
                    "informe": "Cardiomegalia grado I a expensas de ventrículo izquierdo. No hay signos de edema pulmonar agudo."
                },
                "electrolitos": {
                    "pertinencia": "util",
                    "informe": "Sodio 140 mEq/L, Potasio 4.2 mEq/L, Cloro 102 mEq/L."
                },
                "tac_craneo": {
                    "pertinencia": "innecesaria",
                    "informe": "Sin evidencia de infarto reciente ni colecciones hemorrágicas agudas intra o extraaxiales."
                },
                "hemograma": {
                    "pertinencia": "innecesaria",
                    "informe": "Línea roja, blanca y plaquetaria sin anomalías morfológicas ni numéricas."
                }
            },
            "esenciales": ["ecg", "quimica_sanguinea", "ego"]
        },
        "plan_esperado": {
            "disposicion": {
                "correcta": ["observacion", "referencia"],
                "aceptable": ["ambulatorio"]
            },
            "medicamentos": {
                "adecuados": [
                    {"id": "amlodipino", "nota": "Calcioantagonista para reducción gradual de resistencias vasculares periféricas."},
                    {"id": "captopril", "nota": "IECA útil para descenso gradual y controlado de presión arterial."}
                ],
                "aceptables": [
                    {"id": "enalapril", "nota": "IECA para titulación paulatina de cifras tensionales."},
                    {"id": "losartan", "nota": "ARA-II para manejo continuado de hipertensión arterial."}
                ],
                "contraindicados": [
                    {"id": "ibuprofeno", "motivo": "Los AINEs provocan retención hidrosalina y descompensan la presión arterial."}
                ]
            },
            "indicaciones": {
                "esenciales": ["reposo", "monitoreo_presion", "control", "dieta"]
            },
            "alergias_trampa": []
        },
        "evolucion": {
            "control_en_dias": 3,
            "ramas": {
                "empeora": {
                    "condicion": "hay_contraindicado o disposicion_insuficiente",
                    "relato": "Doctor, me volvió un dolor de cabeza palpitante en la nuca bien fuerte y siento que me zumban los oídos, la maquinita me marca arriba de 180."
                },
                "parcial": {
                    "condicion": "disposicion_aceptable o faltan_indicaciones_esenciales",
                    "relato": "El dolor de cabeza se me calmó un poco, doctor, pero todavía me siento medio atarantado y la presión todavía me anda en 150."
                },
                "mejora": {
                    "condicion": "disposicion_correcta y sin_contraindicados y medicacion_adecuada_completa y indicaciones_esenciales_completas",
                    "relato": "Ya me siento mucho más sereno, doctor. Se me quitó la pesadez en la cabeza y las tomas de presión ya me salieron todas en 125 con 80."
                }
            }
        }
    },
    "c_trauma_01": {
        "revision_clinica": {
            "estado": "pendiente",
            "revisado_por": None,
            "fecha": None,
            "fuente": None,
            "observaciones": "Contenido de pruebas, plan y evolución redactado con ayuda de IA. Pendiente de revisión por un profesional de la salud antes de presentarse como validado."
        },
        "pruebas": {
            "resultado_defecto": "Sin lesiones traumáticas evidentes en esta región anatómica.",
            "resultados": {
                "rx_columna_cervical": {
                    "pertinencia": "esencial",
                    "informe": "Alineación de cuerpos vertebrales C1 a C7 conservada, espacios discales respetados, sin trazos de fractura ni luxación evidente."
                },
                "rx_torax": {
                    "pertinencia": "esencial",
                    "informe": "Opacidad alveolar heterogénea basal derecha sin retracción. Pleura visceral adosada a pared torácica en ambos hemitórax, ángulos costofrénicos despejados. Arcos costales sin trazos radiológicos de discontinuidad."
                },
                "ecografia_abdominal": {
                    "pertinencia": "esencial",
                    "informe": "Protocolo FAST negativo: No se observa líquido libre en saco de Douglas, fosa hepatorrenal ni periesplénica."
                },
                "hemograma": {
                    "pertinencia": "util",
                    "informe": "Hemoglobina 13.5 g/dL, Leucocitos 11 200/µL (leucocitosis reactiva por estrés), Plaquetas 220 000/µL."
                },
                "quimica_sanguinea": {
                    "pertinencia": "util",
                    "informe": "Glucosa 132 mg/dL, Creatinina 0.9 mg/dL. Glucemia de estrés."
                },
                "tac_craneo": {
                    "pertinencia": "util",
                    "informe": "Sin fracturas de calota ni sangrado intracraneal subaracnoideo o parenquimatoso."
                },
                "perfil_lipidico": {
                    "pertinencia": "innecesaria",
                    "informe": "Lípidos en límites estándar sin relevancia en urgencia traumática."
                }
            },
            "esenciales": ["rx_columna_cervical", "rx_torax", "ecografia_abdominal"]
        },
        "plan_esperado": {
            "disposicion": {
                "correcta": ["referencia", "emergencia"],
                "aceptable": ["observacion"]
            },
            "medicamentos": {
                "adecuados": [
                    {"id": "collarin_cervical", "nota": "Inmovilización cervical obligatoria hasta confirmación clínica y radiológica."},
                    {"id": "acetaminofen", "nota": "Analgésico seguro de inicio para dolor traumático."}
                ],
                "aceptables": [
                    {"id": "suero_fisiologico_iv", "nota": "Acceso venoso periférico y mantenimiento de volumen."}
                ],
                "contraindicados": [
                    {"id": "ibuprofeno", "motivo": "Riesgo de hemorragia interna oculta en trauma agudo no estabilizado."}
                ]
            },
            "indicaciones": {
                "esenciales": ["inmovilizacion_espinal", "reposo", "signos_alarma"]
            },
            "alergias_trampa": []
        },
        "evolucion": {
            "control_en_dias": 2,
            "ramas": {
                "empeora": {
                    "condicion": "hay_contraindicado o disposicion_insuficiente",
                    "relato": "Doctor, me cuesta respirar hondo, me empezó a doler intensamente el costado y me siento como que me voy a desmayar."
                },
                "parcial": {
                    "condicion": "disposicion_aceptable o faltan_indicaciones_esenciales",
                    "relato": "Todavía ando todo adolorido de los golpes y el cuello tieso, doctor, pero al menos no he vomitado ni perdido el sentido."
                },
                "mejora": {
                    "condicion": "disposicion_correcta y sin_contraindicados y medicacion_adecuada_completa y indicaciones_esenciales_completas",
                    "relato": "Fíjese que en el hospital me chequearon completo con las placas y el cuello protegido, ya me siento más seguro y con menos dolor."
                }
            }
        }
    },
    "c_gea_01": {
        "revision_clinica": {
            "estado": "pendiente",
            "revisado_por": None,
            "fecha": None,
            "fuente": None,
            "observaciones": "Contenido de pruebas, plan y evolución redactado con ayuda de IA. Pendiente de revisión por un profesional de la salud antes de presentarse como validado."
        },
        "pruebas": {
            "resultado_defecto": "Estudio sin hallazgos inflamatorios patológicos.",
            "resultados": {
                "examen_heces": {
                    "pertinencia": "esencial",
                    "informe": "Heces líquidas de color marrón, leucocitos 2 a 4 por campo, no se observan amebas ni quistes parasitarios, sangre oculta negativa."
                },
                "electrolitos": {
                    "pertinencia": "util",
                    "informe": "Sodio 138 mEq/L, Potasio 3.9 mEq/L, Cloro 101 mEq/L. Sin desequilibrio hidroelectrolítico significativo."
                },
                "quimica_sanguinea": {
                    "pertinencia": "util",
                    "informe": "Glucosa 88 mg/dL, Creatinina 0.8 mg/dL, Urea 22 mg/dL. Parámetros renales normales."
                },
                "hemograma": {
                    "pertinencia": "util",
                    "informe": "Glóbulos blancos 8 600/µL, Linfocitos 32%, Neutrófilos 62%, Plaquetas 250 000/µL."
                },
                "rx_torax": {
                    "pertinencia": "innecesaria",
                    "informe": "Silueta cardíaca y parénquima pulmonar normales."
                },
                "coprocultivo": {
                    "pertinencia": "innecesaria",
                    "informe": "Desarrollo de flora entérica habitual sin aislamiento de patógenos invasivos."
                }
            },
            "esenciales": ["examen_heces"]
        },
        "plan_esperado": {
            "disposicion": {
                "correcta": ["ambulatorio"],
                "aceptable": ["observacion"]
            },
            "medicamentos": {
                "adecuados": [
                    {"id": "sales_rehidratacion", "nota": "Pilar fundamental del tratamiento para prevención y corrección de deshidratación."}
                ],
                "aceptables": [
                    {"id": "acetaminofen", "nota": "Para manejo del dolor tipo cólico leve o febrícula si fuera necesario."}
                ],
                "contraindicados": [
                    {"id": "loperamida", "motivo": "Contraindicado en diarrea infecciosa por riesgo de íleo paralítico y proliferación de toxinas."},
                    {"id": "ciprofloxacino", "motivo": "Uso inadecuado de antibióticos en cuadros virales o sin disentería comprobada."}
                ]
            },
            "indicaciones": {
                "esenciales": ["hidratacion", "dieta", "signos_alarma", "control"]
            },
            "alergias_trampa": []
        },
        "evolucion": {
            "control_en_dias": 3,
            "ramas": {
                "empeora": {
                    "condicion": "hay_contraindicado",
                    "relato": "Doctor, me tomé esa pastilla para taparme y ahora tengo la panza inflada como tambor, con retortijones terribles y calentura."
                },
                "parcial": {
                    "condicion": "disposicion_aceptable",
                    "relato": "Todavía voy unas dos o tres veces al baño suelto, doctor, pero al menos ya no me da vómito y tengo un poquito más de ánimo."
                },
                "mejora": {
                    "condicion": "disposicion_correcta y sin_contraindicados y medicacion_adecuada_completa y indicaciones_esenciales_completas",
                    "relato": "Mire doctor, gracias al suerito oral me recuperé volando. Ya mis heces se compusieron, tengo buen apetito y ando como si nada."
                }
            }
        }
    },
    "c_nac_01": {
        "revision_clinica": {
            "estado": "pendiente",
            "revisado_por": None,
            "fecha": None,
            "fuente": None,
            "observaciones": "Contenido de pruebas, plan y evolución redactado con ayuda de IA. Pendiente de revisión por un profesional de la salud antes de presentarse como validado."
        },
        "pruebas": {
            "resultado_defecto": "Estudio sin datos de patología cardiopulmonar agregada.",
            "resultados": {
                "rx_torax": {
                    "pertinencia": "esencial",
                    "informe": "Infiltrado alveolar con broncograma aéreo en lóbulo inferior derecho compatible con condensación parenquimatosa. Senos libres."
                },
                "hemograma": {
                    "pertinencia": "esencial",
                    "informe": "Leucocitosis de 15 400/µL con neutrofilia del 84% y formas en banda 6%. Plaquetas 290 000/µL. Hemoglobina 13.2 g/dL.",
                    "valores": [
                        {"analito": "Leucocitos", "valor": "15 400", "unidad": "/µL", "referencia": "4 500-11 000", "estado": "alto"},
                        {"analito": "Neutrófilos", "valor": "84", "unidad": "%", "referencia": "45-70", "estado": "alto"}
                    ]
                },
                "pcr": {
                    "pertinencia": "esencial",
                    "informe": "Proteína C Reactiva: 78 mg/L (elevada, indicativa de proceso inflamatorio infeccioso agudo).",
                    "valores": [
                        {"analito": "Proteína C Reactiva", "valor": "78", "unidad": "mg/L", "referencia": "<5", "estado": "alto"}
                    ]
                },
                "quimica_sanguinea": {
                    "pertinencia": "util",
                    "informe": "Urea 32 mg/dL, Creatinina 0.9 mg/dL, Glucosa 104 mg/dL. Criterio de nitrógeno en escala de gravedad en rango bajo."
                },
                "gasometria": {
                    "pertinencia": "util",
                    "informe": "pO2 68 mmHg, SatO2 92%, pCO2 34 mmHg, pH 7.42. Hipoxemia leve a moderada en aire ambiente."
                },
                "ecografia_abdominal": {
                    "pertinencia": "innecesaria",
                    "informe": "Hígado, vías biliares y riñones sin alteraciones morfológicas."
                },
                "perfil_lipidico": {
                    "pertinencia": "innecesaria",
                    "informe": "Fracciones lipídicas dentro de normalidad."
                }
            },
            "esenciales": ["rx_torax", "hemograma", "pcr"]
        },
        "plan_esperado": {
            "disposicion": {
                "correcta": ["ambulatorio", "observacion"],
                "aceptable": ["referencia"]
            },
            "medicamentos": {
                "adecuados": [
                    {"id": "amoxicilina", "nota": "Antibiótico de primera elección ambulatoria para cobertura de patógenos bacterianos respiratorios típicos."},
                    {"id": "amoxicilina_clavulanico", "nota": "Betalactámico con inhibidor para paciente con comorbilidades o factores de riesgo."}
                ],
                "aceptables": [
                    {"id": "acetaminofen", "nota": "Manejo sintomático de la fiebre y el dolor torácico pleurítico."}
                ],
                "contraindicados": [
                    {"id": "ciprofloxacino", "motivo": "Las fluoroquinolonas comunes no tienen espectro neumocócico óptimo y no son primera línea comunitaria."}
                ]
            },
            "indicaciones": {
                "esenciales": ["hidratacion", "reposo", "signos_alarma", "control", "adherencia_tratamiento"]
            },
            "alergias_trampa": []
        },
        "evolucion": {
            "control_en_dias": 3,
            "ramas": {
                "empeora": {
                    "condicion": "hay_contraindicado o faltan_medicamentos_adecuados",
                    "relato": "Doctor, me cuesta mucho agarrar aire, el pecho me silba al respirar y la calentura me sigue subiendo hasta 39 grados."
                },
                "parcial": {
                    "condicion": "faltan_indicaciones_esenciales",
                    "relato": "Ya no me ahogo tanto al caminar, doctor, pero todavía saco flema verdosa y me canso fácil al dar un par de pasos."
                },
                "mejora": {
                    "condicion": "disposicion_correcta y sin_contraindicados y medicacion_adecuada_completa y indicaciones_esenciales_completas",
                    "relato": "Mire doctor, con el antibiótico cumplido me he sentido un gran alivio. Ya casi no toso, la fiebre desapareció y respiro bien tranquilo."
                }
            }
        }
    },
    "c_depresion_01": {
        "revision_clinica": {
            "estado": "pendiente",
            "revisado_por": None,
            "fecha": None,
            "fuente": None,
            "observaciones": "Contenido de pruebas, plan y evolución redactado con ayuda de IA. Pendiente de revisión por un profesional de la salud antes de presentarse como validado."
        },
        "pruebas": {
            "resultado_defecto": "Estudio dentro de límites normales, descartando causa médica primaria.",
            "resultados": {
                "tsh": {
                    "pertinencia": "esencial",
                    "informe": "TSH sérica: 2.1 µUI/mL. Parámetro hormonal eutiroideo en rango esperado del laboratorio (0.4-4.5 µUI/mL).",
                    "valores": [
                        {"analito": "TSH", "valor": "2.1", "unidad": "µUI/mL", "referencia": "0.4-4.5", "estado": "normal"}
                    ]
                },
                "hemograma": {
                    "pertinencia": "esencial",
                    "informe": "Glóbulos rojos, hemoglobina (13.8 g/dL), leucocitos y plaquetas dentro de parámetros normales. Sin anemia."
                },
                "quimica_sanguinea": {
                    "pertinencia": "esencial",
                    "informe": "Glucosa 92 mg/dL, Creatinina 0.8 mg/dL, Electrolitos dentro de límites normales. Función renal conservada."
                },
                "ego": {
                    "pertinencia": "util",
                    "informe": "Examen general de orina sin signos de leucocituria ni proteinuria."
                },
                "ecg": {
                    "pertinencia": "util",
                    "informe": "Ritmo sinusal regular, intervalo QTc de 410 ms (normal), sin trastornos de repolarización."
                },
                "tac_craneo": {
                    "pertinencia": "innecesaria",
                    "informe": "Sin alteraciones estructurales, hidrocefalia ni masas intracraneales visibles."
                },
                "rx_torax": {
                    "pertinencia": "innecesaria",
                    "informe": "Campos pulmonares y silueta cardíaca de características normales."
                }
            },
            "esenciales": ["tsh", "hemograma", "quimica_sanguinea"]
        },
        "plan_esperado": {
            "disposicion": {
                "correcta": ["ambulatorio", "referencia"],
                "aceptable": ["observacion"]
            },
            "medicamentos": {
                "adecuados": [
                    {"id": "sertralina", "nota": "Antidepresivo inhibidor selectivo de la recaptación de serotonina (ISRS) de primera línea con buen perfil de seguridad."},
                    {"id": "fluoxetina", "nota": "ISRS alternativo de primera elección para el manejo de trastornos depresivos."}
                ],
                "aceptables": [],
                "contraindicados": []
            },
            "indicaciones": {
                "esenciales": ["psicoeducacion", "vigilancia_suicida", "derivacion_salud_mental", "control"]
            },
            "alergias_trampa": []
        },
        "evolucion": {
            "control_en_dias": 7,
            "ramas": {
                "empeora": {
                    "condicion": "faltan_indicaciones_esenciales o faltan_medicamentos_adecuados",
                    "relato": "Doctor, la verdad sigo encerrado sin querer ver a nadie, las noches son eternas y siento que para mi familia solo soy una carga pesada."
                },
                "parcial": {
                    "condicion": "disposicion_aceptable",
                    "relato": "He estado tomando la pastillita, doctor. Todavía me siento apapagado y con desgano, pero al menos mi hermana me ha estado acompañando."
                },
                "mejora": {
                    "condicion": "disposicion_correcta y sin_contraindicados y medicacion_adecuada_completa y indicaciones_esenciales_completas",
                    "relato": "Doctor, poco a poco voy viendo la luz. El apoyo en casa y la medicina me han ayudado a dormir mejor y ya tengo mi cita para la terapia."
                }
            }
        }
    }
}


def main():
    with open(CASOS_PATH, "r", encoding="utf-8") as f:
        casos = json.load(f)

    for caso in casos:
        cid = caso["id"]
        if cid in ENRIQUECIMIENTO:
            for k, v in ENRIQUECIMIENTO[cid].items():
                caso[k] = v

    with open(CASOS_PATH, "w", encoding="utf-8") as f:
        json.dump(casos, f, ensure_ascii=False, indent=2)

    print(f"OK: {len(casos)} casos enriquecidos exitosamente con datos clínicos de SEGUIMIENTO.md.")


if __name__ == "__main__":
    main()
