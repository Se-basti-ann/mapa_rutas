from dash import Dash
import dash_bootstrap_components as dbc
from layout import crear_layout
from callbacks import registrar_callbacks

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = crear_layout()
registrar_callbacks(app)

if __name__ == '__main__':
    app.run_server(debug=True)