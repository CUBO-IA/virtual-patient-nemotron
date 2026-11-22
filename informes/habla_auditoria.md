# Auditoría de habla salvadoreña

Generado: 2026-11-21 20:39. Glosario: `data/habla_salvadorena.json` (**borrador, sin validar por hablantes**).

## 1. Auditoría de datos (casos)

- Casos revisados: **8**
- Términos a evitar en lo que el paciente dice o copia: **1**
- Temas (claves de `datos_si_pregunta`) con vocabulario técnico: **1** (entran al prompt como «Si te preguntan por…»)

### Errores

- `c_gea_01` · `sintomas[0]`: «deposiciones líquidas como seis o siete veces al día» → contiene **deposicion**. Alternativas: «diarrea», «cursera», «ir al baño a cada rato»

### Avisos (temas)

- `c_gea_01` · tema 'características de las heces' → **heces**. Alternativas: «ir al baño», «lo que sale al hacer del baño», «las heces negras»

### Redacción en tercera persona

**52 de 155** textos del paciente (33 %) parecen estar escritos en 3.ª persona (heurística). El modelo los repite como un narrador («ha bajado unas 5 libras», «le duele al tomar aire»).

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
- Respuestas con vocabulario médico: **2** de 80
- Respuestas que copian frases (5+ palabras) del texto del caso: **67** de 80 (es esperable: el caso es la fuente de los hechos; lo que importa es *cómo* se dicen)
- Respuestas con posible 3.ª persona: **7** de 80

Para el revisor salvadoreño: califica cada respuesta de 1 (no suena salvadoreño) a 5 (suena natural) y anota qué palabra cambiarías.

### c_dengue_01 — Víctor, 20 años (Cabañas Este, Cabañas, rural)
_Escolaridad: secundaria · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por calentura alta y dolor de cabeza.
  - ℹ Copia literal del caso: «alta y dolor de cabeza…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre viajes?
  - **Paciente (modelo):** No he salido de mi municipio en el último mes.
  - ℹ Copia literal del caso: «municipio en el ultimo mes…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre vecinos o familiares enfermos?
  - **Paciente (modelo):** Mis vecinos han tenido lo mismo la semana pasada y uno fue al hospital.
  - ℹ Copia literal del caso: «lo mismo la semana pasada…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre sangrado?
  - **Paciente (modelo):** Ayer me sangraron las encías al cepillarme los dientes.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre manchas en la piel?
  - **Paciente (modelo):** Hoy me salieron unas manchitas rojas en los brazos.
  - ℹ Copia literal del caso: «salieron unas manchitas rojas en…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_dengue_01 — Beatriz, 39 años (San Salvador Centro, San Salvador, urbano)
_Escolaridad: universitario · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por que tengo calentura alta y me duele la cabeza desde hace tres días.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre viajes?
  - **Paciente (modelo):** No he salido de mi municipio en el último mes.
  - ℹ Copia literal del caso: «municipio en el ultimo mes…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre vecinos o familiares enfermos?
  - **Paciente (modelo):** Mis vecinos tuvieron lo mismo la semana pasada y uno fue al hospital.
  - ℹ Copia literal del caso: «vecinos tuvieron lo mismo la…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre sangrado?
  - **Paciente (modelo):** Ayer me sangraron las encías al cepillarme los dientes.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre manchas en la piel?
  - **Paciente (modelo):** Hoy me salieron unas manchitas rojas en los brazos.
  - ℹ Copia literal del caso: «salieron unas manchitas rojas en…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_erc_01 — José, 25 años (San Salvador Centro, San Salvador, urbano)
