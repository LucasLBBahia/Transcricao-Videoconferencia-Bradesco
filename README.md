# Transcrição Videoconferencia Bradesco

Processo para produzir a **Transcrição da Videoconferência de Resultados** do Bradesco no padrão publicado no site de RI, a partir da gravação da transmissão no YouTube. O processo transcreve com Whisper na GPU, separa os falantes, faz a revisão editorial em blocos e gera o Word no modelo do trimestre.

## Resultado no 3T26 (23/10/2026)

- 87,8 min de gravação viraram um Word revisado de 15 páginas: abertura, slides 2 a 15 e Q&A com 11 analistas. O arquivo traz 45 trechos realçados para conferência do RI.
- Um corte de 1min45 no áudio em português (aos 15:40) foi detectado e recuperado pelo canal "Áudio Original".
- No ensaio com o 2T26, comparando com a versão publicada:
  - só 0,4% do texto publicado ficou sem correspondência, num trecho de pergunta em inglês feita via intérprete;
  - 88% dos números saíram idênticos; o restante é edição feita pelo RI.

## Requisitos

- Windows com Python 3.12, `ffmpeg` e `yt-dlp` no PATH.
- GPU NVIDIA: testado numa RTX 2060 de 6 GB com `int8_float16`. Sem GPU também funciona, mas fica bem mais lento.
- Microsoft Word, só para converter o `.docx` em PDF e conferir o layout.

## Instalação

```bash
py -3.12 -m venv venv
venv/Scripts/python -m pip install -r requirements.txt
```

- O modelo Whisper large-v3 (~3 GB) é baixado sozinho na primeira execução.
- Os modelos de separação de falantes (sherpa-onnx) ficam numa pasta `modelos/`:
  - [sherpa-onnx-pyannote-segmentation-3-0.tar.bz2](https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2) (descompactar dentro de `modelos/`)
  - [wespeaker_en_voxceleb_resnet34_LM.onnx](https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/wespeaker_en_voxceleb_resnet34_LM.onnx)
- O PyAV recente não abre áudio pelo faster-whisper. Por isso os scripts leem WAV 16 kHz mono com `soundfile`.

## Passo a passo

**1. Baixar o áudio**, uma única vez, depois que a transmissão terminar. A página de RI publica três versões: português, original e inglês.

```bash
yt-dlp --live-from-start -f 140 -o "dados/pt.%(ext)s" "<link do canal em português>"
yt-dlp --live-from-start -f 140 -o "dados/original.%(ext)s" "<link do Áudio Original>"
```

Não consulte o YouTube em loop. Várias consultas seguidas geram bloqueio temporário (HTTP 429, "confirme que você não é um robô"). Se acontecer, espere o bloqueio passar; não tente contornar fazendo login.

**2. Converter para WAV 16 kHz mono**

```bash
ffmpeg -i dados/pt.m4a -ac 1 -ar 16000 dados/pt_16k.wav
```

**3. Procurar cortes de áudio.** Se o canal em português ficar mudo no meio de uma fala, transcreva o mesmo trecho do canal original. Os canais têm alguns segundos de defasagem entre si.

```bash
venv/Scripts/python scripts/verificar_cortes.py dados/pt_16k.wav
```

**4. Transcrever no modo sequencial.** Atualize o vocabulário a cada trimestre (executivos, analistas, siglas). Evite o `transcribe.py` (modo em lote): é mais rápido, mas no teste do 2T26 perdeu cerca de 4 minutos de fala.

```bash
venv/Scripts/python scripts/transcribe_seq.py dados/pt_16k.wav saidas/seq docs/vocabulario_whisper_3t26.txt
```

**5. Segunda passada nos buracos.** Confira o relatório `saidas/seq2_recuperado.txt` e apague as alucinações típicas do Whisper em trechos de silêncio, como "Legenda Adriana Zanotto".

```bash
venv/Scripts/python scripts/fill_gaps.py dados/pt_16k.wav saidas/seq.json saidas/seq2 docs/vocabulario_whisper_3t26.txt
```

