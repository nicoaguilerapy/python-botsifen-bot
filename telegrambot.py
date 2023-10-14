import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler
import requests
import json
import sqlite3
import datetime
import os

db_filename = 'resultados.db'
db_exists = os.path.exists(db_filename)

conn = sqlite3.connect(db_filename)
cursor = conn.cursor()

if not db_exists:
    cursor.execute('''
    CREATE TABLE resultados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TIMESTAMP,
        resultado TEXT
    )
    ''')
    conn.commit()


def registrar_resultado(resultado):
    fecha_actual = datetime.datetime.now()
    cursor.execute(
        "INSERT INTO resultados (fecha, resultado) VALUES (?, ?)", (fecha_actual, resultado))
    conn.commit()


def verificar_resultados_recientes(minutos=5):
    fecha_limite = datetime.datetime.now() - datetime.timedelta(minutes=minutos)
    cursor.execute(
        "SELECT resultado FROM resultados WHERE fecha >= ? ORDER BY fecha DESC LIMIT 1", (fecha_limite,))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        return None


TOKEN_TELEGRAM = "6621464383:AAEDB3LajPCuPA9yYtKlquo91-0TfcZ0ltw"
URL_BASE = ""
TOKEN_FACTURASEND = ""
CDC_ASINCRONO = ""
CDC_SINCRONO = ""
ok = "✅"
error = "❌"


def incrementar_numero(data):
    try:
        numero_actual = int(data["numero"])
        numero_actual += 1
        data["numero"] = numero_actual
        return data
    except KeyError:
        print("La clave 'numero' no existe en los datos JSON.")
        return None


