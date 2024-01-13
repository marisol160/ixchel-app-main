from flask import Flask, render_template, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from io import BytesIO
import random
import matplotlib.pyplot as plt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:bH-g4--6CcGAbEged3FeCgaG4h1aceHC@monorail.proxy.rlwy.net:50514/msvc_ixchel_db'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/msvc_ixchel_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CONTENT_TYPE'] = 'application/pdf'  # Configuración para Matplotlib y Flask
db = SQLAlchemy(app)

class FrecuenciaCardiaca(db.Model):
    __tablename__ = 'frecuencia_cardiaca'
    id_registro_fc = db.Column(db.Integer, primary_key=True)
    pulsaciones = db.Column(db.Integer)
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)
    curp = db.Column(db.String(20))

class FrecuenciaRespiratoria(db.Model):
    __tablename__ = 'frecuencia_respiratoria'
    id_registro_fr = db.Column(db.Integer, primary_key=True)
    frecuencia_resp = db.Column(db.Integer)
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)
    curp = db.Column(db.String(20))

class Temperatura(db.Model):
    __tablename__ = 'temperatura'
    id_registro_tem = db.Column(db.Integer, primary_key=True)
    temperatura = db.Column(db.Float)
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)
    curp = db.Column(db.String(20))
    
class Infante(db.Model):
    __tablename__ = 'infante'
    
    curp = db.Column(db.String(18), primary_key=True)
    nombre_infante = db.Column(db.String(20))
    ap_paterno = db.Column(db.String(60))
    ap_materno = db.Column(db.String(60))
    sexo = db.Column(db.String(10))
    tipo_sangre = db.Column(db.String(6))
    fechanac = db.Column(db.Date)
    peso = db.Column(db.Float)
    talla = db.Column(db.Float)

    def __repr__(self): 
        return f"<Infante {self.curp}>"



def get_colors(data):
    colors = []
    for value in data:
        if value > 80:
            colors.append('rgba(255, 0, 0, 0.5)')  # Rojo
        elif value > 60:
            colors.append('rgba(255, 165, 0, 0.5)')  # Naranja
        else:
            colors.append('rgba(0, 128, 0, 0.5)')  # Verde
    return colors

with app.app_context():
    db.create_all()

@app.route('/get_chart_data/<curp>', methods=['GET'])
def get_chart_data(curp):
    data_fc_all = FrecuenciaCardiaca.query.filter(
        FrecuenciaCardiaca.curp == curp
    ).all()
    data_fr_all = FrecuenciaRespiratoria.query.filter(
        FrecuenciaRespiratoria.curp == curp
    ).all()
    data_tem_all = Temperatura.query.filter(
        Temperatura.curp == curp
    ).all()

    data_fc_all = [{'fecha_hora': entry.fecha_hora, 'pulsaciones': entry.pulsaciones} for entry in data_fc_all]
    data_fr_all = [{'fecha_hora': entry.fecha_hora, 'frecuencia_resp': entry.frecuencia_resp} for entry in data_fr_all]
    data_tem_all = [{'fecha_hora': entry.fecha_hora, 'temperatura': entry.temperatura} for entry in data_tem_all]

    grouped_data_fc = {}
    for entry in data_fc_all:
        month_year = entry['fecha_hora'].strftime('%B %Y')
        if month_year not in grouped_data_fc:
            grouped_data_fc[month_year] = {'labels': [], 'data': []}
        grouped_data_fc[month_year]['labels'].append(str(entry['fecha_hora']))
        grouped_data_fc[month_year]['data'].append(entry['pulsaciones'])

    grouped_data_fr = {}
    for entry in data_fr_all:
        month_year = entry['fecha_hora'].strftime('%B %Y')
        if month_year not in grouped_data_fr:
            grouped_data_fr[month_year] = {'labels': [], 'data': []}
        grouped_data_fr[month_year]['labels'].append(str(entry['fecha_hora']))
        grouped_data_fr[month_year]['data'].append(entry['frecuencia_resp'])

    grouped_data_tem = {}
    for entry in data_tem_all:
        month_year = entry['fecha_hora'].strftime('%B %Y')
        if month_year not in grouped_data_tem:
            grouped_data_tem[month_year] = {'labels': [], 'data': []}
        grouped_data_tem[month_year]['labels'].append(str(entry['fecha_hora']))
        grouped_data_tem[month_year]['data'].append(entry['temperatura'])

    chart_data = {}
    for month_year, data_fc in grouped_data_fc.items():
        chart_data[f'dataFC{month_year}'] = {
            'labels': data_fc['labels'],
            'datasets': [{
                'label': 'Frecuencia Cardiaca',
                'data': data_fc['data'],
                'backgroundColor': get_colors(data_fc['data']),
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1
            }],
            'title': f'Gráfica de Frecuencia Cardiaca para {month_year}'
        }

    for month_year, data_fr in grouped_data_fr.items():
        chart_data[f'dataFR{month_year}'] = {
            'labels': data_fr['labels'],
            'datasets': [{
                'label': 'Frecuencia Respiratoria',
                'data': data_fr['data'],
                'backgroundColor': get_colors(data_fr['data']),
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 1
            }],
            'title': f'Gráfica de Frecuencia Respiratoria para {month_year}'
        }

    for month_year, data_tem in grouped_data_tem.items():
        chart_data[f'dataTEM{month_year}'] = {
            'labels': data_tem['labels'],
            'datasets': [{
                'label': 'Temperatura',
                'data': data_tem['data'],
                'backgroundColor': get_colors(data_tem['data']),
                'borderColor': 'rgba(255, 0, 0, 1)',
                'borderWidth': 1
            }],
            'title': f'Gráfica de Temperatura para {month_year}'
        }

    return jsonify(chart_data)

