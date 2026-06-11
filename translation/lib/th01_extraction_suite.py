"""
Conversor de formatos gráficos do TH01 ↔ BMP indexado
==============================================================================

Formatos suportados:
  .PTN  — Sprites planares 4bpp 32×32, 16 cores + transparência derivada (cor #15)
  .BOS  — Sprites planares 4bpp de tamanho arbitrário com plano alpha explícito
  .GRC  — Sprites monochrome 1bpp de tamanho arbitrário
  .GRZ  — Container de imagens .GRX com compressão RLE, 640×400

Formato de saída (BMP):
  Todos os formatos são exportados como BMP 4bpp com paleta indexada de 16 cores PC-98.
  Isso garante editabilidade estável: o índice de cor armazenado no BMP corresponde
  diretamente ao índice de cor PC-98, sem nenhuma quantização ou conversão.
  A paleta é incorporada no BMP para visualização correta em qualquer editor de imagens.
  Cor índice 15 = transparente em PTN, BOS e GRZ.
  GRC usa índice 0 = fundo (não desenhado), qualquer outra cor = pixel ativo.

Estruturas dos formatos (detalhadas nas constantes abaixo):
  ─ Palette4: 16 cores × 3 bytes (R, G, B em escala 0–15). 48 bytes total.
  ─ Bitplanes: B (bit0), R (bit1), G (bit2), E (bit3).
    Índice de cor = E«3 | G«2 | R«1 | B (4 bits por pixel, MSB=pixel mais à esquerda).
"""

import struct
import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# ─────────────────────────────────────────────────────────────────────────────
# Paleta canônica PC-98 (16 cores)
# Valores RGB em escala 0–255 (cada componente PC-98 0–15 × 17).
# Esta é a paleta padrão; arquivos podem conter paletas próprias.
# ─────────────────────────────────────────────────────────────────────────────
PC98_DEFAULT_PALETTE_RGB: List[Tuple[int, int, int]] = [
    (  0,   0,   0),  #  0 Preto
    (  0,   0, 170),  #  1 Azul
    (  0, 170,   0),  #  2 Verde
    (  0, 170, 170),  #  3 Ciano
    (170,   0,   0),  #  4 Vermelho
    (170,   0, 170),  #  5 Magenta
    (170,  85,   0),  #  6 Marrom
    (170, 170, 170),  #  7 Cinza claro
    ( 85,  85,  85),  #  8 Cinza escuro
    ( 85,  85, 255),  #  9 Azul claro
    ( 85, 255,  85),  # 10 Verde claro
    ( 85, 255, 255),  # 11 Ciano claro
    (255,  85,  85),  # 12 Vermelho claro
    (255,  85, 255),  # 13 Magenta claro
    (255, 255,  85),  # 14 Amarelo
    (255, 255, 255),  # 15 Branco / TRANSPARENTE em PTN, BOS, GRZ
]

TRANSPARENT_INDEX = 15  # cor #15 = transparente em PTN, BOS, GRZ

# ─────────────────────────────────────────────────────────────────────────────
# Constantes dos formatos
# ─────────────────────────────────────────────────────────────────────────────

# --- Compartilhados ---
PALETTE4_BYTES = 48           # 16 cores × 3 bytes (R,G,B em 0–15)