_Escolaridad: tecnico · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por mucho cansancio, los pies se me hinchan al final del día y la orina con espuma desde hace unos meses.
  - ℹ Copia literal del caso: «hinchan al final del dia…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dolor de espalda y pastillas?
  - **Paciente (modelo):** Tomo diclofenaco casi todos los días porque me duele la espalda del trabajo.
  - ℹ Copia literal del caso: «diclofenaco casi todos los dias…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre agua?
  - **Paciente (modelo):** En el trabajo casi no tomo agua, solo cuando llego a casa.
  - ℹ Copia literal del caso: «en el trabajo casi no…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre familiares?
  - **Paciente (modelo):** Mi papá y un tío murieron de problemas de los riñones.
  - ℹ Copia literal del caso: «papa y un tio murieron…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre cantidad de orina?
  - **Paciente (modelo):** Orino menos que antes y me levanto una o dos veces por la noche.
  - ℹ Copia literal del caso: «una o dos veces por…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_erc_01 — Mario, 33 años (San Salvador Oeste, San Salvador, urbano)
_Escolaridad: ninguno · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por mucho cansancio, los pies me hinchan y la orina me sale espumosa.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dolor de espalda y pastillas?
  - **Paciente (modelo):** Tomo diclofenaco casi todos los días porque me duele la espalda del trabajo.
  - ℹ Copia literal del caso: «diclofenaco casi todos los dias…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre agua?
  - **Paciente (modelo):** En el trabajo casi no tomo agua, solo cuando llego a casa.
  - ℹ Copia literal del caso: «en el trabajo casi no…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre familiares?
  - **Paciente (modelo):** Mi papá y un tío murieron de problemas de los riñones.
  - ℹ Copia literal del caso: «papa y un tio murieron…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre cantidad de orina?
  - **Paciente (modelo):** Orino menos que antes y me levanto una o dos veces por la noche.
  - ℹ Copia literal del caso: «una o dos veces por…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_dm2_01 — René, 69 años (Santa Ana Oeste, Santa Ana, urbano)
_Escolaridad: primaria · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por mucha sed todo el día y orino muchas veces, incluso de noche.
  - ℹ Copia literal del caso: «mucha sed todo el dia…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre familiares?
  - **Paciente (modelo):** Mi mamá le descubrieron azúcar en la sangre y toma pastillas.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «mama le descubrieron azucar en…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dieta?
  - **Paciente (modelo):** Tomo dos o tres refrescos al día y le gusta el pan dulce.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «dos o tres refrescos al…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre peso?
  - **Paciente (modelo):** Ha bajado como 5 libras en dos meses sin querer.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «ha bajado como 5 libras…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre vista?
  - **Paciente (modelo):** A veces ve borroso, sobre todo por la tarde.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «a veces ve borroso sobre…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_dm2_01 — Carolina, 73 años (La Paz Centro, La Paz, urbano)
_Escolaridad: primaria · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por mucho sed, orino muchas veces y he bajado de peso en dos meses.
  - ℹ Copia literal del caso: «sed orino muchas veces y…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre familiares?
  - **Paciente (modelo):** Mi mamá le descubrieron azúcar en la sangre y toma pastillas.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «mama le descubrieron azucar en…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dieta?
  - **Paciente (modelo):** Tomo dos o tres refrescos al día y me gusta el pan dulce.
  - ℹ Copia literal del caso: «dos o tres refrescos al…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre peso?
  - **Paciente (modelo):** Ha bajado como 5 libras en dos meses sin querer.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «ha bajado como 5 libras…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre vista?
  - **Paciente (modelo):** A veces ve borroso, sobre todo por la tarde.
  - ⚠ Posible 3.ª persona (suena a narrador, no al paciente)
  - ℹ Copia literal del caso: «a veces ve borroso sobre…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_hta_01 — Gladis, 56 años (Ahuachapán Centro, Ahuachapán, urbano)
