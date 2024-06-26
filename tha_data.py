import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit_antd_components as sac
import time

# Configura las credenciales para acceder a la API de Google Sheets
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('my-project-uri-409012-2928f7e18a5a.json', scope)
client = gspread.authorize(creds)

# Define una función para manejar la obtención de la hoja de cálculo con reintentos
def get_worksheet_with_retry(spreadsheet_url):
    retries = 0
    delay = 1  # Initial delay in seconds

    while retries < 3:
        try:
            spreadsheet = client.open_by_url(spreadsheet_url)
            return spreadsheet.get_worksheet(0)
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429:
                print(f"Quota exceeded. Retrying in {delay} seconds...")
                time.sleep(delay)
                retries += 1
                delay *= 2  # Double the delay for each retry
            else:
                raise e  # Re-raise other exceptions

    # Raise an exception if all retries fail
    raise Exception("Failed to retrieve worksheet after retries")

# Abre la hoja de cálculo usando el enlace público
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1LKgT9JOEjH96Zlv8B7rXOdRwDjvCZ_3zbYUp9VbDypI/edit?usp=sharing"
try:
    worksheet = get_worksheet_with_retry(spreadsheet_url)  # Usa la función con reintentos
except Exception as e:
    st.error(f"Error abriendo spreadsheet: {e}")
    exit()  # Salir de la app si la apertura falla

st.set_page_config(page_title="HTA", page_icon="favicon-32x32.png", layout="wide")

# Inicializar el estado de la sesión
if 'page' not in st.session_state:
    st.session_state.page = "home"

# Inicializar números de jugadores como una lista
if 'player_numbers' not in st.session_state:
    st.session_state.player_numbers = []

# Página de inicio
if st.session_state.page == "home":
    st.title('**HANDBALL TEAM ANALYSIS**')
    st.write("Configura los números de los jugadores:")
    # Usa st.text_area para ingresar múltiples números separados por comas
    player_numbers_input = st.text_area("Introduce los números de los jugadores separados por comas:", value='1,2,3')
    # Si se hace clic en el botón, actualiza la lista de números de jugadores
    if st.button("Crear botones de jugadores"):
        player_numbers = sorted(int(x.strip()) for x in player_numbers_input.split(",") if x.strip().isnumeric())
        st.session_state.player_numbers = sorted(set(player_numbers))
        st.session_state.page = "player_buttons"

# Variable global para almacenar el estado del DataFrame
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=['Team Name', 'Rival Team Name', 'Lineup', 'Phase Game', 'Inici', 
                                                'Def Type', 'Player', 'Action Type', 'Feeder', 'Sub Action', 'Espai'])

# Función para manejar las acciones y actualizar el DataFrame
def handle_action(team_name, rival_team, campo, phasegame, start, def_type, player, action_type, player2, sub_action_type, space):
    new_row = {'Team Name': team_name, 'Rival Team Name': rival_team, 'Lineup': campo, 'Phase Game': phasegame, 'Inici': start,
               'Def Type': def_type, 'Player': player, 'Action Type': action_type, 'Feeder': player2, 'Sub Action': sub_action_type, 'Espai': space}
    
    # Obtener el DataFrame almacenado en la variable de estado
    df_copy = st.session_state.df.copy()

    # Agregar una nueva fila al DataFrame
    df_copy = pd.concat([df_copy, pd.DataFrame([new_row])], ignore_index=True)
    
    # Actualizar la variable de estado con el DataFrame actualizado
    st.session_state.df = df_copy
    
    return df_copy

# Info general:
col1, col2 = st.columns(2)

with col1:
    team_name = st.text_input('Equipo')

with col2:
    rival_team = st.text_input('Rival')

# App Data
col1, col2, col3 = st.columns(3)

with col1:
    # Fase Joc
    phasegame = sac.segmented(items=[sac.SegmentedItem(label='Ataque'), sac.SegmentedItem(label='Defensa')], label='**Fase Juego**', align='left', size='sm', color='cyan')

    # Inici:
    start = sac.segmented(items=[
                              sac.SegmentedItem(label='Posicional'),
                              sac.SegmentedItem(label='Falta'),
                              sac.SegmentedItem(label='2da Oleada'),
                              sac.SegmentedItem(label='Repliegue'),
                              sac.SegmentedItem(label='Contragol'),
                              sac.SegmentedItem(label='Contraataque'),
                              sac.SegmentedItem(label='Superioridad'),
                              sac.SegmentedItem(label='Inferioridad')],
                          label='**Situación Juego**', align='left', size='sm', color='cyan', divider=False)

    # Desglosar tipos de acción y zonas en botones
    def_type = sac.segmented(items=[
                              sac.SegmentedItem(label='6:0'),
                              sac.SegmentedItem(label='5:1'),
                              sac.SegmentedItem(label='3:3'),
                              sac.SegmentedItem(label='3:2:1'),
                              sac.SegmentedItem(label='4:2'),
                              sac.SegmentedItem(label='4:1:1'),
                              sac.SegmentedItem(label='5:0'),
                              sac.SegmentedItem(label='4:0'),
                              sac.SegmentedItem(label='Individual')],
                          label='**Tipo Defensa**', align='left', size='sm', color='cyan', divider=False)

