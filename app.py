import streamlit as st
import pandas as pd
import random
import gspread
from google.oauth2 import service_account

# ----------------------------
# PRIMERO configuramos la página
st.set_page_config(page_title="🌹 Generador Poceada", page_icon="🌹", layout="centered")

# Luego forzamos el idioma español
st.markdown("""
    <script>
    document.getElementsByTagName('html')[0].setAttribute('lang','es')
    </script>
""", unsafe_allow_html=True)

# ----------------------------
# CONFIGURACIONES
SPREADSHEET_NAME = 'Poceada Chat'
HISTORIAL_SHEET = 'Historial'
REGISTROS_SHEET = 'Registros'

# ----------------------------
# FUNCIONES

# (todas tus funciones exactamente igual que antes: conectar_google_sheets, cargar_historial, etc.)

# ----------------------------
# STREAMLIT APP

def main():
    st.image("https://i.imgur.com/lKW2fKv.png", width=300)
    st.title("🎯 Generador Inteligente de Boletos")
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("Bienvenido a tu herramienta para jugar mejor en la Poceada! 🎲✨")

    # Un pequeño tip motivacional
    st.info("💡 *Recordá: jugar con estrategia mejora tus chances!*", icon="💡")

    if "logueado" not in st.session_state:
        st.session_state.logueado = False
    if "boletos" not in st.session_state:
        st.session_state.boletos = None

    if not st.session_state.logueado:
        with st.form("login"):
            st.subheader("🔐 Iniciar Sesión")
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            login_button = st.form_submit_button("Ingresar")
        if login_button:
            if username == "SebaxDev" and password == "SebaxDev":
                st.session_state.logueado = True
                st.success("¡Bienvenido SebaxDev! 🎯")
            else:
                st.error("Usuario o contraseña incorrectos ❌")

    if st.session_state.logueado:
        client = conectar_google_sheets()
        historial_total = cargar_historial(client)

        st.subheader("📈 Elegí sorteos a analizar")
        opciones_sorteos = ["100", "150", "200", "300", "Todos"]
        seleccion_sorteos = st.selectbox("Cantidad de sorteos", opciones_sorteos)

        historial = seleccionar_historial(historial_total, seleccion_sorteos)

        conteo = frecuencia_numeros(historial)
        atrasados = numeros_atrasados(historial)

        st.subheader("🧊 Top 10 números más fríos")
        st.dataframe(pd.DataFrame(atrasados, columns=["Número", "Sorteos sin salir"]))

        st.subheader("🎯 Elegí estrategia de generación")
        estrategia = st.selectbox("Estrategia", ["balanceada", "calientes", "consecutivos", "grupos", "inteligente"])
        cantidad_boletos = st.slider("Cantidad de boletos", 1, 20, 6)

        if st.button("🎟️ Generar Boletos"):
            with st.spinner("Generando boletos... 🎰"):
                st.session_state.boletos = generar_boletos(conteo, estrategia, cantidad_boletos)
                st.success("¡Boletos generados exitosamente! 🎉")

        if st.session_state.boletos:
            st.subheader("🧾 Tus boletos generados")
            st.dataframe(pd.DataFrame(st.session_state.boletos, columns=["N°1", "N°2", "N°3", "N°4", "N°5"]))

            st.markdown("<hr>", unsafe_allow_html=True)

            guardar = st.radio("¿Querés guardar estos boletos?", ["No", "Sí"], horizontal=True)
            if guardar == "Sí":
                fecha_sorteo = st.date_input("Seleccioná la fecha del sorteo")
                if st.button("💾 Guardar Boletos"):
                    guardar_boletos(client, st.session_state.boletos, fecha_sorteo.strftime("%d/%m/%Y"))
                    st.success("🎯 Boletos guardados en la hoja 'Registros' exitosamente!")

        # Nueva sección extra: Consejito Aleatorio
        st.markdown("<hr>", unsafe_allow_html=True)
        import random
        consejos = [
            "✅ Revisá siempre los números que más se repiten!",
            "✅ Alterná entre estrategias para mejores resultados.",
            "✅ ¡Nunca repitas exactamente los mismos boletos en diferentes sorteos!",
            "✅ Jugá responsablemente y con presupuesto fijo."
        ]
        st.info(random.choice(consejos))

    # FOOTER FINAL
    st.markdown("""
    <hr>
    <center><sub>Creado con ❤️ por <b>SebaxDev</b> - 2025</sub></center>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
