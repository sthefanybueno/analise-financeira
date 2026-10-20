import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def extrair_indicadores_fundamentalistas(ticker_simbolo: str):
    """
    Extrai indicadores de valuation, rentabilidade, liquidez e proventos
    utilizando a API do yfinance de forma segura e com tratamento de exceções.
    """
    try:
        ticker_obj = yf.Ticker(ticker_simbolo)
        info = ticker_obj.info or {}
    except Exception:
        info = {}

    if not info:
        return {
            "disponivel": False,
            "mensagem": "Dados fundamentalistas não encontrados ou indisponíveis para este ativo."
        }

    quote_type = info.get("quoteType", "EQUITY")
    is_equity = (
        quote_type in ("EQUITY", "ETF") or
        info.get("trailingPE") is not None or
        info.get("priceToBook") is not None or
        info.get("returnOnEquity") is not None
    )

    if not is_equity:
        return {
            "disponivel": False,
            "tipo": quote_type,
            "mensagem": "Ativo do tipo Criptomoeda/Índice/Moeda. Indicadores contábeis de balanço patrimonial, valuation e rentabilidade corporativa não se aplicam a esta classe de ativos."
        }

    def pct(val):
        if val is None or pd.isna(val):
            return "N/D"
        return f"{float(val) * 100:.2f}%"

    def num(val):
        if val is None or pd.isna(val):
            return "N/D"
        return f"{float(val):.2f}"

    def moeda(val, cur_simbolo="R$"):
        if val is None or pd.isna(val):
            return "N/D"
        return f"{cur_simbolo} {float(val):.2f}"

    def formatar_valor_grande(val, cur_simbolo="R$"):
        if val is None or pd.isna(val):
            return "N/D"
        v = float(val)
        if v >= 1e12:
            return f"{cur_simbolo} {v / 1e12:.2f} Tri"
        if v >= 1e9:
            return f"{cur_simbolo} {v / 1e9:.2f} Bi"
        if v >= 1e6:
            return f"{cur_simbolo} {v / 1e6:.2f} Mi"
        return f"{cur_simbolo} {v:,.2f}"

    moeda_simbolo = "R$" if (info.get("currency") == "BRL" or ".SA" in ticker_simbolo) else "$"

    setores_map = {
        'Energy': 'Energia / Petróleo, Gás e Biocombustíveis',
        'Financial Services': 'Serviços Financeiros / Bancos e Seguros',
        'Basic Materials': 'Materiais Básicos / Mineração e Siderurgia',
        'Utilities': 'Utilidade Pública / Energia Elétrica e Saneamento',
        'Consumer Defensive': 'Consumo Não Cíclico / Alimentos, Bebidas e Varejo Essencial',
        'Consumer Cyclical': 'Consumo Cíclico / Varejo, Vestuário e Construção',
        'Industrials': 'Bens Industriais / Logística, Transporte e Máquinas',
        'Healthcare': 'Saúde / Farmacêutica e Serviços Médicos',
        'Technology': 'Tecnologia da Informação e Software',
        'Communication Services': 'Comunicações e Telecomunicações',
        'Real Estate': 'Imobiliário / FIIs e Incorporação'
    }
    setor_original = info.get("sector", "N/D")
    setor_formatado = setores_map.get(setor_original, setor_original)

    # Dívida / PL (yfinance retorna em % ex: 76.067 para 76.07%)
    d_pl = info.get("debtToEquity")
    d_pl_formatado = f"{float(d_pl):.2f}%" if (d_pl is not None and not pd.isna(d_pl)) else "N/D"

    # Dividend Yield (trailingAnnualDividendYield é decimal puro ex: 0.0614 -> 6.14%)
    t_dy = info.get("trailingAnnualDividendYield")
    if t_dy is not None and not pd.isna(t_dy):
        dy_formatado = f"{float(t_dy) * 100:.2f}%"
    else:
        dy = info.get("dividendYield")
        if dy is not None and not pd.isna(dy):
            v = float(dy)
            dy_formatado = f"{v:.2f}%" if v > 0.01 else f"{v * 100:.2f}%"
        else:
            dy_formatado = "N/D"

    # Seleção exclusiva dos 6 indicadores fundamentais essenciais com resumo conciso em PT-BR
    indicadores_essenciais = [
        {
            "sigla": "P/L",
            "nome": "Preço sobre Lucro",
            "valor": num(info.get("trailingPE")),
            "resumo": "Anos para reaver o valor investido através dos lucros da empresa."
        },
        {
            "sigla": "P/VP",
            "nome": "Preço s/ Valor Patrimonial",
            "valor": num(info.get("priceToBook")),
            "resumo": "Preço da ação comparado ao seu patrimônio líquido contábil."
        },
        {
            "sigla": "DY",
            "nome": "Dividend Yield",
            "valor": dy_formatado,
            "resumo": "Rendimento percentual pago em dividendos nos últimos 12 meses."
        },
        {
            "sigla": "ROE",
            "nome": "Retorno s/ Patrimônio",
            "valor": pct(info.get("returnOnEquity")),
            "resumo": "Capacidade da empresa de gerar lucro com o dinheiro dos acionistas."
        },
        {
            "sigla": "Margem Líq.",
            "nome": "Margem Líquida",
            "valor": pct(info.get("profitMargins")),
            "resumo": "Porcentagem de lucro líquido que sobra a cada R$ 100 de receita."
        },
        {
            "sigla": "Dívida/PL",
            "nome": "Dívida s/ Patrimônio",
            "valor": d_pl_formatado,
            "resumo": "Nível de endividamento da empresa sobre seus recursos próprios."
        }
    ]

    return {
        "disponivel": True,
        "tipo": quote_type,
        "nome": info.get("longName") or info.get("shortName") or ticker_simbolo,
        "setor": setor_formatado,
        "valor_mercado": formatar_valor_grande(info.get("marketCap"), moeda_simbolo),
        "indicadores": indicadores_essenciais
    }


