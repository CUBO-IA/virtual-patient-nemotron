# Auditoría de habla salvadoreña

Generado: 2026-11-21 20:29. Glosario: `data/habla_salvadorena.json` (**borrador, sin validar por hablantes**).

## 1. Auditoría de datos (casos)

- Casos revisados: **8**
- Términos a evitar en lo que el paciente dice o copia: **1**
- Temas (claves de `datos_si_pregunta`) con vocabulario técnico: **1** (entran al prompt como «Si te preguntan por…»)

### Errores

- `c_gea_01` · `sintomas[0]`: «deposiciones líquidas como seis o siete veces al día» → contiene **deposicion**. Alternativas: «diarrea», «cursera», «ir al baño a cada rato»

### Avisos (temas)

- `c_gea_01` · tema 'características de las heces' → **heces**. Alternativas: «ir al baño», «lo que sale al hacer del baño», «las heces negras»

## 2. Muestras reales del paciente

- Pacientes simulados: **8** · respuestas: **40**
- Respuestas con vocabulario médico: **1** de 40
- Respuestas que copian frases (5+ palabras) del texto del caso: **33** de 40

Para el revisor salvadoreño: califica cada respuesta de 1 (no suena salvadoreño) a 5 (suena natural) y anota qué palabra cambiarías.

### c_dengue_01 — Beatriz, 54 años (Sonsonate Este, Sonsonate, urbano)
_Escolaridad: ninguno · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Buenas tardes, doctor. Venía porque tengo calentura alta y dolor de cabeza desde hace tres días.
  - ⚠ Copia literal del caso: «alta y dolor de cabeza…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre viajes?
  - **Paciente (modelo):** No he salido de mi municipio en el último mes, doctor.
  - ⚠ Copia literal del caso: «municipio en el ultimo mes…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre vecinos o familiares enfermos?
  - **Paciente (modelo):** Sí, doctor, dos vecinos tuvieron lo mismo la semana pasada y uno fue al hospital.
  - ⚠ Copia literal del caso: «dos vecinos tuvieron lo mismo…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre sangrado?
  - **Paciente (modelo):** Ahorita le sangraron las encías al cepillarme los dientes, doctor.
  - ⚠ Copia literal del caso: «le sangraron las encias al…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre manchas en la piel?
  - **Paciente (modelo):** Hoy le salieron unas manchitas rojas en los brazos, doctor.
  - ⚠ Copia literal del caso: «hoy le salieron unas manchitas…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_erc_01 — Héctor, 55 años (San Salvador Este, San Salvador, urbano)
_Escolaridad: primaria · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Buenas tardes, doctor. Me trae el cansancio, los pies que se me hinchan al final del día y la orina con espuma.
  - ⚠ Copia literal del caso: «hinchan al final del dia…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dolor de espalda y pastillas?
  - **Paciente (modelo):** Sí, doctor. Me duele la espalda del trabajo y tomo diclofenaco casi todos los días porque me duele.
  - ⚠ Copia literal del caso: «duele la espalda del trabajo…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre agua?
  - **Paciente (modelo):** En el trabajo, casi no tomo agua, solo cuando llego a casa.
  - ⚠ Copia literal del caso: «en el trabajo casi no…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre familiares?
  - **Paciente (modelo):** Mi papá y un tío murieron de problemas de los riñones, doctor.
  - ⚠ Copia literal del caso: «papa y un tio murieron…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre cantidad de orina?
  - **Paciente (modelo):** Orino menos que antes y me levanto una o dos veces por la noche.
  - ⚠ Copia literal del caso: «una o dos veces por…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_dm2_01 — Ignacio, 44 años (San Salvador Centro, San Salvador, urbano)
