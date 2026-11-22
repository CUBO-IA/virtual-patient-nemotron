# Auditoría de habla salvadoreña

Generado: 2026-11-21 21:50. Glosario: `data/habla_salvadorena.json` (**borrador, sin validar por hablantes**).

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

## 2. Muestras reales del paciente

- Pacientes simulados: **16** · respuestas: **80**
- Respuestas con vocabulario médico: **0** de 80
- Respuestas que copian frases (5+ palabras) del texto del caso: **68** de 80 (es esperable: el caso es la fuente de los hechos; lo que importa es *cómo* se dicen)
- Respuestas con posible 3.ª persona: **21** de 80

Para el revisor salvadoreño: califica cada respuesta de 1 (no suena salvadoreño) a 5 (suena natural) y anota qué palabra cambiarías.

### c_dengue_01 — Idalia, 29 años (San Vicente Sur, San Vicente, urbano)
_Escolaridad: secundaria · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por fiebre alta y dolor de cabeza desde hace tres días.
  - ℹ Copia literal del caso: «fiebre alta y dolor de…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre viajes?
  - **Paciente (modelo):** No he salido de mi municipio en el último mes.
  - ℹ Copia literal del caso: «municipio en el ultimo mes…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre vecinos o familiares enfermos?
  - **Paciente (modelo):** Dos vecinos tuvieron algo similar la semana pasada y uno fue al hospital.
  - ℹ Copia literal del caso: «la semana pasada y uno…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre sangrado?
  - **Paciente (modelo):** No he tenido sangrado.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre manchas en la piel?
  - **Paciente (modelo):** No me salieron manchas rojas en los brazos.
  - Calificación: __ / 5 · Cambiaría: ____________

### c_dengue_01 — Vicente, 35 años (La Libertad Oeste, La Libertad, urbano)
_Escolaridad: universitario · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por fiebre alta y dolor de cabeza desde hace 3 días.
  - ℹ Copia literal del caso: «fiebre alta y dolor de…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre viajes?
  - **Paciente (modelo):** No ha salido de su municipio en el último mes.
  - ℹ Copia literal del caso: «no ha salido de su…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre vecinos o familiares enfermos?
  - **Paciente (modelo):** Dos vecinos tuvieron lo mismo la semana pasada. Uno fue al hospital.
  - ℹ Copia literal del caso: «dos vecinos tuvieron lo mismo…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre sangrado?
  - **Paciente (modelo):** Ayer le sangraron las encías al cepillarse.
  - ℹ Copia literal del caso: «ayer le sangraron las encias…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre manchas en la piel?
  - **Paciente (modelo):** Hoy le salieron unas manchitas rojas en los brazos.
  - ℹ Copia literal del caso: «hoy le salieron unas manchitas…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_erc_01 — Germán, 28 años (San Salvador Este, San Salvador, urbano)
_Escolaridad: universitario · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por cansancio, pies hinchados y orina con espuma desde hace unos meses.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «cansancio pies hinchados y orina…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dolor de espalda y pastillas?
  - **Paciente (modelo):** Tomo diclofenaco casi a diario porque me duele la espalda del trabajo.
  - ℹ Copia literal del caso: «duele la espalda del trabajo…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre agua?
  - **Paciente (modelo):** En el trabajo casi no tomo agua, solo cuando llego a la casa.
  - ℹ Copia literal del caso: «en el trabajo casi no…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre familiares?
  - **Paciente (modelo):** Mi esposo y mi mamá murieron de problemas de los riñones.
  - ℹ Copia literal del caso: «murieron de problemas de los…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre cantidad de orina?
  - **Paciente (modelo):** Orina menos que antes y me levanto una o dos veces por la noche.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «orina menos que antes y…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_erc_01 — Ignacio, 44 años (San Salvador Centro, San Salvador, urbano)
