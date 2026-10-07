#!/usr/bin/env python3
"""Ghost eye for a Raspberry Pi Zero.

Draws straight to the screen with no web browser.

Install once:   sudo apt install python3-pygame python3-pil
Run:            python3 eye.py
Quit:           Esc or Q
Test in a window instead of fullscreen:   python3 eye.py --window 480x320
"""
import base64
import io
import math
import os
import random
import sys
import time

# Plain software drawing: this board has no usable GPU for it
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_FRAMEBUFFER_ACCELERATION", "0")
os.environ.setdefault("SDL_RENDER_DRIVER", "software")

import pygame
from PIL import Image, ImageChops, ImageFilter

# ---------------------------------------------------------------- Settings
TILT = 30            # max tilt in degrees
SIZE_MIN = 0.86      # smallest size
SIZE_MAX = 1.14      # largest size
PAUSE_MIN = 1200     # shortest wait between twitches (ms)
PAUSE_MAX = 4500     # longest wait between twitches (ms)
BURST_CHANCE = 0.2   # how often it fires several twitches in a row
MOVE_MIN = 220       # fastest twitch movement (ms)
MOVE_MAX = 380       # slowest twitch movement (ms)
BLINK_MIN = 5000     # shortest wait between blinks (ms)
BLINK_MAX = 15000    # longest wait between blinks (ms)
BLINK_SHUT = 110     # how long it stays shut (ms)

COLOUR = (63, 188, 239)   # eye colour
EYE_SIZE = 0.56           # eye width as a fraction of the shorter screen side
PERSPECTIVE = 0.70        # smaller = stronger perspective distortion
FPS = 25                  # frames per second while it is moving
GLOW_SHRINK = 4           # glow is drawn this many times smaller, then enlarged (faster)