@app.route('/generate_pdf/<curp>', methods=['GET'])
def generate_pdf(curp):
    try:
        response = get_chart_data(curp)
        chartData = response.json

        pdf_output = BytesIO()
        months = list(chartData.keys())

        plt.switch_backend('agg')

        for i, month in enumerate(months):
            fig, ax = plt.subplots()
            chartConfig = chartData[month]
            ax.set_title(chartConfig['title'])
            ax.set_xlabel('Fecha y hora')
            ax.set_ylabel(chartConfig['datasets'][0]['label'])
            ax.grid(True)
            plt.xticks(rotation=45)

            if chartConfig['labels']:
                print(f"Labels for {month}: {chartConfig['labels']}")
                print(f"Data for {month}: {chartConfig['datasets'][0]['data']}")

                ax.plot(chartConfig['labels'], chartConfig['datasets'][0]['data'], label=chartConfig['datasets'][0]['label'])
                ax.legend()

            # Guardar cada gráfica como una página separada en el PDF
            pdf_output.write(b'\x0c')  # Añadir un salto de página

        pdf_output.seek(0)

        response = make_response(pdf_output.read())
        response.headers['Content-Disposition'] = 'attachment; filename=graficas.pdf'
        response.headers['Content-Type'] = 'application/pdf'

        return response
    except Exception as e:
        print(f'Error al generar el PDF: {str(e)}')
        return jsonify({'error': 'Error al generar el PDF'}), 500
    
from matplotlib.backends.backend_pdf import PdfPages
from flask import make_response, jsonify
import seaborn as sns

