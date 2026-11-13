# Собирает иконку приложения из логотипа: персонаж без надписи «VPN» (в 16–32 px
# она не читается) на белой скруглённой плитке. Результат:
#   YgolekVpn\Assets\app.ico  — иконка exe, окна и панели задач (16…256 px)
#   YgolekVpn\Assets\mark.png — тот же знак для шапки окна
# Запускать после замены Assets\logo.jpg.
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$assets = Join-Path $PSScriptRoot "..\YgolekVpn\Assets"
$logo = [System.Drawing.Image]::FromFile((Join-Path $assets "logo.jpg"))

# Квадрат вокруг персонажа на логотипе 640×640
$crop = New-Object System.Drawing.Rectangle 132, 96, 370, 370

function New-Tile([int]$size) {
    $bmp = New-Object System.Drawing.Bitmap $size, $size, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.Clear([System.Drawing.Color]::Transparent)

    # белая плитка со скруглением ~22% (на 16 px — почти квадрат, иначе съедаются углы)
    $r = [Math]::Max(2, [int]($size * 0.22))
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = 2 * $r
    $path.AddArc(0, 0, $d, $d, 180, 90)
    $path.AddArc($size - $d - 1, 0, $d, $d, 270, 90)
    $path.AddArc($size - $d - 1, $size - $d - 1, $d, $d, 0, 90)
    $path.AddArc(0, $size - $d - 1, $d, $d, 90, 90)
    $path.CloseFigure()
    $g.FillPath([System.Drawing.Brushes]::White, $path)

    # персонаж с небольшим отступом; на маленьких размерах — крупнее
    $pad = if ($size -le 24) { [int]($size * 0.06) } else { [int]($size * 0.12) }
    $dest = New-Object System.Drawing.Rectangle $pad, $pad, ($size - 2 * $pad), ($size - 2 * $pad)
    $g.SetClip($path)
    $g.DrawImage($logo, $dest, $crop, [System.Drawing.GraphicsUnit]::Pixel)
    $g.Dispose()
    return $bmp
}

function Get-PngBytes($bmp) {
    $ms = New-Object System.IO.MemoryStream
    $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
    return , $ms.ToArray()
}

# Классический 32-битный BMP-кадр: заголовок BITMAPINFOHEADER (высота ×2),
# пиксели BGRA снизу вверх и пустая AND-маска. Старые API Windows (и GDI+)
# не умеют PNG-кадры маленьких размеров — показывают мусор.
function Get-DibBytes($bmp) {
    $s = $bmp.Width
    $ms = New-Object System.IO.MemoryStream
    $w = New-Object System.IO.BinaryWriter $ms
    $maskRow = [int]([Math]::Ceiling($s / 32.0) * 4)
    $w.Write([uint32]40); $w.Write([int32]$s); $w.Write([int32]($s * 2))
    $w.Write([uint16]1); $w.Write([uint16]32); $w.Write([uint32]0)
    $w.Write([uint32]($s * $s * 4 + $maskRow * $s))
    $w.Write([int32]0); $w.Write([int32]0); $w.Write([uint32]0); $w.Write([uint32]0)
    for ($y = $s - 1; $y -ge 0; $y--) {
        for ($x = 0; $x -lt $s; $x++) {
            $c = $bmp.GetPixel($x, $y)
            $w.Write([byte]$c.B); $w.Write([byte]$c.G); $w.Write([byte]$c.R); $w.Write([byte]$c.A)
        }
    }
    $w.Write((New-Object byte[] ($maskRow * $s)))
    $w.Flush()
    return , $ms.ToArray()
}

# 256 px — PNG (так принято и так меньше файл), остальные — BMP
$sizes = 16, 20, 24, 32, 40, 48, 64, 96, 128, 256
$frames = foreach ($s in $sizes) {
    $tile = New-Tile $s
    if ($s -ge 256) { , (Get-PngBytes $tile) } else { , (Get-DibBytes $tile) }
}

$out = New-Object System.IO.MemoryStream
$w = New-Object System.IO.BinaryWriter $out
$w.Write([uint16]0); $w.Write([uint16]1); $w.Write([uint16]$sizes.Count)
$offset = 6 + 16 * $sizes.Count
for ($i = 0; $i -lt $sizes.Count; $i++) {
    $s = $sizes[$i]
    $dim = if ($s -ge 256) { 0 } else { $s }
    $w.Write([byte]$dim); $w.Write([byte]$dim); $w.Write([byte]0); $w.Write([byte]0)
    $w.Write([uint16]1); $w.Write([uint16]32)
    $w.Write([uint32]$frames[$i].Length); $w.Write([uint32]$offset)
    $offset += $frames[$i].Length
}
foreach ($f in $frames) { $w.Write($f) }
$w.Flush()
[System.IO.File]::WriteAllBytes((Join-Path $assets "app.ico"), $out.ToArray())

$mark = New-Tile 256
$mark.Save((Join-Path $assets "mark.png"), [System.Drawing.Imaging.ImageFormat]::Png)
$logo.Dispose()
Write-Host "app.ico ($($sizes -join ', ') px) и mark.png -> $assets"
