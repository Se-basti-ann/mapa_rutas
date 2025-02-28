import base64
import numpy as np
import io
import dash
from dash import html, Input, Output, State
import pandas as pd
import unicodedata
import plotly.graph_objects as go
import random
from datetime import datetime
from utilities import convertir_fechas, parse_coord

def eliminar_tildes(texto):
    try:
        texto = unicodedata.normalize('NFKD', texto)
        texto = texto.encode('ASCII', 'ignore').decode('ASCII')
    except:
        pass
    return texto.upper()

def registrar_callbacks(app):
    @app.callback(
    Output('stored-data', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
    )
    def process_uploaded_file(contents, filename):
        if contents is None:
            return dash.no_update
        
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        try:
            df = pd.read_excel(io.BytesIO(decoded))
            
            # Procesamiento de datos
            df['Tecnico_Clean'] = (
            df['4.Nombre del Técnico Instalador']
            .astype(str)
            .apply(eliminar_tildes)
            .str.upper()
            .str.strip()  # Elimina espacios al inicio/final
            .str.replace(r'\s+', ' ', regex=True)  # Unifica múltiples espacios
            .str.replace(r'[^A-Z ]', '', regex=True)  # Elimina caracteres especiales
            )
            df['Latitud_adj'] = df['Latitud']
            df['Longitud_adj'] = df['Longitud']
            
            # Ajuste de coordenadas
            groups = df.groupby(['Latitud', 'Longitud'])
            for (lat, lon), group in groups:
                if len(group) > 1:
                    indices = group.index
                    for i, idx in enumerate(indices[1:]):
                        angle = np.random.uniform(0, 2 * np.pi)
                        delta_lat = (5 / 111320) * np.cos(angle)
                        delta_lon = (5 / (111320 * np.cos(np.radians(lat)))) * np.sin(angle)
                        df.at[idx, 'Latitud_adj'] = lat + delta_lat
                        df.at[idx, 'Longitud_adj'] = lon + delta_lon
            
            df["Latitud"] = df["Latitud"].apply(parse_coord)
            df["Longitud"] = df["Longitud"].apply(parse_coord)
            df = df.dropna(subset=["Latitud", "Longitud"])
            df = df[(df["Latitud"] > 0) & (df["Longitud"] < 0)]
            
            df['FechaCreacion'] = df['FechaCreacion'].apply(convertir_fechas)
            
            # Generar colores
            tecnicos = sorted(df['Tecnico_Clean'].dropna().unique())
            colores = {t: f"rgb({random.randint(0,255)},{random.randint(0,255)},{random.randint(0,255)})" 
                      for t in tecnicos}
            
            return {
                'df': df.to_json(date_format='iso', orient='split'),
                'colores': colores
            }
            
        except Exception as e:
            print(e)
            return dash.no_update
    
 
    # Callback para actualizar dropdown de técnicos
    @app.callback(
        Output('filtro-tecnico', 'options'),
        Input('stored-data', 'data')
    )
    def update_tecnicos(data):
        if not data:
            return []
        df = pd.read_json(data['df'], orient='split')
        tecnicos = sorted([t for t in df['Tecnico_Clean'].unique() if t is not None])
        return [{'label': t, 'value': t} for t in tecnicos]
    
    @app.callback(
        Output('filtro-fecha', 'options'),
        Output('filtro-fecha', 'value'),
        Input('boton-filtrar', 'n_clicks'),
        [State('filtro-tecnico', 'value'),
         State('filtro-ot', 'value'),
         State('filtro-nodo', 'value'),
         State('stored-data', 'data')]  # <-- Añadir este State
    )
    def actualizar_fechas_disponibles(n_clicks, tecnicos_sel, ot, nodo, data):
        if not data:
            return [], None
        df = pd.read_json(data['df'], orient='split')
        df['FechaCreacion'] = pd.to_datetime(df['FechaCreacion'])
        filtered_df = df.copy()
        
        # Aplicar filtros básicos
        if tecnicos_sel:
            filtered_df = filtered_df[filtered_df['Tecnico_Clean'].isin(tecnicos_sel)]
        if ot:
            filtered_df = filtered_df[filtered_df['2.Nro de O.T.'].astype(str).str.contains(ot)]
        if nodo:
            filtered_df = filtered_df[filtered_df['1.NODO DEL POSTE.'].astype(str).str.contains(nodo)]
        
        # Extraer fechas únicas y ordenadas
        if not filtered_df.empty:
            filtered_df['Fecha'] = filtered_df['FechaCreacion'].dt.strftime('%d/%m/%Y')
            fechas_disponibles = sorted(filtered_df['Fecha'].unique().tolist())
        else:
            fechas_disponibles = []
        
        return [{'label': f, 'value': f} for f in fechas_disponibles], None
    # Callback para actualizar horas disponibles
    @app.callback(
        Output('filtro-hora', 'options'),
        Output('filtro-hora', 'value'),
        Output('filtro-hora', 'disabled'),
        Input('filtro-fecha', 'value'),
        [State('filtro-tecnico', 'value'),
         State('filtro-ot', 'value'),
         State('filtro-nodo', 'value'),
         State('stored-data', 'data')]
    )
    def actualizar_horas_disponibles(fecha_seleccionada, tecnicos_sel, ot, nodo, data):
        if not data:
            return [], None, True  # <-- Añadir el tercer elemento (disabled=True)
        
        df = pd.read_json(data['df'], orient='split')
        df['FechaCreacion'] = pd.to_datetime(df['FechaCreacion'], errors='coerce')
        if not fecha_seleccionada:
            return [], None, True  # Deshabilitar si no hay fecha
        
        filtered_df = df.copy()
        
        # Aplicar filtros básicos
        if tecnicos_sel:
            filtered_df = filtered_df[filtered_df['Tecnico_Clean'].isin(tecnicos_sel)]
        if ot:
            filtered_df = filtered_df[filtered_df['2.Nro de O.T.'].astype(str).str.contains(ot)]
        if nodo:
            filtered_df = filtered_df[filtered_df['1.NODO DEL POSTE.'].astype(str).str.contains(nodo)]
        
        # Filtrar por fecha seleccionada
        filtered_df = filtered_df[
            filtered_df['FechaCreacion'].dt.strftime('%d/%m/%Y') == fecha_seleccionada
        ]
        
        # Extraer horas únicas
        horas_disponibles = sorted(filtered_df['FechaCreacion'].dt.strftime('%H:%M').unique())
        return [{'label': h, 'value': h} for h in horas_disponibles], None, False
    
    @app.callback(
        Output('filtro-fecha-sincro', 'start_date'),
        Output('filtro-fecha-sincro', 'end_date'),
        Input('stored-data', 'data')
    )
    def update_datepicker(data):
        if not data:
            return dash.no_update, dash.no_update
        df = pd.read_json(data['df'], orient='split')
        # Convertir la columna a datetime en caso de que no lo sea
        df['FechaCreacion'] = pd.to_datetime(df['FechaCreacion'], errors='coerce')
        min_date = df['FechaCreacion'].min()
        max_date = df['FechaCreacion'].max()
        # DatePickerRange espera fechas en formato ISO (YYYY-MM-DD)
        return min_date.date().isoformat(), max_date.date().isoformat()
        
    @app.callback(
        Output('mapa', 'figure'),
        [Input('boton-filtrar', 'n_clicks'),
         Input('tipo-ruta', 'value')],
        [State('filtro-tecnico', 'value'),
         State('filtro-ot', 'value'),
         State('filtro-nodo', 'value'),
         State('filtro-fecha', 'value'),
         State('filtro-hora', 'value'),
         State('stored-data', 'data')]  # <-- Añadir este State
    )
    def actualizar_mapa(n_clicks, tipo_ruta, tecnicos, ot, nodo, fecha, hora, data):
        
        if not data:
            return go.Figure()
        
        # Leer el DataFrame y convertir la columna 'FechaCreacion' a datetime
        df = pd.read_json(data['df'], orient='split')
        df['FechaCreacion'] = pd.to_datetime(df['FechaCreacion'], errors='coerce')
        
        colores = data['colores']
        filtered_df = df.copy()
        
        # Aplicar filtros
        if tecnicos:
            filtered_df = filtered_df[filtered_df['Tecnico_Clean'].isin(tecnicos)]
        if ot:
            filtered_df = filtered_df[filtered_df['2.Nro de O.T.'].astype(str).str.contains(ot)]
        if nodo:
            filtered_df = filtered_df[filtered_df['1.NODO DEL POSTE.'].astype(str).str.contains(nodo)]
        
        # Filtro por fecha (independiente de la hora)
        if fecha:
            try:
                fecha_dt = pd.to_datetime(fecha, format='%d/%m/%Y')
                filtered_df = filtered_df[
                    filtered_df['FechaCreacion'].dt.date == fecha_dt.date()
                ]
                
                # Filtro adicional por hora si está seleccionada
                if hora:
                    hora_dt = datetime.strptime(hora, "%H:%M").time()
                    filtered_df = filtered_df[
                        filtered_df['FechaCreacion'].dt.time == hora_dt
                    ]
            except:
                print("Error en formato de fecha/hora")
        
        # Ordenar y asignar secuencia
        filtered_df = filtered_df.sort_values(
            ['Tecnico_Clean', 'FechaCreacion'], 
            ascending=[True, True]  # Orden ascendente
        )
        
        # Asignar secuencia numérica por técnico
        filtered_df['Secuencia'] = filtered_df.groupby('Tecnico_Clean').cumcount() + 1
        
        # Ordenar y asignar secuencia
        if not filtered_df.empty:        
            
            if len(filtered_df) == 1:
                lat_center = filtered_df.iloc[0]['Latitud']
                lon_center = filtered_df.iloc[0]['Longitud']
                zoom_level = 14  # Zoom más cercano para un solo punto
            else:
                random_point = filtered_df.sample(1).iloc[0]
                lat_center = random_point['Latitud']
                lon_center = random_point['Longitud']
                zoom_level = 12
        else:
            lat_center = 4.570868 if 'Latitud' in df.columns else 0
            lon_center = -74.297333 if 'Longitud' in df.columns else 0
            zoom_level = 10
            
        fig1 = go.Figure()
        
        # Agregar marcadores con hovertext y customdata
        fig1.add_trace(go.Scattermapbox(
            lat=filtered_df['Latitud_adj'],
            lon=filtered_df['Longitud_adj'],
            mode='markers+text',
            marker=go.scattermapbox.Marker(
                size=12,
                # En el callback actualizar_mapa, modifica:
                color=[colores.get(tecnico, "rgb(128,128,128)") for tecnico in filtered_df['Tecnico_Clean']]
            ),
            text=filtered_df['Secuencia'].astype(str),
            textposition="top center",
            textfont=dict(size=12, color="black"),
            customdata=filtered_df[[
                'Tecnico_Clean',            
                '2.Nro de O.T.',
                '1.NODO DEL POSTE.',            
                'FechaCreacion',
                'Latitud',
                'Longitud',
                'Ubicacion'  
            ]],
            hoverinfo='text',
            hovertext=filtered_df.apply(lambda row: 
                f"Técnico: {row['Tecnico_Clean']}<br>" +
                f"OT: {row['2.Nro de O.T.']}<br>" +
                f"Nodo: {row['1.NODO DEL POSTE.']}<br>" +
                f"Fecha Creación: {row['FechaCreacion'].strftime('%d/%m/%Y %H:%M')}<br>" +
                f"Latitud: {row['Latitud']:.5f}<br>" +  # <-- Nueva línea
                f"Longitud: {row['Longitud']:.5f}",  # <-- Nueva línea
                axis=1
            ),
            name='Puntos'
        ))
        
        # Agregar rutas (código existente)
        if tipo_ruta in ['individuales', 'todas']:
            for tecnico, grupo in filtered_df.groupby('Tecnico_Clean'):
                grupo = grupo.sort_values('FechaCreacion')
                if len(grupo) >= 1:
                    fig1.add_trace(go.Scattermapbox(
                        lat=grupo['Latitud_adj'],
                        lon=grupo['Longitud_adj'],
                        mode='lines+markers+text',
                        line=dict(width=2, color=colores[tecnico]),
                        marker=dict(size=10),
                        text=grupo['Secuencia'].astype(str), 
                        textposition="top center",
                        textfont=dict(size=12, color="black"),
                        name=f'Ruta {tecnico}',
                        customdata=grupo[[  # <-- Usar 'grupo' en lugar de 'filtered_df'
                            'Tecnico_Clean',                    
                            '2.Nro de O.T.',
                            '1.NODO DEL POSTE.',                    
                            'FechaCreacion',
                            'Latitud',
                            'Longitud',
                            'Ubicacion'  
                        ]],
                        hoverinfo='text',
                        hovertext=grupo.apply(lambda row:
                            f"Técnico: {row['Tecnico_Clean']}<br>" +
                            f"OT: {row['2.Nro de O.T.']}<br>" +
                            f"Nodo: {row['1.NODO DEL POSTE.']}<br>" +
                            f"Fecha Creación: {row['FechaCreacion'].strftime('%d/%m/%Y %H:%M')}<br>" +
                            f"Latitud: {row['Latitud']:.5f}<br>" +  # <-- Nueva línea
                            f"Longitud: {row['Longitud']:.5f}",  # <-- Nueva línea
                            axis=1
                        ),
                ))
        
        # Configurar layout
        fig1.update_layout(
            mapbox_style="open-street-map",
            margin={"r":70,"t":0,"l":0,"b":40},
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            mapbox=dict(
                center=dict(lat=lat_center, lon=lon_center),
                zoom=zoom_level
            )
        )
        
        return fig1
    
    # Callback para mostrar detalles del punto
    @app.callback(
        Output('detalle-punto', 'children'),
        Input('mapa', 'clickData')
    )
    def mostrar_detalles(clickData):
        if not clickData or 'customdata' not in clickData['points'][0]:
            return "Seleccione un punto en el mapa para ver detalles"
        
        punto = clickData['points'][0]
        fecha_sincro = pd.to_datetime(punto['customdata'][3])
        ubicacion = punto['customdata'][6]  # Índice 6 = Ubicacion
        
        return html.Div([
            html.H4("Detalles de la Instalación"),
            html.P(f"Técnico: {punto['customdata'][0]}"),
            html.P(f"OT: {punto['customdata'][1]}"),
            html.P(f"Nodo: {punto['customdata'][2]}"),
            html.P(f"Fecha Creación: {fecha_sincro.strftime('%d/%m/%Y %H:%M')}"),
            html.P(f"Latitud: {punto['customdata'][4]:.5f}" f"    Longitud: {punto['customdata'][5]:.5f}"),  # Índice 4
            #html.P(f"Longitud: {punto['customdata'][5]:.5f}"),  # Índice 5
            html.P(html.A(
                "Ver en Google Maps",
                href=ubicacion,
                target="_blank",
                style={'color': 'blue', 'textDecoration': 'underline'}
            )) if ubicacion else html.P("Ubicación no disponible")
        ])