_Escolaridad: ninguno · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Buenas tardes, vengo por dolor de cabeza fuerte en la nuca y mareos desde esta mañana.
  - ℹ Copia literal del caso: «dolor de cabeza fuerte en…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre pastillas previas?
  - **Paciente (modelo):** Sí, me habían dejado enalapril de 20 miligramos al día, pero se me acabaron y no fui a la consulta.
  - ℹ Copia literal del caso: «habian dejado enalapril de 20…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dolor de pecho?
  - **Paciente (modelo):** Siento una pesadez en el pecho desde que empezó el dolor de cabeza, pero no se me va al brazo.
  - ℹ Copia literal del caso: «una pesadez en el pecho…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre visión?
  - **Paciente (modelo):** Cuando me agacho y me levanto rápido veo lucecitas brillantes.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre orina?
  - **Paciente (modelo):** No he tenido problemas al orinar ni he visto sangre.
  - ℹ Copia literal del caso: «tenido problemas al orinar ni…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_hta_01 — María, 53 años (La Libertad Oeste, La Libertad, urbano)
_Escolaridad: bachillerato · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por un dolor de cabeza fuerte en la nuca y mareos desde esta mañana.
  - ℹ Copia literal del caso: «dolor de cabeza fuerte en…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre pastillas previas?
  - **Paciente (modelo):** Tengo pastillas para la tensión alta, pero las dejé de tomar hace dos meses porque me sentía bien. Me dieron enalapril de 20 miligramos al día, pero ya se me acabaron y no fui a consulta.
  - ℹ Copia literal del caso: «de tomar hace dos meses…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dolor de pecho?
  - **Paciente (modelo):** Siento una pesadez en el pecho desde que empezó el dolor de cabeza, pero no se le va al brazo. No es un dolor fuerte, pero no se le va.
  - ℹ Copia literal del caso: «una pesadez en el pecho…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre visión?
  - **Paciente (modelo):** Cuando me agacho y me levanto rápido, veo lucecitas brillantes. La visión no me parece borrosa todo el tiempo.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre orina?
  - **Paciente (modelo):** No he tenido problemas al orinar ni he visto sangre en la orina.
  - ℹ Copia literal del caso: «tenido problemas al orinar ni…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_trauma_01 — Manuel, 29 años (San Salvador Sur, San Salvador, urbano)
_Escolaridad: secundaria · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Buenas tardes, vengo por que me duele fuerte el hombro derecho y la rodilla derecha.
  - ℹ Copia literal del caso: «me duele fuerte el hombro…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre casco y golpe en cabeza?
  - **Paciente (modelo):** Llevaba casco, pero cuando caí se me salió; me pegué un raspón en la frente, pero no perdí el conocimiento.
  - ℹ Copia literal del caso: «un raspon en la frente…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre velocidad y choque?
  - **Paciente (modelo):** Iba a unos 40 por hora y de repente un carro se me atravesó, cayó sobre el lado derecho.
  - ℹ Copia literal del caso: «atraveso cayo sobre el lado…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre respiración y pecho?
  - **Paciente (modelo):** Me duele al tomar aire hondo en las costillas del lado derecho.
  - ℹ Copia literal del caso: «duele al tomar aire hondo…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre cuello y columna?
  - **Paciente (modelo):** No siento dolor en el cuello ni en la espalda, solo en el hombro y las costillas.
  - ℹ Copia literal del caso: «dolor en el cuello ni…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_trauma_01 — Víctor, 20 años (Cabañas Este, Cabañas, rural)
_Escolaridad: secundaria · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Buenas tardes, vengo por que me dio un choque en moto y me duele mucho el hombro y la rodilla.
  - ℹ Copia literal del caso: «el hombro y la rodilla…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre casco y golpe en cabeza?
  - **Paciente (modelo):** Tengo casco, pero se me salió al caer. Me pegué un raspón en la frente, pero no me desmayé.
  - ℹ Copia literal del caso: «un raspon en la frente…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre velocidad y choque?
  - **Paciente (modelo):** Iba como a 40 por hora y un carro se me atravesó, cayó sobre el lado derecho.
  - ℹ Copia literal del caso: «iba como a 40 por…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre respiración y pecho?
  - **Paciente (modelo):** Me duele al respirar hondo en las costillas del lado derecho.
  - ℹ Copia literal del caso: «hondo en las costillas del…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre cuello y columna?
  - **Paciente (modelo):** No siento dolor en el cuello ni en la espalda, solo en el hombro y las costillas.
  - ℹ Copia literal del caso: «dolor en el cuello ni…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_gea_01 — Beatriz, 64 años (La Unión Norte, La Unión, rural)
