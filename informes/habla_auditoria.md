# Auditoría de habla salvadoreña

Generado: 2026-11-21 21:15. Glosario: `data/habla_salvadorena.json` (**borrador, sin validar por hablantes**).

## 1. Auditoría de datos (casos)

- Casos revisados: **8**
- Términos a evitar en lo que el paciente dice o copia: **2**
- Temas (claves de `datos_si_pregunta`) con vocabulario técnico: **1** (entran al prompt como «Si te preguntan por…»)

### Errores

- `c_gea_01` · `sintomas[0]`: «deposiciones líquidas como seis o siete veces al día» → contiene **deposicion**. Alternativas: «diarrea», «cursera», «ir al baño a cada rato»
- `c_gea_01` · `evolucion.mejora.relato`: «Mire doctor, gracias al suerito oral me recuperé volando. Ya mis heces se compusieron, tengo buen apetito y ando como si nada.» → contiene **heces**. Alternativas: «ir al baño», «lo que sale al hacer del baño», «las heces negras»

### Avisos (temas)

- `c_gea_01` · tema 'características de las heces' → **heces**. Alternativas: «ir al baño», «lo que sale al hacer del baño», «las heces negras»

### Redacción en tercera persona

**52 de 179** textos del paciente (29 %) parecen estar escritos en 3.ª persona (heurística). El modelo los repite como un narrador («ha bajado unas 5 libras», «le duele al tomar aire»).

- `c_dengue_01` · `habitos[0]`: «vive en una zona con muchos zancudos»
- `c_dengue_01` · `datos_si_pregunta['dolor de barriga']`: «desde ayer le duele la barriga, sobre todo arriba, y siente que no aguanta»
- `c_dengue_01` · `datos_si_pregunta['vómitos']`: «ha vomitado dos veces hoy»
- `c_dengue_01` · `datos_si_pregunta['medicinas']`: «solo ha tomado acetaminofén (Dolex); no ha tomado aspirina ni ibuprofeno»
- `c_erc_01` · `motivo_consulta`: «Cansancio, pies hinchados y orina con espuma desde hace unos meses»
- `c_erc_01` · `sintomas[2]`: «orina con espuma»
- `c_erc_01` · `habitos[0]`: «trabaja al sol muchas horas»
- `c_erc_01` · `habitos[1]`: «toma poca agua durante la jornada»
- `c_erc_01` · `habitos[3]`: «toma diclofenaco casi a diario por dolor de espalda»
- `c_erc_01` · `datos_si_pregunta['dolor de espalda y pastillas']`: «toma diclofenaco casi todos los días porque le duele la espalda del trabajo»
- `c_erc_01` · `datos_si_pregunta['familiares']`: «su papá y un tío murieron de problemas de los riñones»
- `c_erc_01` · `datos_si_pregunta['cantidad de orina']`: «orina menos que antes y se levanta una o dos veces por la noche»
- `c_dm2_01` · `sintomas[1]`: «orina muchas veces, incluso de noche»
- `c_dm2_01` · `sintomas[5]`: «ha bajado unas 5 libras en dos meses aunque come igual»
- `c_dm2_01` · `antecedentes[2]`: «tiene sobrepeso»
- `c_dm2_01` · `habitos[0]`: «toma dos o tres refrescos o gaseosas al día»
- `c_dm2_01` · `habitos[1]`: «come pan dulce y comida frita seguido»
- `c_dm2_01` · `datos_si_pregunta['familiares']`: «a su mamá le descubrieron azúcar en la sangre y toma pastillas»
- `c_dm2_01` · `datos_si_pregunta['dieta']`: «toma dos o tres refrescos al día y le gusta el pan dulce»
- `c_dm2_01` · `datos_si_pregunta['peso']`: «ha bajado como 5 libras en dos meses sin querer»
- … y 32 más

