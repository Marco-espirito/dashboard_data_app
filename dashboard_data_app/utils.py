import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

def get_image():
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph

def generate_chart(chart_type, data):
    
    if 'date' not in data.columns or 'total_price' not in data.columns:
        raise ValueError("Les colonnes nécessaires sont manquantes dans les données.")
    
    data['date'] = data['date'].apply(lambda x: str(x)[:10])  
    plt.figure(figsize=(15, 5))

    if chart_type == 'bar':
        sns.barplot(x='date', y='total_price', data=data)
        plt.xticks(rotation=90)
    elif chart_type == 'line':
        sns.lineplot(x='date', y='total_price', data=data)
    elif chart_type == 'count':
        sns.countplot(x='date', data=data)
        plt.xticks(rotation=90)
    else:
        return None
    
    plt.subplots_adjust(bottom=0.5)
    plt.xlabel('Date', labelpad=20)

    return get_image()