_Escolaridad: primaria · aspiración de la s: media_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Buenas tardes, vengo por que llevo dos días con mucha diarrea, cólicos fuertes en la panza y vómitos.
  - **Se muestra en pantalla:** Buenaj tardej, vengo por que llevo doj díaj con mucha diarrea, cólicoj fuertej en la panza y vómitoj.
  - ℹ Copia literal del caso: «colicos fuertes en la panza…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre alimentos recientes?
  - **Paciente (modelo):** El día que empezó la diarrea comí pupusas con curtido en la calle que sentí con olor raro.
  - **Se muestra en pantalla:** El día que empezó la diarrea comí pupusaj con curtido en la calle que sentí con olor raro.
  - ℹ Copia literal del caso: «pupusas con curtido en la…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre características de las heces?
  - **Paciente (modelo):** Mis heces son completamente líquidas, amarillentas. No noto moco ni sangre.
  - **Se muestra en pantalla:** Mij hecej son completamente líquidaj, amarillentaj. No noto moco ni sangre.
  - ⚠ Vocabulario médico: **heces** → «ir al baño», «lo que sale al hacer del baño», «las heces negras»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre orina y sed?
  - **Paciente (modelo):** He orinado solo una vez en todo el día y la orina salió bien oscura. Siento mucha resequedad en la boca y mucha sed.
  - **Se muestra en pantalla:** He orinado solo una vez en todo el día y la orina salió bien ojcura. Siento mucha resequedad en la boca y mucha sed.
  - ℹ Copia literal del caso: «orinado solo una vez en…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre fiebre?
  - **Paciente (modelo):** Anoche sentí calentura pero no me puse termómetro para saber si tenía fiebre.
  - **Se muestra en pantalla:** Anoche sentí calentura pero no me puse termómetro para saber si tenía fiebre.
  - Calificación: __ / 5 · Cambiaría: ____________

### c_gea_01 — Yeny, 44 años (San Salvador Norte, San Salvador, rural)
_Escolaridad: primaria · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por que llevo dos días con diarrea líquida, cólicos y vómitos.
  - ℹ Copia literal del caso: «diarrea liquida colicos y vomitos…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre alimentos recientes?
  - **Paciente (modelo):** El día que empezó comí pupusas con curtido en la calle que sentí que olía raro.
  - ℹ Copia literal del caso: «pupusas con curtido en la…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre características de las heces?
  - **Paciente (modelo):** Mis heces son completamente líquidas, amarillentas, sin moco ni sangre.
  - ⚠ Vocabulario médico: **heces** → «ir al baño», «lo que sale al hacer del baño», «las heces negras»
  - ℹ Copia literal del caso: «son completamente liquidas amarillentas sin…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre orina y sed?
  - **Paciente (modelo):** He orinado solo una vez en todo el día y la orina salió bien oscura. La sed es mucho, me siento reseca.
  - ℹ Copia literal del caso: «orinado solo una vez en…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre fiebre?
  - **Paciente (modelo):** Siento calentura, aunque no me puse termómetro.
  - Calificación: __ / 5 · Cambiaría: ____________

### c_nac_01 — Alexandra, 58 años (Santa Ana Norte, Santa Ana, rural)
_Escolaridad: primaria · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por una tos con flema amarillenta que ya dura cuatro días y me duele la espalda al toser.
  - ℹ Copia literal del caso: «una tos con flema amarillenta…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre flema y sangre?
  - **Paciente (modelo):** Tengo flema bastante espesa que es amarilla oscura y ayer noté que había un poco de sangre, como hilitos pequeños.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dolor de costado?
  - **Paciente (modelo):** Me duele la espalda como si me clavaran una aguja en el lado derecho cuando toso o respiro hondo.
  - ℹ Copia literal del caso: «clavaran una aguja en el…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre fiebre?
  - **Paciente (modelo):** Anoche la fiebre me subió a casi 38.5 y me castañeteaban los dientes.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre humo de leña?
  - **Paciente (modelo):** Desde niña cociné en poyo de leña sin chimenea dentro de la casa y ahora me preocupa eso con la tos.
  - ℹ Copia literal del caso: «en poyo de lena sin…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_nac_01 — Beatriz, 54 años (Sonsonate Este, Sonsonate, urbano)