# --- PTN ---
PTN_MAGIC      = b'HPTN'
PTN_W          = 32
PTN_H          = 32
PTN_PLANE_BYTES = PTN_H * (PTN_W // 8)   # 128 bytes por plano (4 bytes/linha × 32 linhas)
# Header (6 bytes): magic[4] + unused_one(1) + image_count(1)
# Depois: Palette4 (48 bytes)
# Por imagem: unused_zero(1) + B_plane(128) + R_plane(128) + G_plane(128) + E_plane(128) = 513 bytes
PTN_HEADER_SIZE = 6
PTN_IMG_BYTES  = 1 + PTN_PLANE_BYTES * 4  # 513

# --- BOS ---
BOS_MAGIC = b'BOSS'
# Header (16 bytes): magic[4] + vram_w(1) + zero(1) + h(1) + unknown(1)
#                   + spriteformat_header_inner_t: image_count(1) + unknown[7] = 8 bytes
# Depois: Palette4 (48 bytes, skipada no load)
# Por imagem: alpha[plane_size] + B[plane_size] + R[plane_size] + G[plane_size] + E[plane_size]
# plane_size = vram_w * h  (vram_w em bytes, não pixels)
BOS_HEADER_SIZE = 16   # 4+1+1+1+1+8
BOS_INNER_OFFSET = 8   # offset de image_count dentro do header = 4+1+1+1+1

# --- GRC ---
GRC_MAGIC = b'GRCG'
# Header (16 bytes): magic[4] + vram_w(int16) + h(int16) + inner(8)
# Depois: Palette4 (48 bytes, skipada)
# Por imagem: dots[vram_w * h] (monochrome: 1 byte = 8 pixels)
GRC_HEADER_SIZE = 16  # 4+2+2+8
GRC_INNER_OFFSET = 8  # offset de image_count

# --- GRZ / GRX ---
HGRZ_MAGIC       = b'HGRZ'
HGRX_MAGIC       = b'HGRX'
GRZ_IMAGE_MAX    = 16
GRZ_HEADER_SIZE  = 96   # 4+1+3+64+4+20
GRX_HEADER_SIZE  = 64   # 4+1+3+2+2+4+48
GRX_W            = 640
GRX_H            = 400
GRX_PLANE_SIZE   = GRX_W * GRX_H // 8   # 32000 bytes por plano
GC_PUT           = 0x00   # "Copiar próximo(s) byte(s) do stream planar"
GC_RUN           = 0x01   # "Iniciar run: [runs uint8] [cmd uint8]"
GC_SKIP          = 0xFF   # Qualquer byte != GC_PUT e != GC_RUN = skip

# ─────────────────────────────────────────────────────────────────────────────
# Utilitários de paleta PC-98
# ─────────────────────────────────────────────────────────────────────────────

def palette4_read(data: bytes, offset: int) -> List[Tuple[int, int, int]]:
    """
    Lê uma Palette4 PC-98 a partir de `data[offset]`.
    Cada componente está em 0–15; converte para 0–255 multiplicando por 17.
    """
    pal = []
    for i in range(16):
        r = data[offset + i*3 + 0] * 17
        g = data[offset + i*3 + 1] * 17
        b = data[offset + i*3 + 2] * 17
        pal.append((r, g, b))
    return pal


def palette4_write(palette: List[Tuple[int, int, int]]) -> bytes:
    """Serializa 16 cores RGB (0–255) como Palette4 PC-98 (componentes 0–15)."""
    out = bytearray()
    for r, g, b in palette[:16]:
        out.append(max(0, min(15, round(r / 17))))
        out.append(max(0, min(15, round(g / 17))))
        out.append(max(0, min(15, round(b / 17))))
    return bytes(out)


# ─────────────────────────────────────────────────────────────────────────────
# Conversão bitplane ↔ índices de cor
# ─────────────────────────────────────────────────────────────────────────────

def planes_to_indices(B: bytes, R: bytes, G: bytes, E: bytes,
                      w_bytes: int, h: int) -> List[List[int]]:
    """
    Converte 4 planos (B, R, G, E) num grid de índices de cor 4bpp.
    Cada plano tem w_bytes × h bytes. Retorna grid[y][x] = índice 0–15.
    MSB de cada byte = pixel mais à esquerda.
    Índice = (E«3)|(G«2)|(R«1)|B
    """
    grid: List[List[int]] = []
    for y in range(h):
        row: List[int] = []
        for bx in range(w_bytes):
            byte_idx = y * w_bytes + bx
            b_byte = B[byte_idx]
            r_byte = R[byte_idx]
            g_byte = G[byte_idx]
            e_byte = E[byte_idx]
            for bit in range(7, -1, -1):
                b = (b_byte >> bit) & 1
                r = (r_byte >> bit) & 1
                g = (g_byte >> bit) & 1
                e = (e_byte >> bit) & 1
                row.append((e << 3) | (g << 2) | (r << 1) | b)
        grid.append(row)
    return grid


def indices_to_planes(grid: List[List[int]], w_bytes: int, h: int
                      ) -> Tuple[bytearray, bytearray, bytearray, bytearray]:
    """
    Converte um grid de índices 4bpp de volta para 4 planos (B, R, G, E).
    Cada plano tem w_bytes × h bytes.
    """
    B = bytearray(w_bytes * h)
    R = bytearray(w_bytes * h)
    G = bytearray(w_bytes * h)
    E = bytearray(w_bytes * h)
    for y in range(h):
        for bx in range(w_bytes):
            b_byte = r_byte = g_byte = e_byte = 0
            for bit in range(7, -1, -1):
                x = bx * 8 + (7 - bit)
                idx = grid[y][x] if x < len(grid[y]) else 0
                b_byte |= ((idx >> 0) & 1) << bit
                r_byte |= ((idx >> 1) & 1) << bit
                g_byte |= ((idx >> 2) & 1) << bit
                e_byte |= ((idx >> 3) & 1) << bit
            byte_idx = y * w_bytes + bx
            B[byte_idx] = b_byte
            R[byte_idx] = r_byte
            G[byte_idx] = g_byte
            E[byte_idx] = e_byte
    return B, R, G, E


def alpha_from_planes(B: bytes, R: bytes, G: bytes, E: bytes) -> bytes:
    """
    Calcula o plano alpha como ~(B & R & G & E), byte a byte.
    Bit=1 → pixel opaco; bit=0 → pixel transparente (cor #15).
    Implementa ptn_alpha_from() do TH01.
    """
    return bytes(~(b & r & g & e) & 0xFF
                 for b, r, g, e in zip(B, R, G, E))


def dots_to_indices_mono(dots: bytes, w_bytes: int, h: int) -> List[List[int]]:
    """
    Converte o plano monochrome do GRC em grid de índices.
    Bit=1 → índice 15 (cor ativa), bit=0 → índice 0 (fundo).
    """
    grid: List[List[int]] = []
    for y in range(h):
        row: List[int] = []
        for bx in range(w_bytes):
            byte_val = dots[y * w_bytes + bx]
            for bit in range(7, -1, -1):
                row.append(TRANSPARENT_INDEX if (byte_val >> bit) & 1 else 0)
        grid.append(row)
    return grid


def indices_to_dots_mono(grid: List[List[int]], w_bytes: int, h: int) -> bytearray:
    """
    Converte grid de índices de volta para plano monochrome do GRC.
    Índice != 0 → bit=1; índice == 0 → bit=0.
    """
    dots = bytearray(w_bytes * h)
    for y in range(h):
        for bx in range(w_bytes):
            byte_val = 0
            for bit in range(7, -1, -1):
                x = bx * 8 + (7 - bit)
                idx = grid[y][x] if x < len(grid[y]) else 0
                if idx != 0:
                    byte_val |= (1 << bit)
            dots[y * w_bytes + bx] = byte_val
    return dots


# ─────────────────────────────────────────────────────────────────────────────
# BMP 4bpp indexado — leitura e escrita
#
# Formato BMP 4bpp:
#   BITMAPFILEHEADER (14 bytes): signature, filesize, reserved×2, pixel_offset
#   BITMAPINFOHEADER (40 bytes): header_size, width, height, planes, bpp,
#                                compression, image_size, xppm, yppm, clr_used, clr_important
#   Color table: 16 × RGBQUAD (4 bytes cada) = 64 bytes
#   Pixel data: linha a linha de baixo para cima (bottom-up) ou cima para baixo (top-down)
#     Cada byte = 2 pixels (nibble alto = pixel esquerdo, nibble baixo = pixel direito)
#     Cada linha alinhada a múltiplos de 4 bytes
# ─────────────────────────────────────────────────────────────────────────────

BMP4_FILE_HEADER_SIZE  = 14
BMP4_INFO_HEADER_SIZE  = 40
BMP4_COLOR_TABLE_SIZE  = 16 * 4   # 64 bytes
BMP4_HEADER_TOTAL      = BMP4_FILE_HEADER_SIZE + BMP4_INFO_HEADER_SIZE + BMP4_COLOR_TABLE_SIZE  # 118 bytes


def bmp4_row_stride(w_pixels: int) -> int:
    """Calcula o stride de linha do BMP 4bpp (alinhado a 4 bytes)."""
    return ((w_pixels + 7) // 8 * 4 + 3) // 4 * 4
    # Simplificado: ceil(w_pixels/2) arredondado para múltiplo de 4
    # = ((w_pixels + 1) // 2 + 3) // 4 * 4


def bmp4_write(path: str, grid: List[List[int]],
               palette: List[Tuple[int, int, int]]):
    """
    Salva um grid de índices 4bpp como BMP 4bpp com tabela de cores.
    grid[y][x] = índice 0–15.
    palette: lista de 16 tuplas (R, G, B) em 0–255.
    O BMP é gerado bottom-up (convenção padrão BMP).
    """
    h = len(grid)
    w = len(grid[0]) if h else 0

    stride = ((w + 1) // 2 + 3) // 4 * 4
    pixel_data_size = stride * h
    file_size = BMP4_HEADER_TOTAL + pixel_data_size

    with open(path, 'wb') as f:
        # BITMAPFILEHEADER
        f.write(b'BM')
        f.write(struct.pack('<I', file_size))
        f.write(struct.pack('<HH', 0, 0))
        f.write(struct.pack('<I', BMP4_HEADER_TOTAL))

        # BITMAPINFOHEADER
        f.write(struct.pack('<I', BMP4_INFO_HEADER_SIZE))  # biSize
        f.write(struct.pack('<i', w))                       # biWidth
        f.write(struct.pack('<i', h))                       # biHeight (positivo = bottom-up)
        f.write(struct.pack('<H', 1))                       # biPlanes
        f.write(struct.pack('<H', 4))                       # biBitCount = 4
        f.write(struct.pack('<I', 0))                       # biCompression = BI_RGB
        f.write(struct.pack('<I', pixel_data_size))         # biSizeImage
        f.write(struct.pack('<i', 2835))                    # biXPelsPerMeter
        f.write(struct.pack('<i', 2835))                    # biYPelsPerMeter
        f.write(struct.pack('<I', 16))                      # biClrUsed
        f.write(struct.pack('<I', 0))                       # biClrImportant

        # Tabela de cores (RGBQUAD: B, G, R, reserved)
        for i in range(16):
            if i < len(palette):
                r, g, b = palette[i]
            else:
                r, g, b = 0, 0, 0
            f.write(bytes([b, g, r, 0]))

        # Pixel data (bottom-up)
        for y in range(h - 1, -1, -1):
            row_bytes = bytearray(stride)
            row = grid[y]
            for x in range(w):
                idx = row[x] & 0xF
                byte_pos = x // 2
                if x % 2 == 0:
                    row_bytes[byte_pos] = idx << 4
                else:
                    row_bytes[byte_pos] |= idx
            f.write(bytes(row_bytes))


def bmp4_read(path: str) -> Tuple[List[List[int]], List[Tuple[int, int, int]]]:
    """
    Lê um BMP 4bpp indexado.
    Retorna (grid[y][x] = índice 0–15, paleta de 16 cores RGB 0–255).
    Exige BMP de 4 bits por pixel sem compressão (BI_RGB).
    """
    with open(path, 'rb') as f:
        data = f.read()

    if data[:2] != b'BM':
        raise ValueError(f"Não é um BMP válido: {path}")

    pixel_offset = struct.unpack_from('<I', data, 10)[0]
    info_size    = struct.unpack_from('<I', data, 14)[0]
    w            = struct.unpack_from('<i', data, 18)[0]
    h_raw        = struct.unpack_from('<i', data, 22)[0]
    bpp          = struct.unpack_from('<H', data, 28)[0]
    compression  = struct.unpack_from('<I', data, 30)[0]

    if bpp != 4:
        raise ValueError(
            f"{path}: BMP deve ser 4bpp (indexado de 16 cores). "
            f"Este arquivo é {bpp}bpp.\n"
            f"  → Exporte como 'BMP 16 cores' no seu editor de imagens."
        )
    if compression != 0:
        raise ValueError(
            f"{path}: BMP 4bpp comprimido (RLE4) não suportado. "
            f"Use BMP 4bpp sem compressão."
        )

    h = abs(h_raw)
    top_down = (h_raw < 0)

    # Lê tabela de cores (RGBQUAD: B, G, R, _)
    color_table_offset = 14 + info_size
    palette: List[Tuple[int, int, int]] = []
    for i in range(16):
        off = color_table_offset + i * 4
        b, g, r, _ = data[off], data[off+1], data[off+2], data[off+3]
        palette.append((r, g, b))

    # Lê pixels
    stride = ((w + 1) // 2 + 3) // 4 * 4
    rows: List[List[int]] = []
    for yi in range(h):
        row_start = pixel_offset + yi * stride
        row: List[int] = []
        for xi in range(w):
            byte_pos = xi // 2
            byte_val = data[row_start + byte_pos]
            if xi % 2 == 0:
                row.append((byte_val >> 4) & 0xF)
            else:
                row.append(byte_val & 0xF)
        rows.append(row)

    if not top_down:
        rows.reverse()  # bottom-up → top-down

    return rows, palette


# ─────────────────────────────────────────────────────────────────────────────
# Formato .PTN
# ─────────────────────────────────────────────────────────────────────────────

def ptn_load(path: str) -> Tuple[List[List[List[int]]], List[Tuple[int, int, int]]]:
    """
    Carrega um arquivo .PTN.
    Retorna (lista_de_grids, paleta).
    Cada grid[y][x] = índice 0–15 (índice 15 = transparente).
    """
    with open(path, 'rb') as f:
        data = f.read()

    if len(data) < PTN_HEADER_SIZE:
        raise ValueError(f"PTN muito pequeno: {path}")
    if data[:4] != PTN_MAGIC:
        raise ValueError(f"Magic PTN inválido em {path}: {data[:4]!r}")

    image_count = data[5]
    if image_count == 0:
        raise ValueError(f"PTN sem imagens: {path}")

    pos = PTN_HEADER_SIZE

    # Paleta
    if pos + PALETTE4_BYTES <= len(data):
        palette = palette4_read(data, pos)
    else:
        palette = list(PC98_DEFAULT_PALETTE_RGB)
        print(f"  [!] Paleta ausente em {path}, usando padrão.")
    pos += PALETTE4_BYTES

    grids: List[List[List[int]]] = []
    for i in range(image_count):
        if pos + PTN_IMG_BYTES > len(data):
            print(f"  [!] Dados insuficientes para imagem #{i} em {path}.")
            break

        pos += 1  # unused_zero

        B = data[pos : pos + PTN_PLANE_BYTES]; pos += PTN_PLANE_BYTES
        R = data[pos : pos + PTN_PLANE_BYTES]; pos += PTN_PLANE_BYTES
        G = data[pos : pos + PTN_PLANE_BYTES]; pos += PTN_PLANE_BYTES
        E = data[pos : pos + PTN_PLANE_BYTES]; pos += PTN_PLANE_BYTES

        grid = planes_to_indices(B, R, G, E, PTN_W // 8, PTN_H)
        grids.append(grid)

    return grids, palette


def ptn_save(path: str, grids: List[List[List[int]]],
             palette: List[Tuple[int, int, int]]):
    """
    Salva uma lista de grids como arquivo .PTN.
    Cada grid deve ser PTN_H × PTN_W (32×32) com índices 0–15.
    """
    if not grids:
        raise ValueError("PTN: nenhuma imagem para salvar.")
    if len(grids) > 127:
        raise ValueError(f"PTN: máximo 127 imagens (recebido {len(grids)}).")

    for i, grid in enumerate(grids):
        if len(grid) != PTN_H or any(len(r) != PTN_W for r in grid):
            raise ValueError(
                f"PTN: imagem #{i} deve ser {PTN_W}×{PTN_H}. "
                f"Encontrado {len(grid[0]) if grid else 0}×{len(grid)}."
            )

    out = bytearray()
    out += PTN_MAGIC
    out += bytes([1, len(grids)])     # unused_one=1, image_count
    out += palette4_write(palette)

    for grid in grids:
        B, R, G, E = indices_to_planes(grid, PTN_W // 8, PTN_H)
        out += bytes([0])   # unused_zero
        out += bytes(B)
        out += bytes(R)
        out += bytes(G)
        out += bytes(E)

    with open(path, 'wb') as f:
        f.write(out)


# ─────────────────────────────────────────────────────────────────────────────
# Formato .BOS
# ─────────────────────────────────────────────────────────────────────────────

def bos_load(path: str) -> Tuple[
    int, int, List[List[List[int]]], List[Tuple[int, int, int]]
]:
    """
    Carrega um arquivo .BOS.
    Retorna (vram_w_bytes, h, lista_de_grids, paleta).
    vram_w_bytes: largura em bytes (pixels = vram_w_bytes × 8).
    O plano alpha original é descartado; pixels transparentes são reconstruídos
    como índice 15 via ptn_alpha_from para round-trip correto.
    """
    with open(path, 'rb') as f:
        data = f.read()

    if len(data) < BOS_HEADER_SIZE:
        raise ValueError(f"BOS muito pequeno: {path}")
    if data[:4] != BOS_MAGIC:
        raise ValueError(f"Magic BOS inválido em {path}: {data[:4]!r}")

    vram_w = data[4]   # uint8_t vram_w (em bytes)
    h      = data[6]   # uint8_t h (em linhas)
    image_count = data[BOS_INNER_OFFSET]  # spriteformat_header_inner_t.image_count

    plane_size = vram_w * h
    pos = BOS_HEADER_SIZE + PALETTE4_BYTES  # skip header + palette

    # Lê paleta (logo após o header)
    if BOS_HEADER_SIZE + PALETTE4_BYTES <= len(data):
        palette = palette4_read(data, BOS_HEADER_SIZE)
    else:
        palette = list(PC98_DEFAULT_PALETTE_RGB)

    grids: List[List[List[int]]] = []
    for i in range(image_count):
        if pos + plane_size * 5 > len(data):
            print(f"  [!] BOS {path}: dados insuficientes para imagem #{i}.")
            break

        alpha = data[pos : pos + plane_size]; pos += plane_size
        B     = data[pos : pos + plane_size]; pos += plane_size
        R     = data[pos : pos + plane_size]; pos += plane_size
        G     = data[pos : pos + plane_size]; pos += plane_size
        E     = data[pos : pos + plane_size]; pos += plane_size

        grid = planes_to_indices(B, R, G, E, vram_w, h)

        # Aplica o alpha original: onde alpha byte tem bit=0, pixel é transparente
        # O plano alpha tem 1 bit por pixel, MSB = pixel mais à esquerda
        for y in range(h):
            for bx in range(vram_w):
                alpha_byte = alpha[y * vram_w + bx]
                for bit in range(7, -1, -1):
                    x = bx * 8 + (7 - bit)
                    if x < len(grid[y]):
                        if not ((alpha_byte >> bit) & 1):
                            grid[y][x] = TRANSPARENT_INDEX

        grids.append(grid)

    return vram_w, h, grids, palette


def bos_save(path: str, vram_w: int, h: int,
             grids: List[List[List[int]]],
             palette: List[Tuple[int, int, int]]):
    """
    Salva grids como arquivo .BOS.
    O plano alpha é recalculado via ptn_alpha_from (índice 15 = transparente).
    """
    if not grids:
        raise ValueError("BOS: nenhuma imagem para salvar.")
    if len(grids) > 255:
        raise ValueError(f"BOS: máximo 255 imagens.")

    w_pixels = vram_w * 8

    for i, grid in enumerate(grids):
        if len(grid) != h or any(len(r) != w_pixels for r in grid):
            raise ValueError(
                f"BOS: imagem #{i} deve ser {w_pixels}×{h}. "
                f"Encontrado {len(grid[0]) if grid else 0}×{len(grid)}."
            )

    # Header BOS (16 bytes)
    out = bytearray()
    out += BOS_MAGIC
    out.append(vram_w)        # vram_w (uint8)
    out.append(0)             # zero
    out.append(h)             # h (uint8)
    out.append(0)             # unknown
    # spriteformat_header_inner_t: image_count(1) + unknown[7]
    out.append(len(grids))    # image_count
    out += bytes(7)           # unknown[7]

    out += palette4_write(palette)

    for grid in grids:
        B, R, G, E = indices_to_planes(grid, vram_w, h)
        alpha = alpha_from_planes(bytes(B), bytes(R), bytes(G), bytes(E))
        out += bytes(alpha)
        out += bytes(B)
        out += bytes(R)
        out += bytes(G)
        out += bytes(E)

    with open(path, 'wb') as f:
        f.write(out)


# ─────────────────────────────────────────────────────────────────────────────
# Formato .GRC
# ─────────────────────────────────────────────────────────────────────────────

def grc_load(path: str) -> Tuple[
    int, int, List[List[List[int]]], List[Tuple[int, int, int]]
]:
    """
    Carrega um arquivo .GRC.
    Retorna (vram_w_bytes, h, lista_de_grids, paleta).
    grid[y][x] = 0 (fundo) ou 15 (pixel ativo).
    """
    with open(path, 'rb') as f:
        data = f.read()

    if len(data) < GRC_HEADER_SIZE:
        raise ValueError(f"GRC muito pequeno: {path}")
    if data[:4] != GRC_MAGIC:
        raise ValueError(f"Magic GRC inválido em {path}: {data[:4]!r}")

    # vram_w: int16_t @ offset 4, h: int16_t @ offset 6
    vram_w = struct.unpack_from('<h', data, 4)[0]
    h      = struct.unpack_from('<h', data, 6)[0]
    image_count = data[GRC_INNER_OFFSET]  # spriteformat_header_inner_t.image_count

    image_size = vram_w * h
    pos = GRC_HEADER_SIZE + PALETTE4_BYTES

    if GRC_HEADER_SIZE + PALETTE4_BYTES <= len(data):
        palette = palette4_read(data, GRC_HEADER_SIZE)
    else:
        palette = list(PC98_DEFAULT_PALETTE_RGB)

    grids: List[List[List[int]]] = []
    for i in range(image_count):
        if pos + image_size > len(data):
            print(f"  [!] GRC {path}: dados insuficientes para imagem #{i}.")
            break
        dots = data[pos : pos + image_size]; pos += image_size
        grid = dots_to_indices_mono(dots, vram_w, h)
        grids.append(grid)

    return vram_w, h, grids, palette


def grc_save(path: str, vram_w: int, h: int,
             grids: List[List[List[int]]],
             palette: List[Tuple[int, int, int]]):
    """
    Salva grids monochrome como arquivo .GRC.
    Índice 0 = fundo (bit=0); qualquer outro índice = pixel ativo (bit=1).
    """
    if not grids:
        raise ValueError("GRC: nenhuma imagem para salvar.")

    w_pixels = vram_w * 8
    for i, grid in enumerate(grids):
        if len(grid) != h or any(len(r) != w_pixels for r in grid):
            raise ValueError(
                f"GRC: imagem #{i} deve ser {w_pixels}×{h}. "
                f"Encontrado {len(grid[0]) if grid else 0}×{len(grid)}."
            )

    out = bytearray()
    out += GRC_MAGIC
    out += struct.pack('<h', vram_w)   # int16_t vram_w
    out += struct.pack('<h', h)        # int16_t h
    # spriteformat_header_inner_t
    out.append(len(grids))            # image_count
    out += bytes(7)                   # unknown[7]

    out += palette4_write(palette)

    for grid in grids:
        dots = indices_to_dots_mono(grid, vram_w, h)
        out += bytes(dots)

    with open(path, 'wb') as f:
        f.write(out)


# ─────────────────────────────────────────────────────────────────────────────
# Formato .GRZ / .GRX — RLE
# ─────────────────────────────────────────────────────────────────────────────

def grx_rle_decode(rle: bytes) -> List[bool]:
    """
    Decodifica o stream RLE de um GRX em lista de GRX_PLANE_SIZE booleanos.
    True = PUT (consumir 4 bytes do stream planar), False = SKIP.

    Implementação fiel do algoritmo de grx_put() do TH01:

        for(vram_offset = 0; vram_offset < PLANE_SIZE; vram_offset++) {
            command = *(rle++);
            if(command == GC_RUN) {
                runs = *(rle++);
                if(runs) {
                    command = *(rle++);
                    while(runs--) {
                        if(command == GC_PUT) {
                            put(vram_offset, vram_offset++, planar);
                        } else {
                            vram_offset++;
                        }
                    }
                }
            }
            if(command == GC_PUT) { put(vram_offset, vram_offset, planar); }
        }

    Cada iteração do for cobre 1 + runs offsets (quando GC_RUN com runs>0),
    mais o incremento final do for. O comando PUT "extra" após o loop while
    é executado para o offset atual (que já foi avançado pelo while).
    """
    result: List[bool] = []
    pos = 0
    vo = 0  # vram_offset simulado

    while vo < GRX_PLANE_SIZE:
        if pos >= len(rle):
            # Stream acabou antes: preencher com SKIPs
            result.extend([False] * (GRX_PLANE_SIZE - vo))
            break

        command = rle[pos]; pos += 1

        if command == GC_RUN:
            if pos >= len(rle):
                break
            runs = rle[pos]; pos += 1
            if runs:
                if pos >= len(rle):
                    break
                command = rle[pos]; pos += 1
                for _ in range(runs):
                    if vo >= GRX_PLANE_SIZE:
                        break
                    result.append(command == GC_PUT)
                    vo += 1

        # PUT extra (ou operação direta se não foi GC_RUN)
        if vo < GRX_PLANE_SIZE:
            result.append(command == GC_PUT)
            vo += 1

    return result


def grx_rle_encode(commands: List[bool]) -> bytes:
    """
    Codifica uma lista de booleanos PUT/SKIP como stream RLE GRX.

    Regras do encoder (derivadas da análise do decoder):
      Para um bloco de K operações consecutivas iguais:
        K=1:         emitir [cmd]           (GC_PUT=0x00 ou GC_SKIP=0xFF)
        2≤K≤256:     emitir [0x01, K-1, cmd] (GC_RUN, runs=K-1)
        K>256:       dividir em múltiplos blocos de ≤256

    O decoder processa: runs=N → N operações no while + 1 extra = N+1 total,
    mais o for++. Para cobrir K offsets começando no offset atual:
      GC_RUN + (K-1) + cmd → K operações, for++ avança para o próximo bloco.
    """
    out = bytearray()
    i = 0
    n = len(commands)

    while i < n:
        cmd = commands[i]
        cmd_byte = GC_PUT if cmd else GC_SKIP

        # Conta a duração do bloco atual
        j = i + 1
        while j < n and commands[j] == cmd:
            j += 1
        run_len = j - i   # número de operações iguais

        while run_len > 0:
            chunk = min(run_len, 256)
            if chunk == 1:
                out.append(cmd_byte)
            else:
                out.append(GC_RUN)
                out.append(chunk - 1)   # runs = chunk - 1
                out.append(cmd_byte)
            run_len -= chunk

        i = j

    return bytes(out)


def grx_decode_image(commands: List[bool], planar_stream: bytes,
                     palette: List[Tuple[int, int, int]]) -> List[List[int]]:
    """
    Aplica os comandos PUT/SKIP ao stream planar intercalado (B,R,G,E)
    e reconstrói o grid de índices 4bpp para a imagem 640×400.
    O stream planar tem 4 bytes por PUT (B, R, G, E consecutivos).
    """
    B = bytearray(GRX_PLANE_SIZE)
    R = bytearray(GRX_PLANE_SIZE)
    G = bytearray(GRX_PLANE_SIZE)
    E = bytearray(GRX_PLANE_SIZE)

    ps_pos = 0
    for offset, do_put in enumerate(commands):
        if offset >= GRX_PLANE_SIZE:
            break
        if do_put:
            if ps_pos + 4 <= len(planar_stream):
                B[offset] = planar_stream[ps_pos]
                R[offset] = planar_stream[ps_pos + 1]
                G[offset] = planar_stream[ps_pos + 2]
                E[offset] = planar_stream[ps_pos + 3]
                ps_pos += 4

    return planes_to_indices(bytes(B), bytes(R), bytes(G), bytes(E),
                             GRX_W // 8, GRX_H)


def grx_encode_image(grid: List[List[int]]) -> Tuple[bytes, bytes, int]:
    """
    Converte um grid 640×400 em (rle_stream, planar_stream, put_count).
    Apenas offsets com dados não-zero (algum plano != 0) recebem PUT.
    Offsets completamente zeros recebem SKIP (economiza espaço e compatibilidade).

    Retorna também put_count para verificar se o stream cabe em uint16.
    O stream planar tem 4 bytes por PUT: B[offset], R[offset], G[offset], E[offset].
    """
    B, R, G, E = indices_to_planes(grid, GRX_W // 8, GRX_H)

    # Decide PUT ou SKIP para cada offset
    commands: List[bool] = []
    planar = bytearray()
    for i in range(GRX_PLANE_SIZE):
        if B[i] | R[i] | G[i] | E[i]:
            commands.append(True)
            planar.append(B[i])
            planar.append(R[i])
            planar.append(G[i])
            planar.append(E[i])
        else:
            commands.append(False)

    rle = grx_rle_encode(commands)
    put_count = sum(commands)

    ps_size = len(planar)
    if ps_size > 65535:
        print(
            f"  [!] AVISO: stream planar tem {ps_size} bytes "
            f"(máximo do formato: 65535). "
            f"A imagem tem muitos pixels não-pretos.\n"
            f"      Use mais fundo preto (índice 0) para reduzir o tamanho."
        )
    if len(rle) > 65535:
        print(f"  [!] AVISO: stream RLE tem {len(rle)} bytes (máximo: 65535).")

    return rle, bytes(planar), put_count


def grz_load(path: str) -> List[Tuple[List[List[int]], List[Tuple[int, int, int]]]]:
    """
    Carrega todas as imagens de um arquivo .GRZ.
    Retorna lista de (grid_640x400, paleta) para cada imagem GRX.
    """
    with open(path, 'rb') as f:
        data = f.read()

    if len(data) < GRZ_HEADER_SIZE:
        raise ValueError(f"GRZ muito pequeno: {path}")
    if data[:4] != HGRZ_MAGIC:
        raise ValueError(f"Magic GRZ inválido em {path}: {data[:4]!r}")

    image_count = data[4]
    # offsets: int32_t[16] @ byte 8
    offsets = [struct.unpack_from('<i', data, 8 + i*4)[0]
               for i in range(GRZ_IMAGE_MAX)]

    results = []
    for n in range(image_count):
        off = offsets[n]
        if off <= 0 or off + GRX_HEADER_SIZE > len(data):
            print(f"  [!] GRZ {path}: GRX #{n} offset inválido ({off:#x}), pulando.")
            continue

        pos = off
        if data[pos:pos+4] != HGRX_MAGIC:
            print(f"  [!] GRZ {path}: GRX #{n} magic inválido em {off:#x}, pulando.")
            continue

        planar_stream_count = data[pos + 4]
        rle_size    = struct.unpack_from('<H', data, pos + 8)[0]
        planar_size = struct.unpack_from('<H', data, pos + 10)[0]
        # Palette4 @ pos+16 (após 4+1+3+2+2+4 = 16 bytes)
        palette = palette4_read(data, pos + 16)

        data_pos = pos + GRX_HEADER_SIZE

        rle_stream = data[data_pos : data_pos + rle_size]
        data_pos += rle_size

        # Lê o primeiro stream planar
        planar_stream = data[data_pos : data_pos + planar_size]

        commands = grx_rle_decode(rle_stream)
        grid = grx_decode_image(commands, planar_stream, palette)
        results.append((grid, palette))

    return results


def grz_save(path: str,
             images: List[Tuple[List[List[int]], List[Tuple[int, int, int]]]]):
    """
    Salva uma lista de (grid_640x400, paleta) como arquivo .GRZ.
    """
    if not images:
        raise ValueError("GRZ: nenhuma imagem para salvar.")
    if len(images) > GRZ_IMAGE_MAX:
        raise ValueError(f"GRZ: máximo {GRZ_IMAGE_MAX} imagens (recebido {len(images)}).")

    for i, (grid, _) in enumerate(images):
        if len(grid) != GRX_H or any(len(r) != GRX_W for r in grid):
            raise ValueError(
                f"GRZ: imagem #{i} deve ser {GRX_W}×{GRX_H}. "
                f"Encontrado {len(grid[0]) if grid else 0}×{len(grid)}."
            )

    # Pré-compila os blocos GRX
    grx_blocks: List[bytes] = []
    for grid, palette in images:
        rle_stream, planar_stream, _ = grx_encode_image(grid)

        rs_size = min(len(rle_stream), 0xFFFF)
        ps_size = min(len(planar_stream), 0xFFFF)

        grx_hdr = bytearray()
        grx_hdr += HGRX_MAGIC
        grx_hdr.append(1)                           # planar_stream_count
        grx_hdr += bytes(3)                         # unused_1
        grx_hdr += struct.pack('<H', rs_size)       # rle_stream_size
        grx_hdr += struct.pack('<H', ps_size)       # planar_stream_size
        grx_hdr += bytes(4)                         # unused_2
        grx_hdr += palette4_write(palette)          # Palette4 (48 bytes)
        assert len(grx_hdr) == GRX_HEADER_SIZE

        grx_blocks.append(bytes(grx_hdr) + rle_stream[:rs_size] + planar_stream[:ps_size])

    # Monta o GRZ header
    offsets = [0] * GRZ_IMAGE_MAX
    cur = GRZ_HEADER_SIZE
    for i, blk in enumerate(grx_blocks):
        offsets[i] = cur
        cur += len(blk)
    total_size = cur

    out = bytearray()
    out += HGRZ_MAGIC
    out.append(len(images))          # image_count
    out += bytes(3)                  # padding
    for off in offsets:
        out += struct.pack('<i', off)
    out += struct.pack('<i', total_size)
    out += bytes(20)                 # unknown
    assert len(out) == GRZ_HEADER_SIZE

    for blk in grx_blocks:
        out += blk

    with open(path, 'wb') as f:
        f.write(out)


# ─────────────────────────────────────────────────────────────────────────────
# Exportação e importação de BMP 4bpp
# ─────────────────────────────────────────────────────────────────────────────

def export_as_bmps(base_name: str, out_dir: Path,
                   grids: List[List[List[int]]],
                   palette: List[Tuple[int, int, int]]) -> List[str]:
    """
    Salva cada grid como BMP 4bpp indexado em out_dir.
    Retorna lista dos caminhos gerados.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, grid in enumerate(grids):
        bmp_path = str(out_dir / f"{base_name}_{i:03d}.bmp")
        bmp4_write(bmp_path, grid, palette)
        paths.append(bmp_path)
    return paths


def import_from_bmps(bmp_files: List[str],
                     expected_w: Optional[int] = None,
                     expected_h: Optional[int] = None
                     ) -> Tuple[List[List[List[int]]], List[Tuple[int, int, int]]]:
    """
    Lê uma lista de BMPs 4bpp. Retorna (lista_de_grids, paleta_do_primeiro_bmp).
    Valida as dimensões se expected_w/expected_h forem fornecidos.
    """
    grids = []
    palette: Optional[List[Tuple[int, int, int]]] = None

    for bmp in bmp_files:
        grid, pal = bmp4_read(bmp)
        if palette is None:
            palette = pal

        h = len(grid)
        w = len(grid[0]) if h else 0

        if expected_w is not None and w != expected_w:
            raise ValueError(
                f"{bmp}: largura {w} ≠ esperada {expected_w} pixels."
            )
        if expected_h is not None and h != expected_h:
            raise ValueError(
                f"{bmp}: altura {h} ≠ esperada {expected_h} pixels."
            )
        grids.append(grid)

    if not grids:
        raise ValueError("Nenhum BMP válido encontrado.")

    return grids, palette or list(PC98_DEFAULT_PALETTE_RGB)


# ─────────────────────────────────────────────────────────────────────────────
# Sidecar JSON — preserva metadados necessários para round-trip exato
# ─────────────────────────────────────────────────────────────────────────────

def sidecar_write(path: str, meta: Dict[str, Any]):
    """Salva um arquivo JSON de metadados ao lado dos BMPs exportados."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def sidecar_read(path: str) -> Dict[str, Any]:
    """Lê o arquivo JSON de metadados."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# Comandos CLI
# ─────────────────────────────────────────────────────────────────────────────

def extract(input, output = None):
    src = Path(input)
    ext = src.suffix.lower()
    out_dir = Path(output) if output else src.parent / src.stem
    stem = src.stem

    if ext == '.ptn':
        print(f"[PTN] Carregando: {src}")
        grids, palette = ptn_load(str(src))
        print(f"  {len(grids)} imagem(ns), {PTN_W}×{PTN_H} pixels")
        paths = export_as_bmps(stem, out_dir, grids, palette)
        for p in paths:
            print(f"  → {p}")
        meta = {'format': 'PTN', 'w': PTN_W, 'h': PTN_H,
                'image_count': len(grids), 'source': str(src)}
        sidecar_write(str(out_dir / f"{stem}.json"), meta)

    elif ext == '.bos':
        print(f"[BOS] Carregando: {src}")
        vram_w, h, grids, palette = bos_load(str(src))
        w_pixels = vram_w * 8
        print(f"  {len(grids)} imagem(ns), {w_pixels}×{h} pixels (vram_w={vram_w} bytes)")
        paths = export_as_bmps(stem, out_dir, grids, palette)
        for p in paths:
            print(f"  → {p}")
        meta = {'format': 'BOS', 'vram_w': vram_w, 'h': h,
                'image_count': len(grids), 'source': str(src)}
        sidecar_write(str(out_dir / f"{stem}.json"), meta)

    elif ext == '.grc':
        print(f"[GRC] Carregando: {src}")
        vram_w, h, grids, palette = grc_load(str(src))
        w_pixels = vram_w * 8
        print(f"  {len(grids)} imagem(ns), {w_pixels}×{h} pixels (vram_w={vram_w} bytes)")
        paths = export_as_bmps(stem, out_dir, grids, palette)
        for p in paths:
            print(f"  → {p}")
        meta = {'format': 'GRC', 'vram_w': vram_w, 'h': h,
                'image_count': len(grids), 'source': str(src)}
        sidecar_write(str(out_dir / f"{stem}.json"), meta)

    elif ext == '.grz':
        print(f"[GRZ] Carregando: {src}")
        images = grz_load(str(src))
        print(f"  {len(images)} imagem(ns), {GRX_W}×{GRX_H} pixels")
        for i, (grid, palette) in enumerate(images):
            bmp_path = str(out_dir / f"{stem}_{i:03d}.bmp")
            out_dir.mkdir(parents=True, exist_ok=True)
            bmp4_write(bmp_path, grid, palette)
            print(f"  → {bmp_path}")
        meta = {'format': 'GRZ', 'w': GRX_W, 'h': GRX_H,
                'image_count': len(images), 'source': str(src)}
        sidecar_write(str(out_dir / f"{stem}.json"), meta)

    else:
        print(f"Extensão não suportada: '{ext}'. Use .ptn, .bos, .grc ou .grz")
        sys.exit(1)

    print(f"  Metadados: {out_dir / (stem + '.json')}")
    print("Extração concluída.")


def pack(bmp_files, output, meta = None):
    # bmp_files = bmp_files
    out_path = Path(output)
    ext = out_path.suffix.lower()

    # Tenta carregar sidecar automático
    meta: Dict[str, Any] = {}
    if meta:
        meta = sidecar_read(meta)
        print(f"  Metadados: {meta}")

    if ext == '.ptn':
        grids, palette = import_from_bmps(bmp_files, PTN_W, PTN_H)
        print(f"[PTN] Empacotando {len(grids)} imagem(ns) → {out_path}")
        ptn_save(str(out_path), grids, palette)

    elif ext == '.bos':
        if 'vram_w' not in meta or 'h' not in meta:
            raise ValueError(
                "BOS requer vram_w e h do arquivo de metadados (--meta).\n"
                "Extraia o original primeiro para obter o .json de metadados."
            )
        vram_w = int(meta['vram_w'])
        h      = int(meta['h'])
        grids, palette = import_from_bmps(bmp_files, vram_w * 8, h)
        print(f"[BOS] Empacotando {len(grids)} imagem(ns) → {out_path} "
              f"(vram_w={vram_w}, h={h})")
        bos_save(str(out_path), vram_w, h, grids, palette)

    elif ext == '.grc':
        if 'vram_w' not in meta or 'h' not in meta:
            raise ValueError(
                "GRC requer vram_w e h do arquivo de metadados (--meta)."
            )
        vram_w = int(meta['vram_w'])
        h      = int(meta['h'])
        grids, palette = import_from_bmps(bmp_files, vram_w * 8, h)
        print(f"[GRC] Empacotando {len(grids)} imagem(ns) → {out_path} "
              f"(vram_w={vram_w}, h={h})")
        grc_save(str(out_path), vram_w, h, grids, palette)

    elif ext == '.grz':
        grids_and_pals = []
        for bmp in bmp_files:
            grid, palette = bmp4_read(bmp)
            h = len(grid)
            w = len(grid[0]) if h else 0
            if w != GRX_W or h != GRX_H:
                raise ValueError(
                    f"GRZ: {bmp} deve ser {GRX_W}×{GRX_H}. "
                    f"Encontrado {w}×{h}."
                )
            grids_and_pals.append((grid, palette))
        print(f"[GRZ] Empacotando {len(grids_and_pals)} imagem(ns) → {out_path}")
        grz_save(str(out_path), grids_and_pals)

    else:
        print(f"Extensão não suportada: '{ext}'. Use .ptn, .bos, .grc ou .grz")
        sys.exit(1)

    print(f"  → {out_path} ({out_path.stat().st_size} bytes)")
    print("Empacotamento concluído.")


# ─────────────────────────────────────────────────────────────────────────────
# main()
# ─────────────────────────────────────────────────────────────────────────────

# def main():
#     parser = argparse.ArgumentParser(
#         prog='ptn_grz_converter',
#         description=(
#             "Conversor de formatos gráficos do TH01 (PC-98) ↔ BMP 4bpp indexado.\n"
#             "BMPs exportados são BMP 4bpp com paleta de 16 cores PC-98 embutida.\n"
#             "Editáveis diretamente em GIMP, Aseprite, Paint.NET etc.\n"
#             "O índice de cor no BMP corresponde EXATAMENTE ao índice PC-98."
#         ),
#         formatter_class=argparse.RawDescriptionHelpFormatter,
#         epilog=
"""
Formatos suportados:
  .PTN — Sprites 32×32, 4bpp. Transparente = índice 15.
  .BOS — Sprites de tamanho variável, 4bpp + alpha explícito. Transparente = índice 15.
  .GRC — Sprites monochrome de tamanho variável. Fundo = índice 0, ativo = qualquer outro.
  .GRZ — Imagens RLE 640×400, 4bpp. Transparente/fundo = índice 0 (preto).

Exemplos:
  # Extrair sprites de um .PTN para BMPs editáveis:
  python ptn_grz_converter.py extract sprites.PTN -o sprites_bmp/

  # Extrair imagens de um .GRZ:
  python ptn_grz_converter.py extract stage1.GRZ -o stage1_bmp/

  # Remontar .PTN a partir de BMPs editados:
  python ptn_grz_converter.py pack sprites_bmp/sprites_000.bmp sprites_bmp/sprites_001.bmp -o novo.PTN

  # Remontar .BOS (requer metadados do extract original):
  python ptn_grz_converter.py pack boss_bmp/boss_000.bmp -o novo.BOS --meta boss_bmp/boss.json

  # Remontar .GRZ:
  python ptn_grz_converter.py pack stage1_bmp/stage1_000.bmp -o novo.GRZ

Dicas de edição dos BMPs:
  • GIMP: Arquivo → Exportar como → BMP → marcar "Salvar como 4 bpp".
  • Aseprite: Arquivo → Exportar → BMP (funciona diretamente com paleta indexada).
  • A paleta de 16 cores está embutida no BMP — use-a sem alterar as entradas.
  • NÃO converta para RGB/RGBA e depois de volta; isso destrói os índices.
"""
#     )

#     sub = parser.add_subparsers(dest='command', required=True)

#     # extract
#     p_ext = sub.add_parser('extract', help='Extrai imagens de qualquer formato para BMP 4bpp')
#     p_ext.add_argument('input',
#                        help='Arquivo de entrada (.ptn, .bos, .grc ou .grz)')
#     p_ext.add_argument('-o', '--output',
#                        help='Diretório de saída (padrão: subdiretório com nome do arquivo)')
#     p_ext.set_defaults(func=extract)

#     # pack
#     p_pack = sub.add_parser('pack', help='Empacota BMPs 4bpp no formato de saída')
#     p_pack.add_argument('bmp_files', nargs='+',
#                         help='Arquivos BMP 4bpp de entrada (em ordem)')
#     p_pack.add_argument('-o', '--output', required=True,
#                         help='Arquivo de saída (.ptn, .bos, .grc ou .grz)')
#     p_pack.add_argument('--meta',
#                         help='Arquivo .json de metadados gerado pelo extract '
#                              '(obrigatório para .bos e .grc)')
#     p_pack.set_defaults(func=pack)

#     args = parser.parse_args()
#     try:
#         args.func(args)
#     except (ValueError, FileNotFoundError) as e:
#         print(f"Erro: {e}", file=sys.stderr)
#         sys.exit(1)


# if __name__ == '__main__':
#     main()