_Escolaridad: secundaria · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Buenas tardes, doctor. Me trae la mucha sed que tengo todo el día y que orino muchas veces, incluso de noche. También noté que bajé de peso en los últimos dos meses.
  - ⚠ Copia literal del caso: «muchas veces incluso de noche…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre familiares?
  - **Paciente (modelo):** Sí, doctor. A mi mamá le descubrieron azúcar en la sangre y toma pastillas.
  - ⚠ Copia literal del caso: «mama le descubrieron azucar en…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dieta?
  - **Paciente (modelo):** Tomo dos o tres refrescos al día y me gusta el pan dulce, doctor.
  - ⚠ Copia literal del caso: «dos o tres refrescos al…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre peso?
  - **Paciente (modelo):** Ha bajado unas 5 libras en los últimos dos meses aunque comía igual, doctor.
  - ⚠ Copia literal del caso: «ha bajado unas 5 libras…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre vista?
  - **Paciente (modelo):** A veces ve borroso, sobre todo por la tarde, doctor.
  - ⚠ Copia literal del caso: «a veces ve borroso sobre…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_hta_01 — Violeta, 52 años (San Miguel Oeste, San Miguel, rural)
_Escolaridad: secundaria · aspiración de la s: media_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Buenas tardes, doctor. Me trae un dolor de cabeza fuerte en la nuca y mareos.
  - **Se muestra en pantalla:** Buenaj tardej, doctor. Me trae un dolor de cabeza fuerte en la nuca y mareoj.
  - ⚠ Copia literal del caso: «dolor de cabeza fuerte en…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre pastillas previas?
  - **Paciente (modelo):** Le habían dejado enalapril de 20 miligramos al día, pero me acabaron y no fui a la consulta.
  - **Se muestra en pantalla:** Le habían dejado enalapril de 20 miligramoj al día, pero me acabaron y no fui a la consulta.
  - ⚠ Copia literal del caso: «le habian dejado enalapril de…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dolor de pecho?
  - **Paciente (modelo):** Siento una pesadez en el pecho desde que empezó el dolor de cabeza, pero no se me va al brazo.
  - **Se muestra en pantalla:** Siento una pesadez en el pecho dejde que empezó el dolor de cabeza, pero no se me va al brazo.
  - ⚠ Copia literal del caso: «una pesadez en el pecho…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre visión?
  - **Paciente (modelo):** Cuando me agacho y me levanto rápido, veo lucecitas brillantes. La vista se vuelve borrosa de vez en cuando.
  - **Se muestra en pantalla:** Cuando me agacho y me levanto rápido, veo lucecitaj brillantej. La vijta se vuelve borrosa de vez en cuando.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre orina?
  - **Paciente (modelo):** No he tenido problemas al orinar ni he visto sangre.
  - **Se muestra en pantalla:** No he tenido problemaj al orinar ni he vijto sangre.
  - ⚠ Copia literal del caso: «tenido problemas al orinar ni…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_trauma_01 — Yamileth, 18 años (La Libertad Costa, La Libertad, urbano)
_Escolaridad: bachillerato · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Buenas tardes, doctor. Choqué en la moto hace dos horas y me duele mucho el hombro y la rodilla.
  - ⚠ Copia literal del caso: «choque en la moto hace…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre casco y golpe en cabeza?
  - **Paciente (modelo):** Le dije a mi hijo: vos andá con casco, pero se me salió al caer y me pegué un raspón en la frente. No perdí el conocimiento.
  - ⚠ Copia literal del caso: «un raspon en la frente…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre velocidad y choque?
  - **Paciente (modelo):** Iba como a 40 por hora y un carro se me atravesó, cayó sobre el lado derecho.
  - ⚠ Copia literal del caso: «iba como a 40 por…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre respiración y pecho?
  - **Paciente (modelo):** Le duele al tomar aire hondo en las costillas del lado derecho.
  - ⚠ Copia literal del caso: «le duele al tomar aire…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre cuello y columna?
  - **Paciente (modelo):** No siento dolor en el cuello ni en la espalda, solo en el hombro y las costillas.
  - ⚠ Copia literal del caso: «dolor en el cuello ni…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_gea_01 — Rosa, 24 años (La Libertad Centro, La Libertad, urbano)
