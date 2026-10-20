import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def gerar_explicacao_grafico(ticker: str, estatisticas: dict):
    ultimo_preco = estatisticas['ultimo_valor']
    mediana_preco = estatisticas['mediana']
    
    explicacao = (
        f"Esta é uma análise técnica para o ativo {ticker.upper()}.\n\n"
        f"O gráfico de linha (azul) mostra a variação do preço de fechamento diário do ativo.\n\n"
        f"O gráfico contém as seguintes linhas de referência:\n"
        f" - Linha Vermelha: É a média móvel simples de 20 dias (MMS20). Ela suaviza os preços e ajuda a identificar a tendência de curto prazo do ativo.\n"
        f" - Linha Laranja (tracejada): É a Mediana de todo o período, o valor que divide os preços exatamente ao meio.\n"
        f" - Linhas de Desvio Padrão (pontilhadas): Marcam as zonas de volatilidade com cores distintas:\n"
        f"    - Verde: Para ±1 desvio padrão, onde cerca de 68% dos preços costumam estar.\n"
        f"    - Roxo: Para ±2 desvios padrão, abrangendo cerca de 95% dos preços.\n"
        f"    - Ciano: Para ±3 desvios padrão, indicando faixas de preço menos comuns.\n\n"
        f"Estatísticas Principais (baseadas em todo o período de 2 anos):\n"
        f"- Último Preço de Fechamento: R$ {ultimo_preco:.2f}\n"
        f"- Preço Médio no Período: R$ {estatisticas['media']:.2f}\n"
        f"- Mediana no Período: R$ {mediana_preco:.2f}\n"
        f"- Volatilidade (Desvio Padrão): R$ {estatisticas['desvio_padrao']:.2f}\n"
        f"- Faixa de Preço no Período: R$ {estatisticas['minimo']:.2f} (mín) a R$ {estatisticas['maximo']:.2f} (máx)"
    )
    return explicacao

def gerar_analise(ticker: str):
    """
    Função principal que retorna estatísticas, explicação, dados do gráfico interativo e o ticker resolvido.
    """
    ticker_original = ticker.upper().strip()
    data_final = datetime.now()
    data_inicial = data_final - timedelta(days=730)

    # 1. Tenta baixar os dados com o ticker exatamente como foi digitado
    dados = yf.download(ticker_original, start=data_inicial, end=data_inicial + timedelta(days=730), auto_adjust=False, progress=False) # Limitando a 2 anos exatos

    ticker_final = ticker_original

    # 2. Se o ticker não tiver ponto nem hífen e retornar vazio, tenta automaticamente com o sufixo .SA (B3)
    if (dados.empty or len(dados) == 0) and '.' not in ticker_original and '-' not in ticker_original:
        ticker_sa = f"{ticker_original}.SA"
        dados_sa = yf.download(ticker_sa, start=data_inicial, end=data_inicial + timedelta(days=730), auto_adjust=False, progress=False)
        if not dados_sa.empty and len(dados_sa) > 0:
            dados = dados_sa
            ticker_final = ticker_sa

    if dados.empty or len(dados) == 0:
        return None, None, None, ticker_original

    if isinstance(dados.columns, pd.MultiIndex):
        dados.columns = dados.columns.droplevel(1)
        
    dados = dados[:-1]

    preco_fechamento = dados['Close']
    estatisticas = {
        "media": preco_fechamento.mean(),
        "mediana": preco_fechamento.median(),
        "desvio_padrao": preco_fechamento.std(),
        "minimo": preco_fechamento.min(),
        "maximo": preco_fechamento.max(),
        "ultimo_valor": preco_fechamento.iloc[-1]
    }
    
    # Calcular média móvel sobre o histórico completo de 2 anos
    periodo_media_movel = 20
    dados = dados.copy()
    dados[f'SMA{periodo_media_movel}'] = dados['Close'].rolling(window=periodo_media_movel).mean()

    media_total = estatisticas['media']
    mediana = estatisticas['mediana']
    dp = estatisticas['desvio_padrao']

    explicacao = gerar_explicacao_grafico(ticker_final, estatisticas)

    # Preparar pontos para o gráfico dinâmico com o período completo (até 2 anos)
    # permitindo selecionar 6 meses, 1 ano ou 2 anos na interface
    pontos_preco = []
    pontos_mms20 = []
    for data_idx, linha in dados.iterrows():
        ts_ms = int(data_idx.timestamp() * 1000)
        preco = round(float(linha['Close']), 2)
        pontos_preco.append([ts_ms, preco])
        
        val_sma = linha.get(f'SMA{periodo_media_movel}')
        if pd.notnull(val_sma):
            pontos_mms20.append([ts_ms, round(float(val_sma), 2)])

    dados_interativos = {
        "serie_preco": pontos_preco,
        "serie_mms20": pontos_mms20,
        "mediana": round(float(mediana), 2),
        "dp_pos1": round(float(media_total + dp), 2),
        "dp_neg1": round(float(media_total - dp), 2),
        "dp_pos2": round(float(media_total + 2 * dp), 2),
        "dp_neg2": round(float(media_total - 2 * dp), 2),
        "dp_pos3": round(float(media_total + 3 * dp), 2),
        "dp_neg3": round(float(media_total - 3 * dp), 2),
    }

    return estatisticas, explicacao, dados_interativos, ticker_final