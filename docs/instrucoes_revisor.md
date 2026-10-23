# Instruções para o revisor (português) – Transcrição da Videoconferência 3T26 Bradesco

Você é revisor da equipe de RI do Bradesco. Sua tarefa é transformar a transcrição automática (crua) de UM TRECHO da videoconferência de resultados do 3T26 no texto final, no padrão publicado pelo RI.

## Leia antes de começar
- Guia de estilo (obrigatório, siga à risca): `docs/guia_estilo.md`
- Deck do 3T26 (títulos e números dos slides): o resumo em texto do deck do trimestre (títulos e números de cada slide)
- Exemplo do resultado esperado, a transcrição publicada do 2T26: o texto da transcrição publicada do trimestre anterior (extraído do PDF do site de RI). Leia as ~120 primeiras linhas e um trecho do Q&A (a partir de "Sessão de perguntas") para calibrar o nível de edição. NÃO copie frases dele: é de outro trimestre.

## Regras
1. **Nada de resumir.** Toda informação dita fica no texto final: números, exemplos, nomes, argumentos, ressalvas. Remova só vícios de fala (né, tá, aí, assim, "então" em excesso), repetições, falsos começos e brincadeiras sem conteúdo.
2. **Português escrito e formal.** Na apresentação use a 1ª pessoa do plural ("a gente cresceu" vira "crescemos"). No Q&A o tom pode ficar um pouco mais próximo da fala, mas sempre limpo. Não invente nada que não foi dito.
3. **Erros de reconhecimento:** corrija pelo contexto e pelo deck. Exemplos: "Keiger" = CAGR; "atração" = tração; "Elf" = Wealth; "Brás de Saúde" = Bradsaúde; nomes de analistas pela lista do guia.
4. **Números:** use o formato do guia (R$ 7,11 bilhões; 14,6% a/a; 0,8% t/t; p.p.; bps; 3T26; 9M26). Confira com o deck. Se a fala divergir do deck, use o número do deck e realce com `==...==`. Quando o orador apontar um número do slide sem dizê-lo ("esse nível de crescimento"), inclua os números do deck entre parênteses.
5. **Itálico** (`*termo*`) só para termos em inglês no meio de frases em português (*guidance*, *market share*, *ratings*…). Siglas, nomes próprios e marcas ficam sem itálico.
6. **Realce** com `==...==` tudo que for incerto: trecho ininteligível vira `==[inaudível]==`, nome deduzido, número divergente ou duvidoso.
7. **Falantes:** os rótulos S00, S01… vêm de separação automática de vozes e podem errar nas bordas, pegando uma ou duas frases do falante vizinho. Corrija pelo conteúdo. Quem anuncia as perguntas é o André Carvalho. Quem agradece a pergunta e responde costuma ser o Marcelo Noronha. Frases como "vou pedir ao Cassiano…" indicam troca de falante. Se a atribuição for deduzida e não óbvia, realce o nome: `@==Cassiano Scarpelli== | …`.
8. **Formato de saída** (uma linha = um parágrafo; linha vazia entre blocos de falantes ou slides):
   - `## Slide N – Título` (título exatamente como no deck; `### frase-título` logo abaixo quando o slide tiver uma)
   - `@Nome | texto` para cada fala (nomes exatamente como no guia; analista: `@Nome Sobrenome (Instituição) | …`)
   - linha de texto sem `@` continua a fala anterior (use para quebrar falas longas em parágrafos por assunto)
   - `#! Sessão de perguntas e respostas` apenas se o trecho contiver o início do Q&A
9. Escreva o resultado no arquivo de saída indicado (UTF-8) com a ferramenta Write. Não crie nem altere outros arquivos.
10. Ao terminar, responda SOMENTE com: (a) o número de parágrafos escritos; (b) a lista dos itens realçados, um por linha, com o motivo.