# The eye image (a PNG), built into this file
IMAGE_B64 = "iVBORw0KGgoAAAANSUhEUgAAAR0AAAETCAYAAAALYNILAAAT/0lEQVR4nO3da6xlZ13H8e9Mp61kpsyhTUGtmDZSxAhF0Jki0Jljz/RCRUvVFMGg8EbjpdrgJSG8sb5ovGECsW98oVJjCphAoYVymTM9pUhLCw0WRGtBIFqDKDMHM4V2ehlfPHt1bnvt57/Xep5nPZffN5lAZu/97P9eOfPp2mfvtdaWvfsPodRJvQz4ZeCngOdvrK2cY3nQ6vrmUeAx4F+AA8DNwIOxhlTh2lhbSfZc25I9kyqh7wNuAq4Zscb34NB6GfBW4P3AbwHfGD2dqqKtUw+gsmkXcD/jwDm5LcDPA5+fra+U0FEAXIJ7O3RepPWfB3wCeEWk9VVBCR11CfARYEfk59kJfBTB03xCp+1SgdMleJTQabjU4HQJnsYTOm02FThdgqfhhE57TQ1Ol+BpNKHTVrmA0yV4GkzotFNu4HQJnsYSOm2UKzhdgqehhE795Q5Ol+BpJKFTd6WA0yV4Gkjo1Ftp4HQJnsoTOnVWKjhdgqfihE59lQ5Ol+CpNKFTV7WA0yV4Kkzo1FNt4HQJnsoSOnVUKzhdgqeihE751Q5Ol+CpJKFTdq2A0yV4KkjolFtr4HQJnsITOmXWKjhdgqfghE55tQ5Ol+ApNKFTVgLnxARPgQmdchI48xM8hSV0ykjgLE7wFJTQyT+BY0vwFJLQyTuBs1yCp4CETr4JnGEJnswTOnkmcMYleDJO6OSXwAmT4Mk0oZNXAidsgifDhE4+CZw4CZ7MEjp5JHDiJngySuhMn8BJk+DJJKEzbQInbYIng4TOdAmcaRI8Eyd0pkngTJvgmTChkz6Bk0eCZ6KETtoETl4JngkSOukSOHkmeBIndNIkcPJO8CRM6MRP4JSR4EmU0ImbwCkrwZMgoRMvgVNmgidyQidOAqfsBE/EhE74BE4dCZ5ICZ2wCZy6EjwREjrhEjh1JngCJ3TCJHDqTvAETOiMT+C0keAJlNAZl8BpK8ETIKEzPIHTZoJnZEJnWAKn7QTPiITO8gkcBYJncEJnuQSOOj7BMyChY0/gqHkJniUTOrYEjlqU4FkioeNP4ChLgseY0FmcwFHLJHgMCZ3+BI4akuDxJHTmJ3DUmATPgoTOqQkcFSLB05PQOTGBo0ImeOYkdI4lcFSMBM9JCR2XwFExEzzHJXQEjkqT4JnVOjoCR6VM8NA2OgJHTVHz8LSKjsDx9xXgx4HTrQ/YWFvZMrv/TwBfjTRXDTUNz5a9+w9NPUPqBI6/O4ErNtZWnhi6wOr65unAfmBPsKnq69vAlcC9Uw+ysbaS7Lla29MROP7uBC4bAw7A7PFrwCeDTFVnTe7xtISOwPHXgfNUiMU21laeRPD4ag6eVtAROP6CgtMleEw1BU8L6Agcf1HA6RI8ppqBp3Z0BI6/qOB0CR5TTcBTMzoCx18ScLoEj6nq4akVHYHjLyk4XYLHVNXw1IiOwPE3CThdgsdUtfDUho7A8TcpOF2Cx1SV8NSEjsDxlwU4XYLHVHXw1IKOwPGXFThdgsdUVfDUgI7A8ZclOF2Cx1Q18JSOjsDxlzU4XYLHVBXwlIyOwPFXBDhdgsdU8fCUio7A8VcUOF2Cx1TR8JSIjsDxVyQ4XYLHVLHwbJt6gCUTOP7uBC4Dnlpd35x4lFF18KyjE4H11cGTxYnArJWEjsDx9ww4I9bYAfwocBFwIXA+8APAObM/ZwBnAUeAw8Dm7H8PA48AXwMeBh4E/nn290MTPP6Kg6cUdASOv6Hg7MD9w14DXo3D5jTD484Azp796espHD6fwsGxzvIICR5/RcFTwjmSBY6/ZcHZCVwNvB7YhwMkRUdw501+L/BB3DmCrW1D8PgafM5lnSP5WALH3zLg7AL+Bvc26N3AVaQDh9lzXTV77kdms+wyPla/XPZXxC+Xc0ZH4PizgvPTuH+s9wFvBrbHHcvUdtws9+Fme63hMYLHX/bw5IqOwPFnAedy4DPA7bhtmmuXALfhALrcc1/B4y9reHJER+D484HzAuD9wMeA3amGCtAu3MwfwL2GvgSPv2zhyQ0dgeNvETjbgLfhPjG6JuVQgXsd7jW8jf5PWAWPvyzhyQkdgeNvETgvBD4N3Ag8K+VQkXoW7rV8Gvfa5iV4/GUHTy7oCBx/i8B5E/AA9k+CSmoX7rW9qed2weMvK3hyQEfg+OsDZxvwLuBm8vhEKlbbca/xL5n/dkvw+MsGnqnRETj++sA5C/gwcF3yiabrN3Gv+dlzbhM8/rKAZ0p0BI6/PnCeC9yN/+PlGrscB8tz59wmePxNDs9U6Agcf33gnAfcBbw0+UT59FLcNjhvzm2Cx9+k8EyBjsDx1wfOubhjl16UfKL8ehFuW5w75zbB428yeFKjI3D89YGzE4Fzch08O+fcJnj8TQJPyqPMBY6/PnDOAO4ALk0+URkdAF6DO4r95HR0ur/BR6cPKdWejsDxt+h7OH+MwFnUpcCf9dymPR5/Sfd4UqAjcPwtAud1wPUphym063Dbal6Cx18yeGKjI3D8LQLnfOCvgS0pByq0LbhtdX7P7YLHXxJ4YqIjcPz5Dt58D/CcpBOV3XNwZyXUQaLDiw5PLHQEjj/f6SmuAy5ON0417QZ+e8HtgsdfVHhioCNw/PnAOQ+4Id041fWHzP/iYJfg8RcNntDoCBx/ljP+vQN3bJUa1lm4bdibLuhnKgo8IdEROP4sV968FHeVBjWu1+NQ6U3wmAoOTyh0BI4/66V+b0wxTCN5t6XgMRUUnhDoCBx/VnBei355HLLdGK4yIXhMBYNnLDoCx58VHIDfjz1Mg/2e5U6Cx1QQeMagI3D8LQPOK9DxQTHai3HvUfCYGg3PUHQEjr9lwAH41ZjDNN6vWe8oeEyNgmcIOgLH37LgPBu4NuI8rXct809xOjfBY2owPMuiI3D8LQsOuAMVaz6x+tRtZ8nrgAkeU4PgWQYdgeNvCDigvZwULb2NBY+ppeGxoiNw/A0FZwewL8I86sTWGPDzK3hMLQWPBR2B428oOOC+gXxm4HnUqZ2J5xvKfQkeU2Z4fOgIHH9jwAF3HJZK0+A9SsFjygTPInQEjr+x4AC8MtQwyturxjxY8JjywtOHjsDxFwKc7bR9/arUXcTITwkFj6mF8MxDR+D4CwEOwIuB0wLMo2ydBrxk7CKCx1QvPCejI3D8hQIHtJczRReFWETwmJoLz/HoXIzA8RUSHIAfCrSOsndhqIUEj6kOnt3dX3TofD9wGwJnUaHBAbgg4FrK1vkhFzsOnrtCrltZO4EPAs+DY+j8BfOvCa1cMcAB+MHA6yl/zw+94AyefQieRX0v8E5w6LwEfQ1/UbHAATg7wppqcVG2ueAxdS3wI1uBN6KLufX1MHBFJHAAzom0ruov2jafwXMZ8JVYz1F4W4Bf2ApcMfUkGfeGjbWVJyKuf0bEtdX8om7z2c/LG2I+R+FdvpXAv1irrH+KvL5+cZ++FNv8gQTPUWov2IouW9vbbHdZqaWK+Ha8hs7eChyceopcW13f7LsmdqgOR15fnVr0bZ7g56bkDm4Fvj71FBkX+xvDRyKvr04txTZ/eYLnKLUvbwXumHqKjLtldX3z9Ijrfyvi2mp+Ubf57OflPTGfo/A+vhX4e+DpqSfJtAuBT0TcXdZb2/RF2+azn5MD6JvmfT0N/MNW4Es4eNT89gL7I8HzHxHWVIuLss1nPx93Aq+OsX4l3QL8a3cYxB8A/z3hMLkXC55/D7ye8ve10AsKHFP/CVwPx469+gZwNfDtiQYqoRjw6Jur6Xs45GICx9Qh4Crgf+HEU1t8BngNgmdRoeGJ/eVDdWpfCLWQwDF1CHdoyDPb/eSTeN2D4PEVEp4vAvoiWbqeAh4MsZDAMdWB87nj/3Le6UoFj79Q8DxKoH8EytSDuG0+KoFjai440H9idsHjLxQ8/xhiGGVq9LYWOKZ6wYHFl6ARPP5CwLM/1DDK2/qYBwscUwvBAf/F9gSPv7HwrAOPB5xHze9xRgAvcEx5wQHbZYUFj78x8Bxm5H+Blal1Bh7sKXBMmcABGzogeCyNged9oYdRpzRoGwscU2ZwwI4OCB5LQ+H5AAE+VVG9PQrcuuyDBI6ppcCB5dABwWNpCDz/h/Z2YvY+lvyZFTimlgYHlkcHBI+lIfD8Vaxh1HLbVuCYGgQODEMHBI+lZeG5F/hUxHla7W7ctjUlcEwNBgeGowOCx9Ky8PxJzGEa7U+tdxQ4pkaBA+PQAcFjaRl4PgzcF3melroPt029CRxTo8GB8eiA4LFkheco8PYE87TS23HbdGECx1QQcCAMOiB4LFnh2Q98KME8tXcbhm8gCxxTwcCBcOiA4LFkhed3gccSzFNrj+G24cIEjqmg4EBYdEDwWNqL+y/wIni+DNyQZpwq+yM8ZwgUOKaCgwPh0QHBY8kCzzuAz6YZp6o+B/y55z4Cx18UcCAOOiB4LPngeQL4JXR4xDI9CrwRt+36Ejj+ooED8dABwWPJB8+/Ab+ebpzi+w3cNutL4PiLCg7ERQcEjyUfPH8H3JRunGK7Cbh5we0Cx190cCA+OiB4LPngeSvuypFqfgdw26gvgeMvCTiQBh0QPJYWwXME+DkCXj6lor6A2zZHem4XOP6SgQOwZe/+Qymep+sngTuAnSmftLDuAvYBT8657VzcQaEvTDpRvj0E7AG+2XO7wPF3CLhsY20lCTiQbk+nS3s8/hbt8fwPcCnu+vOt9yVgDYEzpqR7OF2p0QHBY2kRPI8Al+C2Y6vdg9sGj/TcLnD8TQIOTIMOCB5Li+A5iHsLdnvSifLodtxrP9hzu8DxNxk4MB06IHgsLYLnO8A1wDsxHEldQUeBd+Fe83d67iNw/E0KDkyLDggeS4vgeRK4HvfpzWa6kZK3iXuNv8P8X7CDwLE0OTgwPTogeCztxV23qe97PLcCL6fOE4B9Fvfabl1wH4HjLwtwIA90QPBY2sNieL4KvAp34qrvphoqYt/FvZZX4l5bXwLHXzbgQD7ogOCx5IPnSeBG4CLcSaxK7Xbca7gRHbw5tqzAgbzQAcFjyQcPuPPx/CxwBXB/iqECdT9wJfAzuNewKIHjLztwID90QPBYssAD8HHgYtw/4rtjDzWiu4GrcbN+zHB/geMvS3AgT3RA8FiywnMU93ZlD7Ab+FvyOEfPo7hZduNm+xC2j/4Fjr9swYF80QHBY8kKT9f9wFuA84BfAT5C/4GSMToye843z2Z4C8u9/RM4/rIGB9If8DkkHSTq75O445D6vsOyqB2zx+7DHVrwYuC0QHM9BXwR9/ZpPw7IwwPXEjj+BoOzsbYSfJi+SkAHBI+lMfAc3w4cPBcBFwIX4PZKzpn9ORPYPrvvo8DjwLdmfx7Bfbz9MPAgDpyhyByfwPE3ag8nJTrW3fKp695qCZ7+urdaY+E5jLv2t/n635ETOP6yf0t1fKWgA4LH0jPwbKytjN3jmbzZZWLuwn1BUM2vKHAg718kz0u/XPa3B1g3Xjs92wSOqeLAgfLQAcFjqWh4BI6pIsGBMtEBwWOpSHgEjqliwYFy0QHBY6koeASOqaLBgbLRAcFjqQh4BI6p4sGB8tEBwWMpa3gEjqkqwIE60AHBYylLeASOqWrAgXrQAcFjKSt4BI6pqsCButABwWMpC3gEjqnqwIH60AHBY2lSeASOqSrBgTrRAcFjaRJ4BI6pasGBetEBwWMpKTwCx1TV4EDd6IDgsZQEHoFjqnpwoH50QPBYigqPwDHVBDjQBjogeCxFgUfgmGoGHGgHHRA8loLCI3BMNQUOtIUOCB5LHTynj1lk9niBs7jmwIH20AHBY2kP8NDq+uauZfd6Vtc3t62ub16MO0+ywOmvSXCgrNOVhkynPvV3AXDf7P9vsTxgdX3Tct0q1TA40OaeTpf2eNQUNQ0OtI0OCB6VtubBAaEDgkelSeDMEjouwaNiJnCOS+gcS/CoGAmckxI6JyZ4VMgEzpyEzqkJHhUigdOT0Jmf4FFjEjgLEjr9CR41JIHjSegsTvCoZRI4hoSOP8GjLAkcY0LHluBRixI4SyR07AkeNS+Bs2RCZ7kEjzo+gTMgobN8gkeBwBmc0BmW4Gk7gTMioTM8wdNmAmdkQmdcgqetBE6AhM74BE8bCZxACZ0wCZ66EzgBEzrhEjx1JnACJ3TCJnjqSuBESOiET/DUkcCJlNCJk+ApO4ETMaETL8FTZgInckInboKnrAROgoRO/ARPGQmcRAmdNN0DXIngyTWBkzChk657ETw5JnASJ3TSJnjySuBMkNBJn+DJI4EzUUJnmgTPtAmcCRM60yV4pkngTJzQmTbBkzaBk0FCZ/oET5oOAfsQOJMndPJI8MStA+eBqQdRQienBE+cBE5mCZ28EjxhEzgZJnTyS/CESeBkmtDJM8EzLoGTcUIn3wTPsARO5gmdvBM8yyVwCkjo5J/gsSVwCknolJHgWZzAKSihU06CZ34Cp7CETlkJnhMTOAUmdMpL8LgETqEJnTJrHR6BU3BCp9xahUfgFJ7QKbvW4BE4FSR0yq8VeAROJQmdOqodHoFTUUKnnmqFR+BUltCpq9rgETgVJnTqqxZ4BE6lCZ06Kx0egVNxQqfeSoVH4FSe0Km70uAROA0kdOqvFHgETiNt21hbmXoGFb97V9c3rwQ+Cuycepg5HQL2baytCJwG0p5OO+W6x6M9nMYSOm2VGzwCp8GETnvlAo/AaTSh02ZTwyNwGk7otNtU8AicxhM6bZcaHoGjhI5KBo/AUYDQUa57gVXg65HW/y/gUgSOQuioY30e2A28FzgaaM2ngVuAH5utrxTbph5AZdU3gV8EbgCuxb3t+uEl1zgIPAwcAN4NPBRyQFV+/w9SUNHR09LwrwAAAABJRU5ErkJggg=="