@app.route('/generate_and_download_pdf/<curp>', methods=['GET'])
def generate_and_download_pdf(curp):
    try:
        response = get_chart_data(curp)
        chartData = response.json

        plt.switch_backend('agg')

        pdf_output = BytesIO()

        with PdfPages(pdf_output) as pdf_pages:
            for chart_type, data in chartData.items():
                fig, ax = plt.subplots(figsize=(12, 6))
                chartConfig = chartData[chart_type]

                # Configurar el estilo de las gráficas con seaborn
                sns.set(style="whitegrid", palette="muted")

                # Configurar la paleta de colores
                colors = sns.color_palette("muted")

                ax.set_title(chartConfig['title'], fontsize=16)
                ax.set_xlabel('Fecha y hora', fontsize=12)
                ax.set_ylabel(chartConfig['datasets'][0]['label'], fontsize=12)
                ax.grid(True)
                plt.xticks(rotation=45, ha='right')

                if chartConfig['labels']:
                    # Graficar puntos de datos con líneas suaves
                    sns.lineplot(x=chartConfig['labels'], y=chartConfig['datasets'][0]['data'], label=chartConfig['datasets'][0]['label'], marker='o', linestyle='-', color=colors[0], ax=ax)
                    ax.legend(fontsize=10)

                    # Añadir líneas de referencia y anotaciones
                    if chart_type.startswith('dataFC'):
                        ax.axhline(y=60, color='green', linestyle='--', label='Frecuencia Cardíaca Normal (60 bpm)')
                        ax.axhline(y=100, color='red', linestyle='--', label='Frecuencia Cardíaca Normal (100 bpm)')
                        ax.annotate('Frecuencia Cardíaca Normal (60 bpm)', xy=(0.5, 60), xytext=(0.5, 55), color='green', fontsize=10, ha='center', arrowprops=dict(facecolor='green', shrink=0.05))
                        ax.annotate('Frecuencia Cardíaca Normal (100 bpm)', xy=(0.5, 100), xytext=(0.5, 105), color='red', fontsize=10, ha='center', arrowprops=dict(facecolor='red', shrink=0.05))
                    elif chart_type.startswith('dataFR'):
                        ax.axhline(y=12, color='green', linestyle='--', label='Frecuencia Respiratoria Normal (12 rpm)')
                        ax.axhline(y=20, color='red', linestyle='--', label='Frecuencia Respiratoria Normal (20 rpm)')
                        ax.annotate('Frecuencia Respiratoria Normal (12 rpm)', xy=(0.5, 12), xytext=(0.5, 15), color='green', fontsize=10, ha='center', arrowprops=dict(facecolor='green', shrink=0.05))
                        ax.annotate('Frecuencia Respiratoria Normal (20 rpm)', xy=(0.5, 20), xytext=(0.5, 25), color='red', fontsize=10, ha='center', arrowprops=dict(facecolor='red', shrink=0.05))
                    elif chart_type.startswith('dataTEM'):
                        ax.axhline(y=36.5, color='green', linestyle='--', label='Temperatura Normal (36.5 °C)')
                        ax.axhline(y=37.5, color='red', linestyle='--', label='Temperatura Normal (37.5 °C)')
                        ax.annotate('Temperatura Normal (36.5 °C)', xy=(0.5, 36.5), xytext=(0.5, 35), color='green', fontsize=10, ha='center', arrowprops=dict(facecolor='green', shrink=0.05))
                        ax.annotate('Temperatura Normal (37.5 °C)', xy=(0.5, 37.5), xytext=(0.5, 38), color='red', fontsize=10, ha='center', arrowprops=dict(facecolor='red', shrink=0.05))

                if len(chartConfig['datasets']) > 1:
                    fig, ax = plt.subplots(figsize=(12, 6))
                    ax.set_title(chartConfig['title'], fontsize=16)
                    ax.set_xlabel('Fecha y hora', fontsize=12)
                    ax.set_ylabel(chartConfig['datasets'][1]['label'], fontsize=12)
                    ax.grid(True)
                    plt.xticks(rotation=45, ha='right')

                    if chartConfig['labels']:
                        # Graficar puntos de datos con líneas suaves
                        sns.lineplot(x=chartConfig['labels'], y=chartConfig['datasets'][1]['data'], label=chartConfig['datasets'][1]['label'], marker='o', linestyle='-', color=colors[1], ax=ax)
                        ax.legend(fontsize=10)

                pdf_pages.savefig(fig, bbox_inches='tight')
                plt.close(fig)

        pdf_output.seek(0)

        response = make_response(pdf_output.read())
        response.headers['Content-Disposition'] = f'attachment; filename={curp}_graficas.pdf'
        response.headers['Content-Type'] = 'application/pdf'

        return response
    except Exception as e:
        print(f'Error al generar el PDF: {str(e)}')
        return jsonify({'error': 'Error al generar el PDF'}), 500
               
@app.route('/predict_fc', methods=['POST'])
def predict_fc():
    try:
        curp = request.form.get('curp')
        fecha_hora = datetime.strptime(request.form.get('fecha_hora'), '%Y-%m-%d %H:%M:%S')
        edad = int(request.form.get('edad'))
        genero = request.form.get('genero')
        temperatura = float(request.form.get('temperatura'))
        frecuencia_resp = int(request.form.get('frecuencia_resp'))

        predicted_fc = random.randint(60, 100)

        new_data = {
            'curp': curp,
            'fecha_hora': fecha_hora,
            'temperatura': temperatura,
            'frecuencia_resp': frecuencia_resp
        }

        new_data['pulsaciones'] = int(predicted_fc)

        db.session.add(FrecuenciaCardiaca(**new_data))
        db.session.commit()

        return jsonify({'message': 'Datos agregados correctamente con predicción'})
    except Exception as e:
        print(f'Error en la predicción de Frecuencia Cardiaca: {str(e)}')
        return jsonify({'error': 'Error en la predicción de Frecuencia Cardiaca'}), 500


@app.route('/infante/<curp>', methods=['GET'])

def infante(curp):
    try:
        # Obtener información del infante
        infante_data = Infante.query.filter_by(curp=curp).first()

        if infante_data:
            
            return jsonify(
                infante={
                    'curp': infante_data.curp,
                    'nombre_infante': infante_data.nombre_infante,
                    'ap_paterno': infante_data.ap_paterno,
                    'ap_materno': infante_data.ap_materno,
                    'fechanac': infante_data.fechanac.strftime("%Y-%m-%d"),
                    'sexo': infante_data.sexo,
                    'tipo_sangre': infante_data.tipo_sangre,
                    'peso': infante_data.peso,
                    'talla': infante_data.talla
                    
                },
              
            )

        return jsonify(error='No se encontró información para el CURP'), 404

    except Exception as e:
        print(f"Error al realizar consultas a la base de datos: {e}")
        
        return jsonify(error='Error en la consulta a la base de datos'), 500



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