_Escolaridad: secundaria · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por cansancio, pies hinchados y orina con espuma desde hace algunos meses.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «cansancio pies hinchados y orina…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dolor de espalda y pastillas?
  - **Paciente (modelo):** Toño toma diclofenaco casi a diario por dolor de espalda.
  - ℹ Copia literal del caso: «toma diclofenaco casi a diario…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre agua?
  - **Paciente (modelo):** En el trabajo casi no toma agua, solo cuando llega a la casa.
  - ℹ Copia literal del caso: «en el trabajo casi no…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre familiares?
  - **Paciente (modelo):** Su papá y un tío murieron de problemas de los riñones.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «su papa y un tio…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre cantidad de orina?
  - **Paciente (modelo):** Orina menos que antes y se levanta una o dos veces por la noche.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «orina menos que antes y…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_dm2_01 — Gladis, 56 años (Ahuachapán Centro, Ahuachapán, urbano)
_Escolaridad: ninguno · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Mucha sed, orino muchas veces y he bajado de peso.
  - ℹ Copia literal del caso: «mucha sed orino muchas veces…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre familiares?
  - **Paciente (modelo):** Mi esposo tiene azúcar en la sangre y toma pastillas. Mi mamá le descubrieron azúcar en la sangre.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «azucar en la sangre y…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dieta?
  - **Paciente (modelo):** Tomo dos o tres refrescos o gaseosas al día y le gusta el pan dulce.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «dos o tres refrescos o…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre peso?
  - **Paciente (modelo):** Ha bajado unas 5 libras en dos meses aunque come igual.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «ha bajado unas 5 libras…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre vista?
  - **Paciente (modelo):** A veces ve borroso, sobre todo por la tarde.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «a veces ve borroso sobre…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_dm2_01 — María, 53 años (La Libertad Oeste, La Libertad, urbano)
_Escolaridad: bachillerato · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Mucha sed, orino muchas veces y he bajado de peso.
  - ℹ Copia literal del caso: «mucha sed orino muchas veces…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre familiares?
  - **Paciente (modelo):** Mi esposo le descubrió azúcar en la sangre a mi mamá.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dieta?
  - **Paciente (modelo):** Tomo dos o tres refrescos o gaseosas al día y le gusta el pan dulce.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «dos o tres refrescos o…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre peso?
  - **Paciente (modelo):** Ha bajado unas 5 libras en dos meses aunque come igual.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «ha bajado unas 5 libras…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre vista?
  - **Paciente (modelo):** A veces ve borroso, sobre todo por la tarde.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «a veces ve borroso sobre…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_hta_01 — Luisa, 48 años (La Unión Sur, La Unión, rural)
_Escolaridad: primaria · aspiración de la s: media_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por dolor de cabeza fuerte, como que le late atrás en la nuca; mareos y sensación de inestabilidad al levantarse; zumbido en los oídos como un pito constante; ve como lucecitas; sensación de opresión leve en el pecho y calor en la cara.
  - **Se muestra en pantalla:** Vengo por dolor de cabeza fuerte, como que le late atráj en la nuca; mareoj y sensación de inejtabilidad al levantarse; zumbido en loj oídoj como un pito conjtante; ve como lucecitaj; sensación de opresión leve en el pecho y calor en la cara.
  - ℹ Copia literal del caso: «dolor de cabeza fuerte como…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre pastillas previas?
  - **Paciente (modelo):** Le dijeron hace dos años en la unidad de salud que tenía la tensión alta; le recetaron unas pastillas de 20 miligramos al día, pero se les acabaron y no fui a consulta.
  - **Se muestra en pantalla:** Le dijeron hace doj añoj en la unidad de salud que tenía la tensión alta; le recetaron unaj pajtillaj de 20 miligramoj al día, pero se lej acabaron y no fui a consulta.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «le dijeron hace dos anos…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dolor de pecho?
  - **Paciente (modelo):** Siento una pesadez en el pecho desde que empezó el dolor de cabeza, pero no se me va al brazo.
  - **Se muestra en pantalla:** Siento una pesadez en el pecho dejde que empezó el dolor de cabeza, pero no se me va al brazo.
  - ℹ Copia literal del caso: «una pesadez en el pecho…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre visión?
  - **Paciente (modelo):** Ve lucecitas brillantes cuando se agacha y se levanta rápido.
  - **Se muestra en pantalla:** Ve lucecitaj brillantej cuando se agacha y se levanta rápido.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «ve lucecitas brillantes cuando se…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre orina?
  - **Paciente (modelo):** No ha tenido problemas al orinar ni ha visto sangre.
  - **Se muestra en pantalla:** No ha tenido problemaj al orinar ni ha vijto sangre.
  - ℹ Copia literal del caso: «no ha tenido problemas al…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_hta_01 — Iván, 75 años (San Salvador Oeste, San Salvador, urbano)
