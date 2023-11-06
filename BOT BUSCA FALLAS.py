import pandas as pd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters

df = pd.read_csv('C:/Users/A/Documents/CODIGO Y BASE EN NUBE/BOT BUSCA FALLAS/BDDBBF.csv')  

tipos_alimentadores = df['Alimentador'].unique()
datos_usuario = {}

TIPO_ALIMENTADOR, TIPO_FALLA, OBTENER_ENLACES = range(3)

def start(update, context):
    keyboard = []
    for tipo in tipos_alimentadores:
        keyboard.append([InlineKeyboardButton(tipo, callback_data=tipo)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Selecciona el alimentador:", reply_markup=reply_markup)

    return TIPO_ALIMENTADOR

def button(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    alimentador = query.data

    if chat_id in datos_usuario and 'falla' in datos_usuario[chat_id]:
        context.bot.send_message(chat_id=chat_id, text="Por favor, selecciona el tipo de alimentador antes de elegir el tipo de falla.")
        return ConversationHandler.END  

    datos_usuario.pop(chat_id, None)
    datos_usuario[chat_id] = {'alimentador': alimentador}

    df_filtrado = df[df['Alimentador'] == alimentador]
    tipos_fallas = df_filtrado.columns[1:5].tolist()  

    keyboard = []
    for tipo in tipos_fallas:
        keyboard.append([InlineKeyboardButton(tipo, callback_data=tipo)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=chat_id, text="Selecciona el tipo de falla:", reply_markup=reply_markup)

    return TIPO_FALLA

def sub_button(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    tipo_falla = query.data

    if tipo_falla not in df.columns:
        context.bot.send_message(chat_id=chat_id, text="El tipo de falla seleccionado no es válido. Para una nueva consulta pulsa o manda /start")
        return ConversationHandler.END  

    datos_usuario[chat_id]['falla'] = tipo_falla

    context.bot.send_message(chat_id=chat_id, text=f"Seleccionaste el tipo de falla '{tipo_falla}' para el alimentador '{datos_usuario[chat_id]['alimentador']}'.\n\nAhora, por favor, envía el valor de la falla:")

    return OBTENER_ENLACES

def enviar_enlace(update, context):
    chat_id = update.message.chat_id
    mensaje = update.message.text.strip()

    if chat_id in datos_usuario and datos_usuario[chat_id].get('falla') is not None:
        try:
            valor_falla = int(mensaje)
            alimentador_seleccionado = datos_usuario[chat_id]['alimentador']
            tipo_falla_seleccionado = datos_usuario[chat_id]['falla']

            filtro_alimentador = df['Alimentador'] == alimentador_seleccionado
            filas_filtradas = df[filtro_alimentador]

            valor_minimo = filas_filtradas[tipo_falla_seleccionado].min()
            valor_maximo = filas_filtradas[tipo_falla_seleccionado].max()

            if valor_falla >= valor_minimo and valor_falla <= valor_maximo:
                filtro_falla = df[tipo_falla_seleccionado] == valor_falla
                filas_filtradas = df[filtro_alimentador & filtro_falla]

                if not filas_filtradas.empty:
                    enlaces_tramos = filas_filtradas['Enlace a maps'].tolist()
                    
                    if len(enlaces_tramos) == 1:
                          context.bot.send_message(chat_id=chat_id, text=f"Aquí tienes el enlace que corresponde a tu búsqueda:\n\n{enlaces_tramos[0]}")
                    else:
                          message = "Aquí tienes los enlaces correspondientes a tu búsqueda:\n\n"
                          for enlace_tramo in enlaces_tramos:
                              message += f"{enlace_tramo}\n"
                          context.bot.send_message(chat_id=chat_id, text=message)
                
                else:
                    closest_smaller_value = df.loc[filtro_alimentador & (df[tipo_falla_seleccionado] <= valor_falla), tipo_falla_seleccionado].max()
                    if pd.notnull(closest_smaller_value):
                        filtro_falla = df[tipo_falla_seleccionado] == closest_smaller_value
                        filas_filtradas = df[filtro_alimentador & filtro_falla]
                        enlaces_tramos = filas_filtradas['Enlace a maps'].tolist()

                        if len(enlaces_tramos) == 1:
                           context.bot.send_message(chat_id=chat_id, text=f"Aquí tienes el enlace que corresponde a tu búsqueda:\n\n{enlaces_tramos[0]}")
                        else:
                             message = "Aquí tienes los enlaces correspondientes a tu búsqueda:\n\n"
                             for enlace_tramo in enlaces_tramos:
                                 message += f"{enlace_tramo}\n"
                             context.bot.send_message(chat_id=chat_id, text=message)
                      
                    else:
                        context.bot.send_message(chat_id=chat_id, text="No se encontraron filas que coincidan con los criterios de selección.")
            else:
                context.bot.send_message(chat_id=chat_id, text=f"El valor ingresado ({valor_falla}) se encuentra fuera del rango ({valor_minimo} - {valor_maximo}).")
            datos_usuario.pop(chat_id)

        except ValueError:
            context.bot.send_message(chat_id=chat_id, text="Por favor, ingresa un valor numérico válido para la falla (números enteros positivos)")
            return      
    context.bot.send_message(chat_id=chat_id, text="Para una nueva consulta pulsa o manda /start.")
    return ConversationHandler.END

def main():
    
    updater = Updater(token='6373539093:AAFwrDtmmGuK93FK85uQrW7nbYPhJ3WT7go')
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    button_handler = CallbackQueryHandler(button)
    sub_button_handler = CallbackQueryHandler(sub_button)
    message_handler = MessageHandler(Filters.text & (~Filters.command), enviar_enlace)

    conversation_handler = ConversationHandler(
        entry_points=[start_handler],
        states={
            TIPO_ALIMENTADOR: [button_handler],
            TIPO_FALLA: [sub_button_handler],
            OBTENER_ENLACES: [message_handler]
        },
        fallbacks=[],
    )

    dispatcher.add_handler(conversation_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
