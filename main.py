import streamlit as st
import requests
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Análisis de Arbitraje Cripto", layout="wide")

st.title("💱 Análisis de Arbitraje USD/USDT")
st.markdown("---")

# Exchanges argentinos
EXCHANGES_ARGENTINOS = [
    'decrypto', 'binancep2p', 'tiendacrypto', 'buenbit', 
    'letsbit', 'fiwind', 'belo', 'satoshitango','lemoncash','cocos','astropay'
]

# Sidebar para configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    capital_inicial_ars = st.number_input(
        "Capital inicial (ARS)", 
        min_value=1000, 
        value=1000000, 
        step=10000
    )
    
    st.markdown("---")
    st.markdown("### ℹ️ Información")
    st.info("Este cálculo NO incluye:\n- Comisiones\n- Impuestos\n- Costos de transferencia")

# Función para obtener datos
@st.cache_data(ttl=60)
def obtener_datos():
    # ComparaDólar
    url_comparadolar = 'https://api.comparadolar.ar/quotes'
    response_cd = requests.get(url_comparadolar)
    datos_cd = response_cd.json()
    
    # Filtrar solo los que tienen precio de venta (ask) válido
    proveedores_usd = []
    for item in datos_cd:
        if isinstance(item, dict) and item.get('ask'):
            proveedores_usd.append({
                'name': item.get('name'),
                'prettyName': item.get('prettyName', item.get('name')),
                'ask': item.get('ask'),
                'bid': item.get('bid'),
                'is24x7': item.get('is24x7', False)
            })
    
    # Ordenar por precio ASK (de menor a mayor) para encontrar los más baratos
    proveedores_usd.sort(key=lambda x: x['ask'])
    
    # USDT/USD
    url_usdt_usd = 'https://criptoya.com/api/USDT/USD/0.1'
    response_usdt_usd = requests.get(url_usdt_usd)
    datos_usdt_usd = response_usdt_usd.json()
    
    # USDT/ARS
    url_usdt_ars = 'https://criptoya.com/api/USDT/ARS/0.1'
    response_usdt_ars = requests.get(url_usdt_ars)
    datos_usdt_ars = response_usdt_ars.json()
    
    return proveedores_usd, datos_usdt_usd, datos_usdt_ars

# Función para calcular arbitraje
def calcular_arbitraje(capital, proveedor_usd, exchange_compra, exchange_venta):
    usd_comprados = capital / proveedor_usd['ask']
    ask_usdt = exchange_compra['ask']
    usdt_comprados = usd_comprados / ask_usdt
    bid_ars = exchange_venta['bid']
    ars_finales = usdt_comprados * bid_ars
    ganancia = ars_finales - capital
    porcentaje = (ganancia / capital) * 100
    
    return {
        'proveedor_usd': proveedor_usd['prettyName'],
        'precio_usd': proveedor_usd['ask'],
        'compra_exchange': exchange_compra['exchange'],
        'venta_exchange': exchange_venta['exchange'],
        'usd_comprados': usd_comprados,
        'usdt_comprados': usdt_comprados,
        'ars_finales': ars_finales,
        'ganancia': ganancia,
        'porcentaje': porcentaje,
        'ask_usdt': ask_usdt,
        'bid_ars': bid_ars
    }

# Botón para actualizar datos
if st.button("🔄 Actualizar Cotizaciones"):
    st.cache_data.clear()