_Escolaridad: ninguno · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por dolor de cabeza fuerte en la nuca, mareos y sensación de inestabilidad al levantarme.
  - ℹ Copia literal del caso: «dolor de cabeza fuerte en…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre pastillas previas?
  - **Paciente (modelo):** Hace dos años me dijeron en la unidad de salud que tenía la tensión alta; les recetaron algunas pastillas, pero las dejé de tomar hace dos meses porque me sentía bien.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «en la unidad de salud…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dolor de pecho?
  - **Paciente (modelo):** Siento una pesadez en el pecho desde que empezó el dolor de cabeza, pero no se le va al brazo.
  - ℹ Copia literal del caso: «una pesadez en el pecho…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre visión?
  - **Paciente (modelo):** Ve lucecitas brillantes cuando me agacho y me levanto rápido.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre orina?
  - **Paciente (modelo):** No me ha bajado orina ni he visto sangre.
  - Calificación: __ / 5 · Cambiaría: ____________

### c_trauma_01 — Alberto, 26 años (Ahuachapán Sur, Ahuachapán, rural)
_Escolaridad: primaria · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por choque en moto hace dos horas y dolor fuerte en hombro derecho, pierna y algunas costillas.
  - ℹ Copia literal del caso: «moto hace dos horas y…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre casco y golpe en cabeza?
  - **Paciente (modelo):** Llevaba casco pero se le salió al caer; se pegó un raspón en la frente pero no perdió el conocimiento.
  - ℹ Copia literal del caso: «llevaba casco pero se le…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre velocidad y choque?
  - **Paciente (modelo):** Iba como a 40 por hora y un carro se le atravesó; cayó sobre el lado derecho.
  - ℹ Copia literal del caso: «iba como a 40 por…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre respiración y pecho?
  - **Paciente (modelo):** Le duele al tomar aire hondo en las costillas del lado derecho.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «le duele al tomar aire…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre cuello y columna?
  - **Paciente (modelo):** No siento dolor en el cuello ni en la espalda, solo en el hombro y las costillas.
  - ℹ Copia literal del caso: «dolor en el cuello ni…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_trauma_01 — Ana, 30 años (San Vicente Sur, San Vicente, rural)
_Escolaridad: bachillerato · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por un choque en moto hace dos horas. Me duele fuerte el hombro derecho y la rodilla. También hay un raspón en la frente, pero no perdí el conocimiento. Le duele al tomar aire hondo en las costillas del lado derecho.
  - ℹ Copia literal del caso: «me duele fuerte el hombro…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre casco y golpe en cabeza?
  - **Paciente (modelo):** Llevaba casco pero se le salió al caer. Se pegó un raspón en la frente, pero no perdí el conocimiento.
  - ℹ Copia literal del caso: «llevaba casco pero se le…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre velocidad y choque?
  - **Paciente (modelo):** Iba como a 40 por hora y un carro se le atravesó, cayó sobre el lado derecho.
  - ℹ Copia literal del caso: «iba como a 40 por…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre respiración y pecho?
  - **Paciente (modelo):** Le duele al tomar aire hondo en las costillas del lado derecho.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «le duele al tomar aire…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre cuello y columna?
  - **Paciente (modelo):** No siento dolor en el cuello ni en la espalda, solo en el hombro y las costillas.
  - ℹ Copia literal del caso: «dolor en el cuello ni…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_gea_01 — Rina, 38 años (Usulután Este, Usulután, rural)