def enviar_solicitud(url, json_data, headers):
    try:
        response = requests.post(url, json=json_data, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('success') == True:
                return ok, data
            else:
                print(f"Error en la respuesta: {data.get('error_message')}")
                return error, None
        else:
            print(f"Error en la solicitud: {response.status_code}")
            return error, None
    except Exception as e:
        print(f"Error en la solicitud: {str(e)}")
        return error, None


def consultar_ruc(documento):
    headers = {"Authorization": f"Bearer {TOKEN_FACTURASEND}"}
    url = f"{URL_BASE}/ruc/{documento}"

    result = enviar_solicitud(url, {}, headers)
    return result


def crear_documento_electronico(tipo):
    with open("de.json", "r") as file:
        json_temp = json.load(file)

    json_temp = incrementar_numero(json_temp)

    with open("de.json", "w") as file:
        json.dump(json_temp, file, indent=4)

    headers = {"Authorization": f"Bearer {TOKEN_FACTURASEND}",
               "Content-Type": "application/json"}
    url = f"{URL_BASE}/{tipo}/create/"

    if tipo == 'lote':
        json_data = []
        json_data.append(json_temp)
    else:
        json_data = json_temp
    

    result, data = enviar_solicitud(url, json_data, headers)
    if data:
        print(data.get('result', {}).get('deList', [{}])[0])
        return result, data.get('result', {}).get('deList', [{}])[0]
    else:
        return result, None


def cancelar_documento_cdc(cdc):
    json_data = {"motivo": "ANULACION DE PRUEBA", "cdc": cdc}
    headers = {"Authorization": f"Bearer {TOKEN_FACTURASEND}",
               "Content-Type": "application/json"}
    url = f"{URL_BASE}/evento/cancelacion/"

    result, _ = enviar_solicitud(url, json_data, headers)
    return result


def get_evento_in():
    json_data = {"hasta": 10, "tipoDocumento": 1, "motivo": "anulacion de prueba",
                 "desde": 1, "establecimiento": "001", "punto": "001", "timbrado": "03699583"}
    headers = {
        "Authorization": f"Bearer {TOKEN_FACTURASEND}",
        "Content-Type": "application/json"
    }
    return enviar_solicitud(URL_BASE + "/evento/inutilizacion/", json_data, headers)


def get_evento_co():
    json_data = {"tipoConformidad": 2, "cdc": "01800695631001001000000812021112910953738413",
                 "fechaRecepcion": "2023-09-14T00:00:00"}

    headers = {
        "Authorization": f"Bearer {TOKEN_FACTURASEND}",
        "Content-Type": "application/json"
    }
    return enviar_solicitud(URL_BASE + "/evento/conformidad/", json_data, headers)


def get_evento_di():
    json_data = {"motivo": "NO ME GUSYA NADA COMO LO HICIERON",
                 "cdc": "01800695631001001000000812021112910953738413"}

    headers = {
        "Authorization": f"Bearer {TOKEN_FACTURASEND}",
        "Content-Type": "application/json"
    }
    return enviar_solicitud(URL_BASE + "/evento/disconformidad/", json_data, headers)


def get_evento_de():
    json_data = {"ruc": "80010785-3 ", "motivo": "NO ME GUSYA NADA COMO LO HICIERON",
                 "cdc": "01800695631001001000000812021112910953738413", "tipoReceptor": 1, "documentoNumero": "",
                 "fechaEmision": "2023-09-14T00:00:00", "documentoTipo": 11,
                 "nombre": "MAXLUB SRL                                                                                                                                            ",
                 "fechaRecepcion": "2023-09-14T00:00:00"}

    headers = {
        "Authorization": f"Bearer {TOKEN_FACTURASEND}",
        "Content-Type": "application/json"
    }
    return enviar_solicitud(URL_BASE + "/evento/desconocimiento/", json_data, headers)


async def handle_test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resultado = verificar_resultados_recientes(minutos=3)

    if resultado:
        await update.message.reply_text(resultado)
        return
    else:
        resultado_arr = []

        welcome_message = (
            "Buenas! Soy un Bot para comprobar el estado de los servicios del Sifen Paraguay 🇵🇾 😃\n"
            f'La fecha y hora de la prueba registrada es: {current_time}\n'
            'Ambiente: Test\n'
            'Formato:\n'
            'SERVICIO => ESTADO'
        )

        print(f"ALGUIEN MANDO MSJ: {current_time}")
        resultado_arr.append(welcome_message)
        await update.message.reply_text(welcome_message)

        message = (
            'El sifen puede tener estos estados: \n'
            '✅: Servidor en linea\n'
            '✅: Servidor en linea pero con Errores en los Servicios\n'
            '❌: Servidor caido\n'
        )
        resultado_arr.append(message)
        await update.message.reply_text(message)

        resultado_temp = consultar_ruc('80003400')
        resultado_ruc = f'CONSULTA RUC: {resultado_temp[0]}'
        resultado_arr.append(resultado_ruc)
        await update.message.reply_text(resultado_ruc)

        # Crear CDC Sincrónico y Cancelarlo
        response, cdc = crear_documento_electronico("de")
        message = (
            f'CREAR CDC SINCRONO: {response}\n'
            f'CANCELAR CDC SINCRONO: {cancelar_documento_cdc(cdc)}\n'
        )
        response, cdc = crear_documento_electronico("lote")
        message = (
            f'CREAR CDC ASINCRONO: {response}\n'
            f'CANCELAR CDC ASINCRONO: {cancelar_documento_cdc(cdc)}\n'
        )
        resultado_arr.append(message)
        await update.message.reply_text(message)

        message = 'EVENTOS: Espere mientras se procesan...⌚'
        resultado_arr.append(message)
        await update.message.reply_text(message)

        eventos_arr = [get_evento_in(), get_evento_co(),
                       get_evento_di(), get_evento_de()]
        
        print(eventos_arr)

        message = f'INUTILIZACION: {eventos_arr[0][0]} \n{json.dumps(eventos_arr[0][1], indent=1)}'
        resultado_arr.append(message)
        await update.message.reply_text(message)

        message = f'CONFORMIDAD: {eventos_arr[1][0]} \n{json.dumps(eventos_arr[1][1], indent=1)}'
        resultado_arr.append(message)
        await update.message.reply_text(message)

        message = f'DISCONFORMIDAD: {eventos_arr[2][0]} \n{json.dumps(eventos_arr[2][1], indent=1)}'
        resultado_arr.append(message)
        await update.message.reply_text(message)

        message = f'DESCONOCIMIENTO: {eventos_arr[3][0]} \n{json.dumps(eventos_arr[3][1], indent=1)}'
        resultado_arr.append(message)
        await update.message.reply_text(message)

        concatenated_message = "\n".join(resultado_arr)
        registrar_resultado(concatenated_message)
        await update.message.reply_text("Luego tendré más funcionalidades, estoy chiquito...")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text

    welcome_message = (
            'Soy un Bot del Sifen Paraguay 🇵🇾 😃, listo para ayudarte!\n'
            'Comandos: \n'
            'Para ambiente de test: /test\n'
            'Para Consulta Ruc: /ruc XXXXXXX'
        )
                
    await update.message.reply_text(welcome_message)

async def handle_ruc_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text

    if text.startswith("/ruc") and text[4:].strip().isdigit():
        ruc_number = text[4:].strip()
        response_message = f"Consultando: {ruc_number} ⌚..."
        await update.message.reply_text(response_message)
        resultado_temp = consultar_ruc(ruc_number)
        print(resultado_temp)
        if resultado_temp[0] == "❌":
            resultado_text = "Error de Servicio"
        else:
            if resultado_temp[1]['result']['respuesta_codigo'] != "0500":
                resultado_text = "Razón Social: "+resultado_temp[1]['result']['razon_social']+\
                "\nEstado: "+resultado_temp[1]['result']['estado_mensaje']+\
                "\nFacturador Electronico: "+("SI" if resultado_temp[1]['result']['facturador_electronico'] else "No")
            else:
                resultado_text = "Ruc no encontrado en el Sifen"
                
        await update.message.reply_text(resultado_text)
    else:
        await update.message.reply_text("El formato válido es /ruc seguido de un número.\nEjemplo: /ruc 12345678")

app = ApplicationBuilder().token(TOKEN_TELEGRAM).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("test", handle_test_command))
app.add_handler(CommandHandler("ruc", handle_ruc_command))
app.run_polling()