_Escolaridad: ninguno · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por una tos con flema amarillenta y me cuesta respirar desde hace cuatro días.
  - ℹ Copia literal del caso: «una tos con flema amarillenta…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre flema y sangre?
  - **Paciente (modelo):** La flema es espesa y amarilla oscura, y ayer noté que había un poco de sangre, como hilitos pequeños.
  - ℹ Copia literal del caso: «la flema es espesa y…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dolor de costado?
  - **Paciente (modelo):** Me duele como si le clavaran una aguja en el lado derecho de la espalda cuando toso o respiro hondo.
  - ℹ Copia literal del caso: «duele como si le clavaran…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre fiebre?
  - **Paciente (modelo):** Anoche me subió la fiebre a 38.5 y me castañeteaban los dientes.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre humo de leña?
  - **Paciente (modelo):** Desde niña cociné en poyo de leña sin chimenea adentro de la casa.
  - ℹ Copia literal del caso: «en poyo de lena sin…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_depresion_01 — Diana, 73 años (San Salvador Centro, San Salvador, urbano)
_Escolaridad: ninguno · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por que paso sin ganas de nada, no puedo dormir y lloro a cada rato desde hace un mes.
  - ℹ Copia literal del caso: «paso sin ganas de nada…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre ideas de muerte o autolesion?
  - **Paciente (modelo):** A veces he pensado que mejor quisiera dormirse y no despertar, pero nunca he intentado hacerme daño.
  - ℹ Copia literal del caso: «pensado que mejor quisiera dormirse…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre duelo y pérdida?
  - **Paciente (modelo):** Desde que murió mi compañero de vida, siento que la casa está vacía y que no tengo ningún propósito.
  - ℹ Copia literal del caso: «que la casa esta vacia…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre sueño?
  - **Paciente (modelo):** Me acuesto a las 9 pero me duerme hasta la 1, y me despierto a las 3 o 4 sin poder volver a dormir.
  - ℹ Copia literal del caso: «duerme hasta la 1 y…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre alimentación?
  - **Paciente (modelo):** La comida no me saboriza nada, como solo por obligación unas tortillas con queso.
  - ℹ Copia literal del caso: «solo por obligacion unas tortillas…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_depresion_01 — Carmen, 40 años (San Salvador Centro, San Salvador, urbano)
_Escolaridad: posgrado · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Vengo por que paso sin ganas de nada, no puedo dormir bien y lloro a cada rato desde hace un mes.
  - ℹ Copia literal del caso: «paso sin ganas de nada…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre ideas de muerte o autolesion?
  - **Paciente (modelo):** A veces pienso que mejor quisiera dormirme y no despertar, pero nunca he intentado hacerme daño.
  - ℹ Copia literal del caso: «y no despertar pero nunca…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre duelo y pérdida?
  - **Paciente (modelo):** Desde que murió mi compañero de vida, siento que la casa está vacía y que no tengo ningún propósito.
  - ℹ Copia literal del caso: «que la casa esta vacia…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre sueño?
  - **Paciente (modelo):** Me acuesto a las nueve pero me duerme hasta la una, y me despierto a las tres o cuatro sin poder volver a dormir.
  - ℹ Copia literal del caso: «sin poder volver a dormir…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre alimentación?
  - **Paciente (modelo):** La comida no me sabe a nada, solo como unas tortillas con queso por obligación.
  - Calificación: __ / 5 · Cambiaría: ____________