_Escolaridad: secundaria · aspiración de la s: media_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por que llevo dos días con diarrea líquida, cólicos fuertes y vómitos.
  - **Se muestra en pantalla:** Vengo por que llevo doj díaj con diarrea líquida, cólicoj fuertej y vómitoj.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre alimentos recientes?
  - **Paciente (modelo):** El día que empezó a sentirme mal, el día antes, comí pupusas y curtido en un puesto de la calle que me daba mal al olor.
  - **Se muestra en pantalla:** El día que empezó a sentirme mal, el día antej, comí pupusaj y curtido en un puejto de la calle que me daba mal al olor.
  - ℹ Copia literal del caso: «pupusas y curtido en un…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre características de las heces?
  - **Paciente (modelo):** Son completamente líquidas, amarillentas, sin moco ni sangre visible.
  - **Se muestra en pantalla:** Son completamente líquidaj, amarillentaj, sin moco ni sangre visible.
  - ℹ Copia literal del caso: «son completamente liquidas amarillentas sin…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre orina y sed?
  - **Paciente (modelo):** Ahorita le cuesta retener agua, la devuelve casi de inmediato. Ha orinado una sola vez en el día, y la orina salió bien oscura.
  - **Se muestra en pantalla:** Ahorita le cuejta retener agua, la devuelve casi de inmediato. Ha orinado una sola vez en el día, y la orina salió bien ojcura.
  - ℹ Copia literal del caso: «ahorita le cuesta retener agua…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre fiebre?
  - **Paciente (modelo):** Ayer tuve calentura, pero no me puse termómetro.
  - **Se muestra en pantalla:** Ayer tuve calentura, pero no me puse termómetro.
  - Calificación: __ / 5 · Cambiaría: ____________

### c_gea_01 — Alexander, 60 años (Santa Ana Oeste, Santa Ana, urbano)
_Escolaridad: primaria · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por que llevo dos días con bastante diarrea líquida, cólicos y vómitos.
  - ℹ Copia literal del caso: «llevo dos dias con bastante…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre alimentos recientes?
  - **Paciente (modelo):** El día que empezó comió pupusas con curtido en la calle que sintió con olor raro.
  - ℹ Copia literal del caso: «el dia que empezo comio…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre características de las heces?
  - **Paciente (modelo):** Son completamente líquidas, amarillentas, sin moco ni sangre visible.
  - ℹ Copia literal del caso: «son completamente liquidas amarillentas sin…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre orina y sed?
  - **Paciente (modelo):** Ha orinado solo una vez en todo el día y la orina salió bien oscura. Ahorita le cuesta retener agua, la devuelve casi de inmediato.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «ha orinado solo una vez…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre fiebre?
  - **Paciente (modelo):** Ayer sintió calentura pero no se puso termómetro.
  - ℹ Copia literal del caso: «pero no se puso termometro…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_nac_01 — Ángeles, 86 años (La Paz Oeste, La Paz, rural)
_Escolaridad: ninguno · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por tos con flema amarillenta, calentura y no me entra aire caminando un poco.
  - ℹ Copia literal del caso: «tos con flema amarillenta calentura…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre flema y sangre?
  - **Paciente (modelo):** La flema es espesa y amarilla oscura, ayer vio como hilitos de sangre pero poquito.
  - ℹ Copia literal del caso: «la flema es espesa y…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dolor de costado?
  - **Paciente (modelo):** Me duele como si le clavaran una aguja en el lado derecho de la espalda cuando toco o respiro hondo.
  - ℹ Copia literal del caso: «duele como si le clavaran…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre fiebre?
  - **Paciente (modelo):** Ayer le subió como a 38.5 y le castañeteaban los dientes del frío.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «le subio como a 38…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre humo de leña?
  - **Paciente (modelo):** Desde tierna cociné en poyo de leña sin chimenea adentro de la casa.
  - ℹ Copia literal del caso: «en poyo de lena sin…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_nac_01 — Mario, 57 años (San Salvador Este, San Salvador, urbano)