# ---------------------------------------------------------------- Maths
def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def mat_inv(m):
    (a, b, c), (d, e, f), (g, h, i) = m
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    return [
        [(e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det],
        [(f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det],
        [(d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det],
    ]


def translate(x, y):
    return [[1, 0, x], [0, 1, y], [0, 0, 1]]


def scale(s):
    return [[s, 0, 0], [0, s, 0], [0, 0, 1]]


def pose_matrix(rx, ry, rz, size, dist):
    """Tilt a flat picture in 3D and project it with perspective.

    Works on coordinates centred on the picture; angles are in degrees.
    """
    ax, ay, az = math.radians(rx), math.radians(ry), math.radians(rz)
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    rot_x = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    rot_y = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    rot_z = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    r = mat_mul(rot_x, mat_mul(rot_y, rot_z))
    return [
        [dist * size * r[0][0], dist * size * r[0][1], 0],
        [dist * size * r[1][0], dist * size * r[1][1], 0],
        [-size * r[2][0], -size * r[2][1], dist],
    ]


def project(m, x, y):
    w = m[2][0] * x + m[2][1] * y + m[2][2]
    return (m[0][0] * x + m[0][1] * y + m[0][2]) / w, (m[1][0] * x + m[1][1] * y + m[1][2]) / w


def warp(image, m, out_size):
    """Draw `image` through matrix `m` (image pixels -> output pixels)."""
    inv = mat_inv(m)
    k = inv[2][2]
    coeffs = [inv[0][0] / k, inv[0][1] / k, inv[0][2] / k,
              inv[1][0] / k, inv[1][1] / k, inv[1][2] / k,
              inv[2][0] / k, inv[2][1] / k]
    return image.transform(out_size, Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BILINEAR)


def bezier(x1, y1, x2, y2):
    """Easing curve, same as CSS cubic-bezier()."""
    def curve(u, p1, p2):
        return 3 * (1 - u) ** 2 * u * p1 + 3 * (1 - u) * u ** 2 * p2 + u ** 3

    def ease(t):
        if t <= 0:
            return 0.0
        if t >= 1:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(24):
            mid = (lo + hi) / 2
            if curve(mid, x1, x2) < t:
                lo = mid
            else:
                hi = mid
        return curve((lo + hi) / 2, y1, y2)
    return ease


EASE_MOVE = bezier(0.4, 0, 0.2, 1)    # fast but smooth
EASE_IN = bezier(0.42, 0, 1, 1)
EASE_OUT = bezier(0, 0, 0.58, 1)


def rand(a, b):
    return a + random.random() * (b - a)


# ---------------------------------------------------------------- Drawing
class Renderer:
    """Makes one finished frame (eye + glow on black) for any pose."""

    def __init__(self, width, height, eye, dist):
        self.width = width            # frame size in pixels
        self.height = height
        self.dist = dist              # perspective distance in pixels

        shape = Image.open(io.BytesIO(base64.b64decode(IMAGE_B64))).convert("RGBA").getchannel("A")
        fit = eye / max(shape.size)
        shape = shape.resize((max(1, round(shape.width * fit)), max(1, round(shape.height * fit))),
                             Image.Resampling.LANCZOS)

        def padded(pad):
            side = eye + 2 * pad
            img = Image.new("L", (side, side), 0)
            img.paste(shape, ((side - shape.width) // 2, (side - shape.height) // 2))
            return img

        # Sharp eye with a thin soft edge
        base = padded(math.ceil(eye * 0.04))
        halo = base.filter(ImageFilter.GaussianBlur(eye * 0.0107)).point(lambda v: int(v * 0.55))
        self.sharp = ImageChops.screen(base, halo)

        # Blurred copy for the glow, kept at quarter size because it is soft anyway
        blurred = padded(math.ceil(eye * 0.2)).filter(ImageFilter.GaussianBlur(eye * 0.0625))
        small = max(2, blurred.width // GLOW_SHRINK)
        self.glow = blurred.resize((small, small), Image.Resampling.BOX)
        self.glow_unit = blurred.width / small   # glow pixels -> full-size pixels

    def render(self, rx, ry, rz, size, glow_opacity, glow_size):
        cw, ch = self.width, self.height
        m = pose_matrix(rx, ry, rz, size, self.dist)
        centre = translate(cw / 2, ch / 2)

        # Glow, drawn at low resolution then enlarged
        g = self.glow.width
        m_glow = mat_mul(scale(1 / GLOW_SHRINK), mat_mul(centre, mat_mul(m, mat_mul(
            scale(glow_size * self.glow_unit), translate(-g / 2, -g / 2)))))
        glow = warp(self.glow, m_glow, (cw // GLOW_SHRINK, ch // GLOW_SHRINK))
        glow = glow.point([int(v * glow_opacity) for v in range(256)])
        frame = glow.resize((cw, ch), Image.Resampling.BILINEAR)

        # Sharp eye, drawn only inside the box it covers
        n = self.sharp.width
        h = n / 2
        pts = [project(m, x, y) for x, y in ((-h, -h), (h, -h), (h, h), (-h, h))]
        x0 = max(0, math.floor(min(p[0] for p in pts) + cw / 2) - 1)
        y0 = max(0, math.floor(min(p[1] for p in pts) + ch / 2) - 1)
        x1 = min(cw, math.ceil(max(p[0] for p in pts) + cw / 2) + 1)
        y1 = min(ch, math.ceil(max(p[1] for p in pts) + ch / 2) + 1)
        if x1 > x0 and y1 > y0:
            m_sharp = mat_mul(translate(cw / 2 - x0, ch / 2 - y0), mat_mul(m, translate(-h, -h)))
            sharp = warp(self.sharp, m_sharp, (x1 - x0, y1 - y0))
            box = (x0, y0, x1, y1)
            frame.paste(ImageChops.screen(frame.crop(box), sharp), box)
        return frame


PALETTE = [(COLOUR[0] * i // 255, COLOUR[1] * i // 255, COLOUR[2] * i // 255) for i in range(256)]


def to_surface(frame):
    surf = pygame.image.frombuffer(frame.tobytes(), frame.size, "P")
    surf.set_palette(PALETTE)
    return surf.convert()


# ---------------------------------------------------------------- Behaviour
def next_target(pose, first):
    """Pick where the eye twitches to next."""
    target = dict(pose)
    if not first and random.random() < 0.35:
        # Size and glow jump on their own, keeping the current tilt
        target["size"] = rand(SIZE_MIN, SIZE_MAX)
        g = random.random()
    else:
        centre = random.random() < 0.2      # sometimes snap back to face forward
        target["rx"] = 0 if centre else rand(-TILT, TILT)
        target["ry"] = 0 if centre else rand(-TILT, TILT)
        target["rz"] = 0 if centre else rand(-4, 4)
        target["size"] = rand(SIZE_MIN, SIZE_MAX)
        k = (target["size"] - SIZE_MIN) / (SIZE_MAX - SIZE_MIN)
        g = min(1, max(0, k * 0.6 + random.random() * 0.4))
    target["glow_opacity"] = 0.3 + 0.7 * g
    target["glow_size"] = 0.95 + 0.45 * g
    return target


def main(argv=None, max_seconds=None):
    argv = sys.argv[1:] if argv is None else argv
    pygame.display.init()
    if "--window" in argv:
        w, h = argv[argv.index("--window") + 1].lower().split("x")
        screen = pygame.display.set_mode((int(w), int(h)))
    else:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Eye")
    pygame.mouse.set_visible(False)

    width, height = screen.get_size()
    short = min(width, height)
    # The part of the screen that gets redrawn: full height, a bit wider than tall
    cw = min(width, int(short * 1.5)) // GLOW_SHRINK * GLOW_SHRINK
    ch = short // GLOW_SHRINK * GLOW_SHRINK
    renderer = Renderer(cw, ch, max(8, int(short * EYE_SIZE)), short * PERSPECTIVE)
    area = pygame.Rect((width - cw) // 2, (height - ch) // 2, cw, ch)
    screen.fill((0, 0, 0))
    pygame.display.flip()

    pose = {"rx": 0, "ry": 0, "rz": 0, "size": 1, "glow_opacity": 0.6, "glow_size": 1}
    current = to_surface(renderer.render(**pose))

    def make_plan(start_at, first=False):
        duration = rand(MOVE_MIN, MOVE_MAX) / 1000
        return {"start_at": start_at, "from": dict(pose), "to": next_target(pose, first),
                "duration": duration, "count": max(2, round(duration * FPS)), "frames": []}

    start = time.monotonic()
    plan = make_plan(start, first=True)   # the move being prepared
    playing = None                        # (frames, start time, duration)
    next_at = start
    blink_at = start + rand(BLINK_MIN, BLINK_MAX) / 1000
    blink_started = None
    shown = None
    stats = {"moves": 0, "blinks": 0, "draws": 0}
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q)):
                pygame.quit()
                return stats
        now = time.monotonic()
        if max_seconds is not None and now - start > max_seconds:
            pygame.quit()
            return stats

        # Start the prepared move when it is due
        if playing is None and len(plan["frames"]) == plan["count"] and now >= plan["start_at"]:
            playing = (plan["frames"], now, plan["duration"])
            pose = plan["to"]
            burst = random.random() < BURST_CHANCE
            next_at = now + (rand(MOVE_MAX, MOVE_MAX + 200) if burst else rand(PAUSE_MIN, PAUSE_MAX)) / 1000
            stats["moves"] += 1

        # Which picture is showing right now
        if playing is not None:
            frames, t0, duration = playing
            step = int((now - t0) / duration * len(frames))
            if step >= len(frames) - 1:
                current = frames[-1]
                playing = None
                plan = make_plan(next_at)
            else:
                current = frames[step]

        # Blink: shrink to nothing, stay shut, reopen
        size, alpha = 1.0, 1.0
        if blink_started is None and now >= blink_at:
            blink_started = now
            blink_at = now + rand(BLINK_MIN, BLINK_MAX) / 1000
            stats["blinks"] += 1
        if blink_started is not None:
            t = now - blink_started
            shut = BLINK_SHUT / 1000
            if t < 0.14:
                alpha = 1 - EASE_IN(t / 0.14)
            elif t < 0.14 + shut:
                alpha = 0.0
            elif t < 0.14 + shut + 0.2:
                alpha = EASE_OUT((t - 0.14 - shut) / 0.2)
            else:
                blink_started = None
            size = 0.02 + 0.98 * alpha

        # Redraw only when something changed
        key = (id(current), round(size, 3))
        if key != shown:
            shown = key
            stats["draws"] += 1
            screen.fill((0, 0, 0), area)
            if size >= 0.999:
                screen.blit(current, area.topleft)
            elif alpha > 0.004:
                shrunk = (max(1, int(cw * size)), max(1, int(ch * size)))
                try:
                    small = pygame.transform.smoothscale(current, shrunk)
                except ValueError:
                    small = pygame.transform.scale(current, shrunk)
                small.set_alpha(int(alpha * 255))
                screen.blit(small, small.get_rect(center=area.center))
            pygame.display.update(area)

        # Use quiet moments to prepare the next move's frames, one at a time
        if playing is not None or blink_started is not None:
            clock.tick(30)
        elif len(plan["frames"]) < plan["count"]:
            e = EASE_MOVE((len(plan["frames"]) + 1) / plan["count"])
            a, b = plan["from"], plan["to"]
            mix = {k: a[k] + (b[k] - a[k]) * e for k in a}
            plan["frames"].append(to_surface(renderer.render(**mix)))
        else:
            time.sleep(max(0.0, min(0.05, min(plan["start_at"], blink_at) - now)))


if __name__ == "__main__":
    main()
