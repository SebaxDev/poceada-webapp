import streamlit as st
import pandas as pd
import random
import gspread
from google.oauth2 import service_account
import matplotlib.pyplot as plt

st.set_page_config(page_title="🌹 Generador Poceada", page_icon="🌹", layout="centered")

# Forzar idioma
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

def conectar_google_sheets():
    try:
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
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return None

def cargar_historial(client):
    try:
        sheet = client.open(SPREADSHEET_NAME).worksheet(HISTORIAL_SHEET)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        numeros = df.iloc[:, 2:12].values.flatten()
        numeros = [int(n) for n in numeros if str(n).isdigit()]
        return numeros
    except Exception as e:
        st.error(f"Error al cargar el historial: {e}")
        return []

def seleccionar_historial(historial, sorteos):
    numeros_por_sorteo = 10
    if sorteos == "Todos":
        return historial
    else:
        cantidad_numeros = int(sorteos) * numeros_por_sorteo
        return historial[-cantidad_numeros:]

def guardar_boletos(client, boletos, fecha_sorteo):
    try:
        sheet = client.open(SPREADSHEET_NAME).worksheet(REGISTROS_SHEET)
        rows = [[fecha_sorteo] + boleto for boleto in boletos]
        sheet.append_rows(rows, value_input_option='USER_ENTERED')
    except Exception as e:
        st.error(f"Error al guardar los boletos: {e}")

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
            boleto = [base, base + 1]
            while len(boleto) < 5:
                n = random.choice(numeros)
                if n not in boleto:
                    boleto.append(n)
        elif estrategia == 'grupos':
            boleto = [random.choice(range(i, i + 20)) for i in range(0, 100, 20)]
        elif estrategia == 'inteligente':
            seleccionados = random.sample(calientes, 3)
            seleccionados.append(random.choice(frios))
            rangos = [range(i, i + 20) for i in range(0, 100, 20)]
            usado = set(seleccionados)
            while len(seleccionados) < 5:
                r = random.choice(rangos)
                n = random.choice(list(r))
                if n not in usado:
                    seleccionados.append(n)
                    usado.add(n)
            pares = [n for n in seleccionados if n % 2 == 0]
            if not (2 <= len(pares) <= 3):
                candidatos = [n for n in numeros if n not in usado]
                reemplazo = random.choice([n for n in candidatos if (len(pares) > 3) ^ (n % 2 == 0)])
                seleccionados[random.randint(0, 4)] = reemplazo
            boleto = sorted(seleccionados)
        else:
            boleto = random.sample(numeros, 5)
        boletos.append(sorted(boleto))
    return boletos

def simular_boletos(historial, boletos):
    resultados = []
    sorteos = [historial[i:i+10] for i in range(0, len(historial), 10)]
    for boleto in boletos:
        max_aciertos = max([len(set(boleto) & set(sorteo)) for sorteo in sorteos])
        resultados.append(max_aciertos)
    return resultados

# ----------------------------
# STREAMLIT APP

def main():
    st.markdown("<div style='text-align: center'><img src='https://raw.githubusercontent.com/SebaxDev/poceada-webapp/main/gengar.png' width='150'></div>", unsafe_allow_html=True)
    st.title("🎯 Generador Inteligente de Boletos")
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("Bienvenido a tu herramienta para jugar mejor en la Poceada! 🎲✨")

    st.info("💡 Recordá: jugar con estrategia mejora tus chances!", icon="💡")

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
        if client:
            historial_total = cargar_historial(client)
            if historial_total:
                st.subheader("📈 Elegí sorteos a analizar")
                seleccion_sorteos = st.selectbox("Cantidad de sorteos", ["100", "150", "200", "300", "Todos"])
                historial = seleccionar_historial(historial_total, seleccion_sorteos)
                conteo = frecuencia_numeros(historial)
                atrasados = numeros_atrasados(historial)

                st.subheader("🧊 Top 10 números más fríos")
                st.dataframe(pd.DataFrame(atrasados, columns=["Número", "Sorteos sin salir"]))

                calientes_top = sorted(conteo.items(), key=lambda x: x[1], reverse=True)[:10]
                st.subheader("🔥 Top 10 números más calientes")
                st.dataframe(pd.DataFrame(calientes_top, columns=["Número", "Veces que salió"]))

                st.subheader("📊 Frecuencia de los 20 más repetidos")
                top20 = pd.Series(conteo).sort_values(ascending=False).head(20)
                st.bar_chart(top20)

                st.subheader("🎯 Elegí estrategia de generación")
                estrategia = st.selectbox("Estrategia", ["balanceada", "calientes", "consecutivos", "grupos", "inteligente"])
                cantidad_boletos = st.slider("Cantidad de boletos", 1, 20, 6)

                if st.button("🎟 Generar Boletos"):
                    with st.spinner("Generando boletos... 🎰"):
                        st.session_state.boletos = generar_boletos(conteo, estrategia, cantidad_boletos)
                        st.success("¡Boletos generados exitosamente! 🎉")

                if st.session_state.boletos:
                    st.subheader("🧾 Tus boletos generados")
                    df_boletos = pd.DataFrame(st.session_state.boletos, columns=["N°1", "N°2", "N°3", "N°4", "N°5"])
                    st.dataframe(df_boletos)

                    st.download_button("📥 Descargar en CSV", data=df_boletos.to_csv(index=False),
                                       file_name="boletos_poceada.csv", mime="text/csv")

                    resultados = simular_boletos(historial, st.session_state.boletos)
                    st.subheader("🧪 Simulación contra el historial")
                    st.write("Máximo acierto obtenido por boleto:")
                    for idx, aciertos in enumerate(resultados):
                        st.write(f"Boleto {idx+1}: {aciertos} aciertos")

                    st.markdown("<hr>", unsafe_allow_html=True)
                    guardar = st.radio("¿Querés guardar estos boletos?", ["No", "Sí"], horizontal=True)
                    if guardar == "Sí":
                        fecha_sorteo = st.date_input("Seleccioná la fecha del sorteo")
                        if st.button("💾 Guardar Boletos"):
                            guardar_boletos(client, st.session_state.boletos, fecha_sorteo.strftime("%d/%m/%Y"))
                            st.success("🎯 Boletos guardados exitosamente!")

            st.markdown("<hr>", unsafe_allow_html=True)
            st.info(random.choice([
                "✅ Revisá siempre los números que más se repiten!",
                "✅ Alterná entre estrategias para mejores resultados.",
                "✅ ¡Nunca repitas exactamente los mismos boletos!",
                "✅ Jugá responsablemente y con presupuesto fijo."
            ]))

    st.markdown("""
    <hr>
    <center><sub>Creado con ❤ por <b>SebaxDev</b> - 2025</sub></center>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