def gerar_explicacao_grafico(ticker: str, estatisticas: dict):
    ultimo_preco = estatisticas['ultimo_valor']
    mediana_preco = estatisticas['mediana']
    cv = estatisticas.get('coeficiente_variacao', 0.0)
    retorno = estatisticas.get('retorno_total', 0.0)
    
    explicacao = (
        f"Esta é uma análise técnica e estatística para o ativo {ticker.upper()}.\n\n"
        f"O gráfico de linha (azul) mostra a evolução do preço de fechamento diário do ativo.\n\n"
        f"Linhas e Parâmetros de Referência:\n"
        f" - Linha Vermelha: Média Móvel Simples de 20 dias (MMS20), suavizando oscilações e rastreando a tendência de curto prazo.\n"
        f" - Linha Laranja (tracejada): Mediana de todo o período, dividindo a distribuição dos preços ao meio (50% acima e 50% abaixo).\n"
        f" - Zonas de Volatilidade por Desvio Padrão (linhas pontilhadas):\n"
        f"    - Verde: ±1 Desvio Padrão (~68% das cotações sob distribuição normal).\n"
        f"    - Roxo: ±2 Desvios Padrão (~95% das cotações, indicando faixas de sobrecompra ou sobrevenda estatística).\n"
        f"    - Ciano: ±3 Desvios Padrão (~99.7% das cotações, marcando extremos raros de volatilidade).\n\n"
        f"Estatísticas Descritivas da Série Temporal (histórico de 2 anos):\n"
        f"- Último Preço de Fechamento: R$ {ultimo_preco:.2f}\n"
        f"- Preço Médio no Período: R$ {estatisticas['media']:.2f}\n"
        f"- Mediana no Período: R$ {mediana_preco:.2f}\n"
        f"- Volatilidade (Desvio Padrão Amostral): R$ {estatisticas['desvio_padrao']:.2f}\n"
        f"- Coeficiente de Variação (CV): {cv:.2f}% (mede a dispersão relativa e o risco proporcional do ativo)\n"
        f"- Retorno Acumulado no Período: {retorno:+.2f}%\n"
        f"- Faixa Histórica de Negociação: R$ {estatisticas['minimo']:.2f} (mín) a R$ {estatisticas['maximo']:.2f} (máx)"
    )
    return explicacao


def gerar_analise(ticker: str):
    """
    Função principal que retorna estatísticas, explicação, dados do gráfico interativo,
    o ticker resolvido e o conjunto de indicadores fundamentalistas.
    """
    ticker_original = ticker.upper().strip()
    data_final = datetime.now()
    data_inicial = data_final - timedelta(days=730)

    # 1. Tenta baixar os dados com o ticker exatamente como foi digitado
    dados = yf.download(ticker_original, start=data_inicial, end=data_inicial + timedelta(days=730), auto_adjust=False, progress=False)

    ticker_final = ticker_original

    # 2. Se o ticker não tiver ponto nem hífen e retornar vazio, tenta automaticamente com o sufixo .SA (B3)
    if (dados.empty or len(dados) == 0) and '.' not in ticker_original and '-' not in ticker_original:
        ticker_sa = f"{ticker_original}.SA"
        dados_sa = yf.download(ticker_sa, start=data_inicial, end=data_inicial + timedelta(days=730), auto_adjust=False, progress=False)
        if not dados_sa.empty and len(dados_sa) > 0:
            dados = dados_sa
            ticker_final = ticker_sa

    if dados.empty or len(dados) == 0:
        return None, None, None, ticker_original, None

    if isinstance(dados.columns, pd.MultiIndex):
        dados.columns = dados.columns.droplevel(1)
        
    dados = dados[:-1]

    preco_fechamento = dados['Close']
    primeiro_valor = float(preco_fechamento.iloc[0])
    ultimo_valor = float(preco_fechamento.iloc[-1])
    retorno_total = ((ultimo_valor - primeiro_valor) / primeiro_valor) * 100 if primeiro_valor != 0 else 0.0

    media = float(preco_fechamento.mean())
    dp = float(preco_fechamento.std())
    cv = (dp / media) * 100 if media != 0 else 0.0

    estatisticas = {
        "media": media,
        "mediana": float(preco_fechamento.median()),
        "desvio_padrao": dp,
        "coeficiente_variacao": cv,
        "retorno_total": retorno_total,
        "minimo": float(preco_fechamento.min()),
        "maximo": float(preco_fechamento.max()),
        "ultimo_valor": ultimo_valor
    }
    
    # Calcular média móvel sobre o histórico completo de 2 anos
    periodo_media_movel = 20
    dados = dados.copy()
    dados[f'SMA{periodo_media_movel}'] = dados['Close'].rolling(window=periodo_media_movel).mean()

    media_total = estatisticas['media']
    mediana = estatisticas['mediana']

    explicacao = gerar_explicacao_grafico(ticker_final, estatisticas)

    # Preparar pontos para o gráfico dinâmico com o período completo (até 2 anos)
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

    # Extração de indicadores fundamentalistas (Valuation, Eficiência, Rentabilidade, Proventos)
    fundamentalistas = extrair_indicadores_fundamentalistas(ticker_final)

    return estatisticas, explicacao, dados_interativos, ticker_final, fundamentalistas