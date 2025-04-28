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

# Conexión con Google Sheets usando st.secrets
def conectar_google_sheets():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    private_key = st.secrets.SERVICE_ACCOUNT_JSON.private_key.replace("\\n", "\n")

    service_account_info = {
        "type": st.secrets.SERVICE_ACCOUNT_JSON.type,
        "project_id": st.secrets.SERVICE_ACCOUNT_JSON.project_id,
        "private_key_id": st.secrets.SERVICE_ACCOUNT_JSON.private_key_id,
        "private_key": private_key,
        "client_email": st.secrets.SERVICE_ACCOUNT_JSON.client_email,
        "client_id": st.secrets.SERVICE_ACCOUNT_JSON.client_id,
        "auth_uri": st.secrets.SERVICE_ACCOUNT_JSON.auth_uri,
        "token_uri": st.secrets.SERVICE_ACCOUNT_JSON.token_uri,
        "auth_provider_x509_cert_url": st.secrets.SERVICE_ACCOUNT_JSON.auth_provider_x509_cert_url,
        "client_x509_cert_url": st.secrets.SERVICE_ACCOUNT_JSON.client_x509_cert_url,
        "universe_domain": st.secrets.SERVICE_ACCOUNT_JSON.universe_domain,
    }
    creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=scope)
    client = gspread.authorize(creds)
    return client

def cargar_historial(client):
    sheet = client.open(SPREADSHEET_NAME).worksheet(HISTORIAL_SHEET)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    numeros = df.iloc[:, 2:12].values.flatten()
    numeros = [int(n) for n in numeros if n != '']
    return numeros

def seleccionar_historial(historial, sorteos):
    numeros_por_sorteo = 10
    if sorteos == "Todos":
        return historial
    else:
        cantidad_numeros = int(sorteos) * numeros_por_sorteo
        return historial[-cantidad_numeros:]

def guardar_boletos(client, boletos, fecha_sorteo):
    sheet = client.open(SPREADSHEET_NAME).worksheet(REGISTROS_SHEET)
    rows = []
    for boleto in boletos:
        row = [fecha_sorteo] + boleto
        rows.append(row)
    sheet.append_rows(rows, value_input_option='USER_ENTERED')

def frecuencia_numeros(lista):
    conteo = {}
    for n in lista:
        conteo[n] = conteo.get(n, 0) + 1
    return conteo

def numeros_atrasados(historial):
    numeros = set(range(0, 100))
    historial_reversed = historial[::-1]
    ultimas_apariciones = {}

    for idx, n in enumerate(historial_reversed):
        if n not in ultimas_apariciones:
            ultimas_apariciones[n] = idx // 10

    faltantes = numeros - set(ultimas_apariciones.keys())
    for f in faltantes:
        ultimas_apariciones[f] = len(historial) // 10

    atrasados = sorted(ultimas_apariciones.items(), key=lambda x: x[1], reverse=True)
    return atrasados[:10]

def generar_boletos(conteo, estrategia='balanceada', cantidad_boletos=6):
    numeros = list(range(0, 100))
    conteo_ordenado = sorted(conteo.items(), key=lambda x: x[1], reverse=True)
    calientes = [n for n, _ in conteo_ordenado[:20]]
    frios = [n for n, _ in conteo_ordenado[-20:]]

    boletos = []

    for _ in range(cantidad_boletos):
        boleto = []

        if estrategia == 'balanceada':
            boleto.extend(random.sample(calientes, 3))
            boleto.extend(random.sample(frios, 2))

        elif estrategia == 'calientes':
            boleto.extend(random.sample(calientes, 5))

        elif estrategia == 'consecutivos':
            base = random.choice(numeros[:-1])
            boleto.append(base)
            boleto.append(base + 1)
            while len(boleto) < 5:
                n = random.choice(numeros)
                if n not in boleto:
                    boleto.append(n)

        elif estrategia == 'grupos':
            boleto.append(random.choice(range(0, 20)))
            boleto.append(random.choice(range(20, 40)))
            boleto.append(random.choice(range(40, 60)))
            boleto.append(random.choice(range(60, 80)))
            boleto.append(random.choice(range(80, 100)))

        elif estrategia == 'inteligente':
            seleccionados = []
            seleccionados.extend(random.sample(calientes, 3))
            seleccionados.append(random.choice(frios))

            rangos = [
                range(0, 20),
                range(20, 40),
                range(40, 60),
                range(60, 80),
                range(80, 100)
            ]
            usado = set(seleccionados)

            while len(seleccionados) < 5:
                rango = random.choice(rangos)
                n = random.choice(list(rango))
                if n not in usado:
                    seleccionados.append(n)
                    usado.add(n)

            pares = [n for n in seleccionados if n % 2 == 0]
            if not (2 <= len(pares) <= 3):
                candidatos = [n for n in numeros if n not in usado]
                if len(pares) > 3:
                    reemplazo = random.choice([n for n in candidatos if n % 2 != 0])
                else:
                    reemplazo = random.choice([n for n in candidatos if n % 2 == 0])
                seleccionados[random.randint(0, 4)] = reemplazo

            boleto = sorted(seleccionados)

        else:
            boleto = random.sample(numeros, 5)

        boleto = sorted(boleto)
        boletos.append(boleto)

    return boletos

# ----------------------------
# STREAMLIT APP

def main():
    st.image("https://raw.githubusercontent.com/SebaxDev/poceada-webapp/main/gengar.png", width=300)
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