_Escolaridad: bachillerato · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Buenas tardes, doctor. Llevo dos días con mucha diarrea, cólicos fuertes en la panza y vómitos.
  - ⚠ Copia literal del caso: «colicos fuertes en la panza…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre alimentos recientes?
  - **Paciente (modelo):** El día que empezó noté que las pupusas y el curtido que comí en la calle tenían un olor raro.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre características de las heces?
  - **Paciente (modelo):** Mis heces son completamente líquidas, amarillentas, no tienen moco ni sangre.
  - ⚠ Vocabulario médico: **heces** → «ir al baño», «lo que sale al hacer del baño», «las heces negras»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre orina y sed?
  - **Paciente (modelo):** Hoy he orinado solo una vez y la orina salió oscura. La verdad, la sed me tiene derrumbada.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre fiebre?
  - **Paciente (modelo):** Sí, anoche sentí que me subía el calor, pero no me tomé un termómetro.
  - Calificación: __ / 5 · Cambiaría: ____________

### c_nac_01 — Medardo, 60 años (Sonsonate Este, Sonsonate, urbano)
_Escolaridad: secundaria · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Buenas tardes, doctor. Tengo una tos con flema amarillenta y calentura desde hace cuatro días.
  - ⚠ Copia literal del caso: «tengo una tos con flema…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre flema y sangre?
  - **Paciente (modelo):** Sí, doctor. La flema es espesa y amarilla oscura, y ayer noté que había hilitos de sangre, pero muy poco.
  - ⚠ Copia literal del caso: «la flema es espesa y…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre dolor de costado?
  - **Paciente (modelo):** Siento un dolor fuerte en el lado derecho de la espalda al toser o respirar hondo, como si le clavaran una aguja.
  - ⚠ Copia literal del caso: «en el lado derecho de…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre fiebre?
  - **Paciente (modelo):** Anoche la fiebre subió a 38.5 grados y me castañeteaban los dientes.
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre humo de leña?
  - **Paciente (modelo):** Desde niño cociné en poyo de leña sin chimenea adentro de la casa, y estuve expuesto al humo de leña diariamente.
  - ⚠ Copia literal del caso: «en poyo de lena sin…»
  - Calificación: __ / 5 · Cambiaría: ____________

### c_depresion_01 — Alexander, 61 años (Sonsonate Este, Sonsonate, urbano)
_Escolaridad: primaria · aspiración de la s: ninguna_

- **Doctor:** Buenas tardes, ¿qué le trae por aquí?
  - **Paciente (modelo):** Pasé sin ganas de nada, no puedo dormir y lloro a cada rato desde hace un mes.
  - ⚠ Copia literal del caso: «sin ganas de nada no…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre ideas de muerte o autolesion?
  - **Paciente (modelo):** A veces he pensado que mejor quisiera dormirse y no despertar, pero nunca he intentado hacerme daño.
  - ⚠ Copia literal del caso: «pensado que mejor quisiera dormirse…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre duelo y pérdida?
  - **Paciente (modelo):** Desde que murió mi compañero de vida, siento que la casa está vacía y que no tengo propósito.
  - ⚠ Copia literal del caso: «que la casa esta vacia…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre sueño?
  - **Paciente (modelo):** Me acuesto a las 9 pero me duerme hasta la 1, y me despierto a las 3 o 4 sin poder volver a dormir.
  - ⚠ Copia literal del caso: «duerme hasta la 1 y…»
  - Calificación: __ / 5 · Cambiaría: ____________
- **Doctor:** ¿Me puede contar sobre alimentación?
  - **Paciente (modelo):** La comida no me sabe a nada, solo como tortillas con queso por obligación.
  - Calificación: __ / 5 · Cambiaría: ____________