try:
    # Obtener datos
    with st.spinner("Obteniendo cotizaciones..."):
        proveedores_usd, datos_usdt_usd, datos_usdt_ars = obtener_datos()
    
    # Mostrar las 2 mejores opciones para comprar USD
    st.subheader("💵 Mejores opciones para comprar USD")
    col1, col2 = st.columns(2)
    
    if len(proveedores_usd) >= 1:
        with col1:
            st.metric(
                f"1º {proveedores_usd[0]['prettyName']}", 
                f"${proveedores_usd[0]['ask']:,.2f}"
            )
    
    if len(proveedores_usd) >= 2:
        with col2:
            st.metric(
                f"2º {proveedores_usd[1]['prettyName']}", 
                f"${proveedores_usd[1]['ask']:,.2f}"
            )
    
    st.metric("💰 Capital Inicial", f"${capital_inicial_ars:,.2f}")
    
    # Procesar exchanges USDT
    exchanges_compra_usdt = []
    for exchange, info in datos_usdt_usd.items():
        if isinstance(info, dict) and info.get('totalAsk'):
            if exchange.lower() in EXCHANGES_ARGENTINOS:
                exchanges_compra_usdt.append({
                    'exchange': exchange,
                    'ask': info['totalAsk']
                })
    exchanges_compra_usdt.sort(key=lambda x: x['ask'])
    
    exchanges_venta_usdt = []
    for exchange, info in datos_usdt_ars.items():
        if isinstance(info, dict) and info.get('totalBid'):
            if exchange.lower() in EXCHANGES_ARGENTINOS:
                exchanges_venta_usdt.append({
                    'exchange': exchange,
                    'bid': info['totalBid']
                })
    exchanges_venta_usdt.sort(key=lambda x: x['bid'], reverse=True)
    
    # Calcular todas las combinaciones
    resultados = []
    
    # Combinaciones con el proveedor más barato de USD
    if len(proveedores_usd) >= 1:
        if len(exchanges_compra_usdt) >= 1 and len(exchanges_venta_usdt) >= 1:
            resultados.append({
                'titulo': f'Opción 1: {proveedores_usd[0]["prettyName"]} + Mejor USDT compra/venta',
                **calcular_arbitraje(capital_inicial_ars, proveedores_usd[0],
                                   exchanges_compra_usdt[0], exchanges_venta_usdt[0])
            })
        
        if len(exchanges_compra_usdt) >= 1 and len(exchanges_venta_usdt) >= 2:
            resultados.append({
                'titulo': f'Opción 2: {proveedores_usd[0]["prettyName"]} + Mejor USDT compra/2do venta',
                **calcular_arbitraje(capital_inicial_ars, proveedores_usd[0],
                                   exchanges_compra_usdt[0], exchanges_venta_usdt[1])
            })
    
    # Combinaciones con el segundo proveedor más barato de USD
    if len(proveedores_usd) >= 2:
        if len(exchanges_compra_usdt) >= 1 and len(exchanges_venta_usdt) >= 1:
            resultados.append({
                'titulo': f'Opción 3: {proveedores_usd[1]["prettyName"]} + Mejor USDT compra/venta',
                **calcular_arbitraje(capital_inicial_ars, proveedores_usd[1],
                                   exchanges_compra_usdt[0], exchanges_venta_usdt[0])
            })
        
        if len(exchanges_compra_usdt) >= 1 and len(exchanges_venta_usdt) >= 2:
            resultados.append({
                'titulo': f'Opción 4: {proveedores_usd[1]["prettyName"]} + Mejor USDT compra/2do venta',
                **calcular_arbitraje(capital_inicial_ars, proveedores_usd[1],
                                   exchanges_compra_usdt[0], exchanges_venta_usdt[1])
            })
    
    # Mostrar resultados
    st.markdown("---")
    st.header("📊 Análisis de Opciones")
    
    df_resultados = pd.DataFrame(resultados)
    df_resultados = df_resultados.sort_values('ganancia', ascending=False)
    
    # Mostrar mejor opción destacada
    mejor = df_resultados.iloc[0]
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.success(f"### 🏆 {mejor['titulo']}")
    with col2:
        st.metric(
            "Ganancia/Pérdida", 
            f"${mejor['ganancia']:,.2f}",
            f"{mejor['porcentaje']:.2f}%"
        )
    
    # Detalles de la mejor opción
    with st.expander("Ver detalles de la operación", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**📥 PASO 1: Comprar USD**")
            st.write(f"🏦 En: **{mejor['proveedor_usd']}**")
            st.write(f"💵 Precio: ${mejor['precio_usd']:,.2f} ARS/USD")
            st.write(f"📊 USD comprados: ${mejor['usd_comprados']:,.2f}")
        
        with col2:
            st.markdown(f"**💱 PASO 2: Comprar USDT**")
            st.write(f"🏦 En: **{mejor['compra_exchange']}**")
            st.write(f"💵 Precio: ${mejor['ask_usdt']:.4f} USD/USDT")
            st.write(f"📊 USDT: {mejor['usdt_comprados']:,.4f}")
        
        with col3:
            st.markdown(f"**📤 PASO 3: Vender USDT**")
            st.write(f"🏦 En: **{mejor['venta_exchange']}**")
            st.write(f"💵 Precio: ${mejor['bid_ars']:,.2f} ARS/USDT")
            st.write(f"📊 ARS finales: ${mejor['ars_finales']:,.2f}")
    
    # Tabla comparativa
    st.markdown("### 📋 Comparativa de todas las opciones")
    
    tabla_comparativa = df_resultados[['titulo', 'proveedor_usd', 'compra_exchange', 'venta_exchange', 'ganancia', 'porcentaje']].copy()
    tabla_comparativa.columns = ['Opción', 'Compra USD en', 'Compra USDT en', 'Vende USDT en', 'Ganancia (ARS)', 'Rendimiento (%)']
    tabla_comparativa['Ganancia (ARS)'] = tabla_comparativa['Ganancia (ARS)'].apply(lambda x: f"${x:,.2f}")
    tabla_comparativa['Rendimiento (%)'] = tabla_comparativa['Rendimiento (%)'].apply(lambda x: f"{x:+.2f}%")
    
    st.dataframe(tabla_comparativa, use_container_width=True, hide_index=True)
    
    # Gráfico de barras
    st.markdown("### 📈 Visualización de resultados")
    chart_data = df_resultados[['titulo', 'ganancia']].copy()
    chart_data.columns = ['Opción', 'Ganancia']
    st.bar_chart(chart_data.set_index('Opción'))
    
    # Mostrar todos los proveedores disponibles
    with st.expander("Ver todos los proveedores de USD disponibles"):
        df_proveedores = pd.DataFrame(proveedores_usd)
        df_proveedores = df_proveedores[['prettyName', 'ask', 'bid', 'is24x7']]
        df_proveedores.columns = ['Proveedor', 'Compra (Ask)', 'Venta (Bid)', '24/7']
        st.dataframe(df_proveedores, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error al obtener datos: {str(e)}")
    st.info("Intenta actualizar las cotizaciones en unos segundos.")