with col2:
    campo = sac.chip([sac.ChipItem(label=str(player_num)) for player_num in st.session_state.get('player_numbers', [])], label='**Banquillo**', align='left', size='xs', radius='xs', key="player_buttons", multiple=True)
    selected_player_numbers = [x for x in st.session_state.get('player_numbers', []) if str(x) in campo]
    player_numbers_str = [str(player_num) for player_num in selected_player_numbers]
    player_numbers_buttons = sac.buttons([sac.ButtonsItem(label=player_num_str) for player_num_str in player_numbers_str],
                                         label='**Pista**', align='left', size='xs', radius='xs')
    player = player_numbers_buttons

    action_type = sac.segmented(items=[
        sac.SegmentedItem(label='Gol'),
        sac.SegmentedItem(label='Falta'),
        sac.SegmentedItem(label='Parada'),
        sac.SegmentedItem(label='Palo/Fuera'),
        sac.SegmentedItem(label='Pasos'),
        sac.SegmentedItem(label='Dobles'),
        sac.SegmentedItem(label='Ataque'),
        sac.SegmentedItem(label='Area'),
        sac.SegmentedItem(label='Recuperación'),
        sac.SegmentedItem(label='Mal Pase'),
        sac.SegmentedItem(label='Mala Recepción'),
        sac.SegmentedItem(label='2 min'),
        sac.SegmentedItem(label='Penalti'),
        sac.SegmentedItem(label='Pasivo')
    ], label='**Acción**', align='left', size='sm', divider=False)

    st.session_state.player_buttons_switch = sac.switch(label="Activar/Desactivar Feeder", off_color='grey', on_color='lime', value=True)

    if st.session_state.player_buttons_switch:
        player_numbers_buttons2 = sac.buttons([sac.ButtonsItem(label=str(player_num)) for player_num in selected_player_numbers],
                                              label='**Feeder**', align='left', size='xs', radius='xs', color='lime')   
        sub_action_type1 = sac.segmented(items=[
            sac.SegmentedItem(label='NA'),
            sac.SegmentedItem(label='Asistencia'),
            sac.SegmentedItem(label='Desmarque sin balón')
        ], label='**Sub Acción**', align='left', size='sm', color='lime', divider=False)
             
    else:
        player_numbers_buttons2 = None
        sub_action_type1 = None

    player2 = player_numbers_buttons2
    sub_action_type = sub_action_type1

with col3:
    # Espais Atacats
    space = sac.segmented(items=[
                          sac.SegmentedItem(label='0-1'),
                          sac.SegmentedItem(label='...', disabled=True),
                          sac.SegmentedItem(label='7 metros'),
                          sac.SegmentedItem(label='...', disabled=True),
                          sac.SegmentedItem(label='1-0'),
                          sac.SegmentedItem(label='1-2'),
                          sac.SegmentedItem(label='2-3'),
                          sac.SegmentedItem(label='3-3'),
                          sac.SegmentedItem(label='3-2'),
                          sac.SegmentedItem(label='2-1'),
                          sac.SegmentedItem(label='9m Izq'),
                          sac.SegmentedItem(label='9m Centro'),
                          sac.SegmentedItem(label='9m Der'),
                          sac.SegmentedItem(label='-   Medio Campo   -'),
                          sac.SegmentedItem(label='-   Propio Campo   -')],
                      label='**Espacio Atacado/Defendido**', size='md', color='green', divider=False)

    # Diccionario de mapeo para los valores de Espacio Atacado/Defendido
    espacio_mapping = {
        '0-1': '6m 0-1',
        '7 metros': '7m',
        '1-0': '6m 1-0',
        '1-2': '6m 1-2',
        '2-3': '6m 2-3',
        '3-3': '6m 3-3',
        '3-2': '6m 3-2',
        '2-1': '6m 2-1',
        '9m Izq': '9mIzquierda',
        '9m Centro': '9mCentro',
        '9m Der': '9mDerecha',
        '-   Medio Campo   -': 'Medio Campo',
        '-   Propio Campo   -': 'Propio Campo'
    }

    # Botón para agregar información a Google Sheets
    if st.button('**REGISTRAR ACCIÓN**'):
        # Obtener los valores de los campos
        team_name_value = team_name
        rival_team_value = rival_team
        campo_value = ','.join(str(x) for x in campo)
        phasegame_value = phasegame
        start_value = start
        def_type_value = def_type
        player_value = player
        action_type_value = action_type
        player2_value = player2
        sub_action_type_value = sub_action_type
        space_value = space

        # Obtener el valor mapeado para el espacio seleccionado en la aplicación
        space_value_mapped = espacio_mapping.get(space_value, space_value)

        try:
            # Agregar la nueva fila a Google Sheets
            worksheet.append_row([team_name_value, rival_team_value, campo_value, phasegame_value, start_value, def_type_value, player_value, action_type_value, player2_value, sub_action_type_value, space_value_mapped])
            st.success("Datos registrados y enviados a Google Sheets con éxito.")
        except Exception as e:
            st.error(f"Error al registrar la acción: {e}")