**6. Separar falantes e juntar com a transcrição.** A separação acerta os pontos de troca de falante, mas pode misturar as vozes do estúdio. Por isso os nomes são atribuídos pelo conteúdo: o RI anuncia cada analista e os executivos passam a palavra pelo nome.

```bash
venv/Scripts/python scripts/diarize.py dados/pt_16k.wav saidas/diar.json modelos/wespeaker_en_voxceleb_resnet34_LM.onnx 0.6
venv/Scripts/python scripts/merge.py saidas/seq2.json saidas/diar.json saidas/turnos.txt
```

**7. Revisão editorial em blocos.** Revise cada bloco (apresentação e Q&A) seguindo [docs/instrucoes_revisor.md](docs/instrucoes_revisor.md) e [docs/guia_estilo.md](docs/guia_estilo.md). Cada bloco tem um `X_entrada.txt` (transcrição crua) e um `X_saida.txt` (texto revisado no formato abaixo).

**8. Conferências automáticas**

```bash
venv/Scripts/python scripts/qa_cobertura.py blocos/P1_entrada.txt blocos/P1_saida.txt   # nada da fala ficou de fora
venv/Scripts/python scripts/verifica_ajustes.py blocos                                   # números não falados, traços, parágrafos no Q&A
```

**9. Montar e gerar o Word no modelo do trimestre**

```bash
py scripts/monta_final.py saidas/final.txt blocos/P1_saida.txt blocos/P2_saida.txt blocos/Q1_saida.txt blocos/Q2_saida.txt
py scripts/build_docx.py <modelo_do_trimestre.docx> saidas/final.txt saidas/transcricao.docx "Transcrição da Videoconferência" "Resultados do 3T26" "23 de outubro de 2026" pt
powershell -File scripts/docx2pdf.ps1 <caminho completo do .docx> <caminho completo do .pdf>
```

## Formato do texto marcado

Cada linha é um parágrafo:

| Linha | Vira no Word |
|---|---|
| `@Marcelo Noronha \| texto` | fala: nome em negrito, " – " e o texto |
| `@Daniel Vaz (Safra) \| texto` | fala de analista, com a instituição entre parênteses |
| `## Slide 2 – Destaques` | título de slide, em negrito |
| `### frase-título` | subtítulo do slide, em negrito |
| `#! Sessão de perguntas e respostas` | título do Q&A, em vermelho |
| texto sem marcador | parágrafo que continua a fala anterior (só na apresentação) |
| linha vazia | espaço entre blocos |

Dentro do texto, `*termo*` sai em itálico e `==trecho==` sai realçado em amarelo, para conferência.

## Regras de estilo principais

- **Apresentação:** a abertura do CEO fica num bloco. Depois vem um título "Slide N – Título" por slide, com o texto dividido em parágrafos.
- **Q&A:** cada fala é um único parágrafo, por maior que seja.
- **Números:** só o que foi falado, sem números tirados do deck. Os números ficam como foram ditos, e as divergências em relação ao deck vão realçadas.
- **Traços:** nenhum traço como pontuação no meio das falas. Use vírgula, parênteses, ponto e vírgula ou dois-pontos.
- **Itálico:** só para termos em inglês no meio de frases em português.
- **Realce amarelo:** nomes, falas atribuídas por dedução e trechos duvidosos, para conferência do RI.

Os detalhes estão em [docs/guia_estilo.md](docs/guia_estilo.md).

## Outros scripts

- `compare.py`: compara uma transcrição automática com a versão publicada, medindo cobertura de conteúdo e números.
- `diarize_fast.py` e `recluster.py`: separação de falantes mais rápida, por agrupamento de embeddings de voz.
- `dump_docx.py`: lista os parágrafos e a formatação de um `document.xml`, útil para estudar o modelo.

## O que não está neste repositório

Ficam de fora os modelos `.docx` do banco (classificados como internos), os áudios, as transcrições, as apresentações e os e-mails internos. O `.gitignore` bloqueia esses formatos.
