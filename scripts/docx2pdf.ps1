# Converte um .docx em PDF usando o Word instalado (somente leitura, sem alterar o original).
# Uso: powershell -File docx2pdf.ps1 <entrada.docx> <saida.pdf>
param([string]$Src, [string]$Dst)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($Src, $false, $true)
    $doc.ExportAsFixedFormat($Dst, 17)
    $doc.Close($false)
    Write-Output "ok: $Dst"
} finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
