from dash import dcc, html
import dash_bootstrap_components as dbc

def crear_layout():
    return html.Div([
        dbc.Container([
            html.H1("Mapa Interactivo de Instalaciones", 
                    className="text-center my-4", 
                    style={'color': '#343a40'}),
            
            dbc.Card(
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Arrastra y suelta o ',
                        html.A('Selecciona un archivo Excel', 
                               style={'color':'#007bff', 'textDecoration': 'none'})
                    ]),
                    style=upload_style()
                ),
                body=True, className="mb-4 shadow"
            ),
            
            dcc.Store(id='stored-data'),
            
            # Mapa en tamaño completo
            dbc.Row(
                dbc.Col(
                    dcc.Graph(
                        id='mapa',
                        style={'height': '75vh', 'margin-bottom': '20px'}  # Altura aumentada
                    ),
                    width=12
                )
            ),
            
            # Sección de controles y detalles debajo del mapa
            dbc.Row([
                dbc.Col([
                    dbc.Row(
                        dbc.Col(controles_filtros(), className="mb-4")
                    ),
                    dbc.Row(
                        dbc.Col(controles_fecha(), className="mb-4")
                    )
                ], width=8),
                
                dbc.Col(
                    panel_detalles(),
                    width=4,
                    style={'height': '50vh', 'overflow-y': 'auto'}  # Panel con scroll
                )
            ], className="g-4")  # Espacio entre columnas
        ], fluid=True)
    ], style={'backgroundColor': '#f8f9fa', 'padding': '20px'})

def upload_style():
    return {
        'width': '100%', 'height': '60px', 'lineHeight': '60px',
        'borderWidth': '2px', 'borderStyle': 'dashed',
        'borderRadius': '50px', 'textAlign': 'center', 'margin': '10px 0',
        'backgroundColor': '#ffffff', 'color': '#6c757d'
    }

def controles_filtros():
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                dcc.Dropdown(
                    id='tipo-ruta', 
                    options=[{'label': 'Rutas individuales', 'value': 'individuales'}],
                    value='individuales',
                    placeholder="Tipo de ruta",
                    className="mb-3"
                ),
                dcc.Dropdown(
                    id='filtro-tecnico', 
                    placeholder='Seleccionar técnicos', 
                    multi=True,
                    className="mb-3"
                ),
                dbc.InputGroup([
                    dbc.Input(
                        id='filtro-ot', 
                        placeholder='Número de OT', 
                        className="form-control"
                    ),
                ], className="mb-3"),
                dbc.InputGroup([
                    dbc.Input(
                        id='filtro-nodo', 
                        placeholder='Nodo del Poste', 
                        className="form-control"
                    ),
                ], className="mb-3"),
                dbc.Button('Aplicar Filtros', 
                          id='boton-filtrar', 
                          color="primary", 
                          className="w-100")
            ])
        ]),
        className="shadow-sm"
    )

def controles_fecha():
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                dcc.DatePickerRange(
                    id='filtro-fecha-sincro', 
                    display_format='DD/MM/YYYY',
                    className="mb-3"
                ),
                dcc.Dropdown(
                    id='filtro-fecha', 
                    placeholder='Seleccionar fecha',
                    className="mb-3"
                ),
                dcc.Dropdown(
                    id='filtro-hora', 
                    placeholder='Seleccionar hora',
                    className="mb-3"
                )
            ])
        ]),
        className="shadow-sm"
    )

def panel_detalles():
    return dbc.Card(
        dbc.CardBody([
            html.H4("Detalles del Punto", className="card-title"),
            html.Div(
                id='detalle-punto', 
                className='detail-panel',
                style={'padding': '10px'}
            )
        ]),
        className="shadow-sm h-100"  # Altura completa del contenedor
    )