_Escolaridad: universitario · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por tos con flema amarillenta, calentura y dificultad para respirar desde hace cuatro días. También me duele el lado derecho de la espalda cuando toso. Ayer subió mi fiebre a 38.5 y me castañeteaban los dientes del frío. Y desde que cociné con leña, se acumulan humo en la casa.
  - ℹ Copia literal del caso: «tos con flema amarillenta calentura…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre flema y sangre?
  - **Paciente (modelo):** La flema es espesa y amarilla oscura, ayer vi como hilitos de sangre, pero no mucho.
  - ℹ Copia literal del caso: «la flema es espesa y…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dolor de costado?
  - **Paciente (modelo):** Le duele como si le clavaran una aguja en el lado derecho de la espalda cuando toso.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «le duele como si le…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre fiebre?
  - **Paciente (modelo):** Anoche subió mi fiebre a 38.5 y me castañeteaban los dientes del frío.
  - ℹ Copia literal del caso: «castaneteaban los dientes del frio…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre humo de leña?
  - **Paciente (modelo):** Desde tierna edad cociné con leña en cocina cerrada sin chimenea.
  - Calificación: __ / 5 · Cambiaría: ____________

### c_depresion_01 — Iván, 75 años (San Salvador Oeste, San Salvador, urbano)
_Escolaridad: ninguno · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por que no puedo dormir ni tampoco comer bien, me duermo a las 9 y me despierto a las 3 o 4, y no me apetece hacer nada.
  - ℹ Copia literal del caso: «a las 3 o 4…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre ideas de muerte o autolesion?
  - **Paciente (modelo):** A veces he pensado que mejor quisiera dormirme y no despertar, pero nunca me he animado a hacerlo.
  - ℹ Copia literal del caso: «y no despertar pero nunca…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre duelo y pérdida?
  - **Paciente (modelo):** Desde que murió mi esposo, me siento como si la casa estuviera vacía y no tengo propósito.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre sueño?
  - **Paciente (modelo):** Me acuesto a las 9, pero me duermo hasta las 3 o 4 y no puedo volver a dormirme.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre alimentación?
  - **Paciente (modelo):** Pues la comida no me sabe a nada, solo me sirvo de unas tortillas con queso.
  - Calificación: __ / 5 · Cambiaría: ____________

### c_depresion_01 — José, 41 años (Chalatenango Sur, Chalatenango, urbano)
_Escolaridad: bachillerato · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por que paso sin ganas de nada, no puedo dormir y lloro a cada rato desde hace un mes.
  - ℹ Copia literal del caso: «paso sin ganas de nada…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre ideas de muerte o autolesion?
  - **Paciente (modelo):** A veces he pensado que mejor quisiera dormir y no despertar, pero nunca he intentado hacerme daño.
  - ℹ Copia literal del caso: «y no despertar pero nunca…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre duelo y pérdida?
  - **Paciente (modelo):** Desde que murió mi esposo siento que la casa está vacía y que no tengo propósito.
  - ℹ Copia literal del caso: «que la casa esta vacia…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre sueño?
  - **Paciente (modelo):** Se acuesto a las 9 pero me duermo hasta las 1, y me despierto a las 3 o 4 sin poder volver a dormir.
  - ℹ Copia literal del caso: «a las 3 o 4…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre alimentación?
  - **Paciente (modelo):** La comida no me gusta, solo me sirvo unas tortillas con queso por obligación.
  - Calificación: __ / 5 · Cambiaría: ____________

