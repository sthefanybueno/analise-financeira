from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.templating import Jinja2Templates
from analise import gerar_analise

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def render_template(template_name: str, request: Request, context: dict = None, status_code: int = 200):
    """
    Renderiza um template Jinja2 de forma compatível com todas as versões
    do Starlette / FastAPI (novas e legadas).
    """
    ctx = dict(context) if context else {}
    ctx["request"] = request
    try:
        # Padrão moderno do Starlette (0.29.0+): request explícito ou por keyword
        return templates.TemplateResponse(request=request, name=template_name, context=ctx, status_code=status_code)
    except TypeError:
        # Padrão legado do Starlette (< 0.29.0)
        return templates.TemplateResponse(template_name, ctx, status_code=status_code)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Retorna status 204 (No Content) para requisições de favicon, evitando erros 404 no console."""
    return Response(status_code=204)


@app.get("/")
def home(request: Request):
    """
    Esta função é executada quando o usuário acessa a URL raiz ('/').
    Ela renderiza e retorna a página inicial interativa (home.html).
    """
    return render_template("home.html", request)


@app.get("/api/analise/{ticker}")
def obter_analise_json(ticker: str):
    """
    Esta é uma rota de API pura. Ela retorna os dados em formato JSON.
    É útil se você quiser que outro programa consuma os dados, em vez de um humano vendo uma página web.
    """
    stats, explicacao, dados_interativos, ticker_resolvido, fundamentalistas = gerar_analise(ticker.upper())
    
    if not stats:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' não encontrado.")
    
    stats_formatado = {key: f"{value:.2f}" for key, value in stats.items()}
    
    return {
        "ticker_analisado": ticker_resolvido,
        "estatisticas": stats_formatado,
        "explicacao_analise": explicacao,
        "dados_grafico": dados_interativos,
        "indicadores_fundamentalistas": fundamentalistas
    }


@app.get("/relatorio/{ticker}")
def gerar_relatorio_web(ticker: str, request: Request):
    """
    Esta é a rota principal para o usuário. Ela gera a análise e decide qual página HTML mostrar:
    - Se a análise for bem-sucedida, mostra 'resultado.html' com todos os dados.
    - Se a análise falhar, mostra 'erro.html' com uma mensagem amigável.
    """
    print(f"Gerando relatório web para o ticker: {ticker}")
    
    stats, explicacao, dados_interativos, ticker_resolvido, fundamentalistas = gerar_analise(ticker.upper())

    if not stats:
        contexto_erro = {
            "ticker": ticker.upper()
        }
        return render_template("erro.html", request, contexto_erro, status_code=404)

    stats_formatado = {key: f"{value:.2f}" for key, value in stats.items()}
 
    contexto_sucesso = {
        "ticker": ticker_resolvido,
        "estatisticas": stats_formatado,
        "explicacao": explicacao,
        "dados_grafico": dados_interativos,
        "fundamentalistas": fundamentalistas
    }

    return render_template("resultado.html", request, contexto_sucesso)