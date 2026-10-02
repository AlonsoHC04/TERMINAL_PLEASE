#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ingress-monitor :: Ministerio de Admision de Vostrokia - Puesto Remoto WS-07

Un juego tipo "Papers, Please" disfrazado de stream de logs.
Compara la informacion de los "documentos" (lineas DEBUG/TRACE/INFO) y decide
si el solicitante entra o no. Todo desde la comodidad de tu home office.

Uso:
    python ingress_monitor.py            # menu inicial (continuar / nueva partida)
    python ingress_monitor.py --new      # salta el menu y empieza partida nueva
    python ingress_monitor.py --stealth  # sin colores ni emblema (maximo bajo perfil)
    python ingress_monitor.py --fast     # logs sin animacion
"""

import argparse
import datetime as dt
import json
import os
import random
import sys
import textwrap
import time
from pathlib import Path

VERSION = "1.1.1"
LINE_WIDTH = 120       # ancho maximo de linea; los textos mas largos se cortan
SAVE_PATH = Path.home() / ".ingress_monitor_state.json"
START_DATE = dt.date(1984, 3, 1)
LAST_DAY = 10
SHIFT_START = 6 * 60   # 06:00
SHIFT_END = 18 * 60    # 18:00
MAX_IDLE = 90          # segundos reales maximos que cuenta un comando (por si te vas a una junta)
REAL_TO_GAME = 1.0     # minutos de juego por segundo real
WINDOWS = os.name == "nt"

SALARY = 5
REASON_BONUS = 2
CITATION_FINE = 5
RENT, FOOD, HEAT, MEDICINE = 20, 10, 5, 15

# ---------------------------------------------------------------------------
# Mundo
# ---------------------------------------------------------------------------
HOME = "Vostrokia"
NATIONS = {
    "Vostrokia": ["Grestavo", "Orvenko", "Pashkov"],
    "Drovnia": ["Velsk", "Drovgrad", "Tamir"],
    "Kastrelia": ["Kastel", "Merin", "Sorova"],
    "Ulmeria": ["Ulmen", "Brask", "Hollov"],
    "Tsavaria": ["Tsavin", "Nokor", "Elvast"],
}
NAT_CODE = {"Vostrokia": "VK", "Drovnia": "DR", "Kastrelia": "KS", "Ulmeria": "UL", "Tsavaria": "TS"}
FOREIGN = [n for n in NATIONS if n != HOME]
FAKE_CITIES = ["Novomir", "Zlatograd", "Belvask", "Korvinsk", "Petrovo-9"]
VALID_SEALS = ["MX-7731", "MX-2208", "MX-5590", "MX-4417"]
FIELDS = ["MINERIA", "AGRICULTURA", "CONSTRUCCION", "SIDERURGIA", "PESCA", "TEXTIL"]
PURPOSES = ["WORK", "VISIT", "TRANSIT", "WORK", "IMMIGRATE"]
DURATIONS = {"WORK": ["6M", "1Y", "2Y"], "VISIT": ["14D", "1M", "2M"],
             "TRANSIT": ["2D", "3D"], "IMMIGRATE": ["PERM"]}
VACCINES = ["TIFUS", "COLERA", "SARAMPION", "FIEBRE_AMARILLA", "TETANOS", "RUBEOLA"]

FIRST_M = ["Ivan", "Dmitri", "Sergei", "Viktor", "Pavel", "Mikhail", "Anton", "Yuri", "Boris",
           "Oleg", "Nikolai", "Lev", "Fyodor", "Grigor", "Alexei", "Konstantin", "Emil", "Radek"]
FIRST_F = ["Anya", "Olga", "Irina", "Svetlana", "Natalia", "Katya", "Vera", "Ludmila", "Tatiana",
           "Yelena", "Mila", "Zoya", "Daria", "Galina", "Ilsa", "Mirela"]
LAST = ["KOVAC", "PETROV", "SOKOLOV", "VOLKOV", "MOROZOV", "LEBEDEV", "NOVAK", "KOZLOV", "ORLOV",
        "ZAITSEV", "POPESCU", "HORVAT", "DRAGAN", "MIKHAILOV", "BELOV", "GROMOV", "KARPOV", "TITOV",
        "STRELKOV", "VASILEV", "LAZAR", "BOGDAN", "RYBAK", "SEMENOV", "DUBROV", "KRAVETS"]

# Dia en que cada regla entra en vigor
RULE_DAY = {"foreigners": 2, "city": 3, "workpass": 4, "weight": 4,
            "banned": 5, "wanted": 5, "vaccine": 6, "seal": 7}

REASONS = {
    "expired": "documento vencido",
    "nation": "nacionalidad no admitida",
    "missing": "falta un documento requerido",
    "name": "el nombre no coincide entre documentos",
    "id": "el numero de pasaporte (pid) no coincide",
    "city": "ciudad emisora invalida para esa nacion",
    "weight": "el peso no coincide con la bascula (>2kg)",
    "wanted": "persona en la lista de buscados",
    "vaccine": "falta vacuna de POLIO",
    "seal": "sello del ministerio invalido",
}

POLICY_NEWS = {
    1: ["Solo ciudadanos de Vostrokia pueden ingresar.",
        "Verifique que el pasaporte no este vencido (exp >= ref_date)."],
    2: ["Se permite la entrada a extranjeros con permiso de entrada (entry_permit).",
        "holder y pid_ref del permiso deben coincidir con el pasaporte. El permiso no puede estar vencido."],
    3: ["Verifique que issuer_city corresponda a la nacion del pasaporte (ver 'rules')."],
    4: ["Extranjeros con purpose=WORK requieren work_pass vigente.",
        "El peso del permiso (wt) debe coincidir con la bascula (+-2kg)."],
    5: ["ATAQUE EN LA FRONTERA: ciudadanos de Drovnia tienen prohibida la entrada.",
        "Se publica lista diaria de buscados. Denegar si el nombre aparece."],
    6: ["Brote de polio: extranjeros deben presentar vax_cert que incluya POLIO.",
        "holder y pid_ref del certificado deben coincidir con el pasaporte."],
    7: ["Falsificaciones detectadas: el permiso debe llevar un sello valido del ministerio."],
    8: ["Sin cambios de politica. Se reporta aumento de documentos falsos. Mantenga la vigilancia."],
    9: ["Sin cambios de politica. Recuerde: el ministerio ve todo."],
    10: ["Ultimo dia del periodo. Su desempeno sera evaluado al cierre."],
}

MINISTRY_INTRO = [
    "Felicidades, ciudadano. Su nombre fue seleccionado en la loteria laboral de marzo.",
    "Ha sido asignado al Puesto de Control REMOTO WS-07. Trabajara desde casa.",
    "Su apartamento clase 8 en Grestavo ya ha sido asignado. Su familia lo espera.",
    "Revise los documentos de cada solicitante y decida. Gloria a Vostrokia.",
]

JORJI_CHAT = [
    "Amigo! Soy yo, Jorji. Tu recuerdas. Jorji siempre recuerda caras amigas.",
    "Jorji tiene nuevo negocio. No preguntes que negocio. Es negocio.",
    "Hoy hace mucho frio en la fila. Jorji usa tres abrigos. Dos no son suyos.",
    "Tu jefe esta mirando? Pon cara seria. Mas seria. Perfecto, muy profesional.",
    "En Cobrastan el pasaporte es de carton. Muy bueno. Hasta que llueve.",
    "Jorji encontro sello del ministerio en la basura. Casi nuevo. Te interesa?",
    "Jorji no es contrabandista. Jorji es... facilitador de bienes.",
    "Si la computadora no funciona, golpeala. Asi arreglo yo mi radio. Y a mi primo.",
    "Mi tia dice hola. No la conoces. Ella tampoco a ti. Pero dice hola.",
    "Escribo desde telefono publico. Cobran por palabra. Adios.",
    "Pregunta: cuantos documentos es demasiados documentos? Pregunto por un amigo.",
    "Jorji vio a tu vecino. Muy sospechoso. Igual que todos aqui. Igual que Jorji.",
    "Trabajar desde casa es buena idea. Jorji tambien trabaja desde casa. Casa de otro.",
    "Si alguien pregunta, Jorji estuvo contigo toda la tarde. Gracias amigo.",
]

FAMILY_MSGS = [
    "Tu hijo pregunta por que trabajas en pijama.",
    "La suegra dice que tu terminal hace demasiado ruido.",
    "Se acabo el pan. Otra vez.",
    "El tio dice que en su epoca los pasaportes se revisaban a mano. En la nieve. Cuesta arriba.",
    "Tu esposa pregunta si ya pagaron. Ella sabe que no. Solo pregunta.",
    "El hijo dibujo un aguila en la pared. Dice que es para el ministerio.",
]

MINISTRY_MSGS = [
    "Recordatorio: el uso de la terminal ministerial para fines personales esta prohibido.",
    "La productividad de su puesto esta siendo monitoreada. Gloria a Vostrokia.",
    "La camara web debe permanecer encendida. (No la encontramos. La tapo?)",
    "Encuesta de satisfaccion laboral: usted esta satisfecho. Gracias por participar.",
    "Se recuerda a los teletrabajadores que el pijama no es uniforme reglamentario.",
    "Un mensaje de su supervisor: 'sigo esperando el reporte'. No sabemos cual reporte.",
]

COWORKER_MSGS = [
    ("ivanka.ws03", "Alguien sabe si hoy pagan? Mi refrigerador hace eco."),
    ("ivanka.ws03", "Me acaba de pasar un tipo con pasaporte de Jorjigrad. Jorjigrad! Ustedes tambien?"),
    ("petr.ws11", "Tip: la bascula nunca miente. La gente si."),
    ("petr.ws11", "Mi supervisor me pidio 'mas productividad'. Le aprobe a su suegra. Ya no me habla."),
    ("milos.ws05", "Se me fue la luz 20 minutos. Les juro que el pasaporte del abuelo parecia valido."),
    ("milos.ws05", "Alguien tiene la lista de sellos de hoy? La mia la uso mi hijo para dibujar."),
    ("ivanka.ws03", "Recuerden revisar las ciudades. Kastel no es de Ulmeria, por mucho que insistan."),
    ("petr.ws11", "Si ven a un tal Costava, saluden de mi parte. Me debe 5 creditos."),
]

# Lo que dicen los solicitantes al llegar. A veces dan pistas sobre sus documentos... o no.
GREETINGS = [
    "Buenos dias.", "Buen dia, camarada.", "Hola.", "...", "Gloria a Vostrokia.",
    "Buenas. Larga fila hoy.", "Hola? Me escucha? Creo que se congelo su camara.",
    "Buenos dias. Esto es por videollamada? Que moderno.", "Buenas tardes. O dias. Ya no se.",
]
SMALLTALK = [
    "Llevo seis horas en la fila. Seis.", "Esta conexion es muy lenta. Como todo aqui.",
    "Mi hijo tiene fiebre, por favor rapido.", "Escuche que la renta subio otra vez.",
    "Tiene usted cara de cansado. Bueno, su camara.", "Hace frio. Siempre hace frio.",
    "Estoy nervioso, es mi primera vez cruzando.", "Todos mis papeles estan en orden. Creo.",
    "Mi primo trabaja en el ministerio. No es amenaza, solo comentario.",
    "Por favor no me pregunte nada dificil, no he desayunado.",
]
HOME_LINES = [
    "Por fin en casa. Tres meses fuera.", "Vuelvo de visitar a mi madre. No pregunte.",
    "Soy de aqui. Nacido y congelado aqui.", "Regreso de un viaje de trabajo. Nada interesante.",
]
PURPOSE_LINES = {
    "WORK": ["Vengo a trabajar. Dicen que pagan en pan.", "Trabajo en la mina. O en lo que haya.",
             "Me ofrecieron empleo. Espero que exista."],
    "VISIT": ["Solo vengo a visitar a mi hermana. Dos semanas, lo prometo.",
              "Visita familiar. Mi tia cumple 90. O 91."],
    "TRANSIT": ["Solo estoy de paso. Sin ofender, no me quedaria aqui.",
                "Voy hacia el norte. Mas frio, pero mas barato."],
    "IMMIGRATE": ["Quiero empezar una nueva vida aqui. Una mas fria.",
                  "Me mudo con todo. Bueno, con esta maleta."],
}
FLAW_LINES = {
    "pass_expired": ["Mi pasaporte... creo que todavia sirve. Lo renuevo la proxima semana."],
    "city": ["El pasaporte me lo tramito mi primo. El conoce gente.",
             "Lo saque en otra ciudad. Es lo mismo, no?"],
    "permit_missing": ["El permiso? Pense que con el pasaporte bastaba."],
    "permit_name": ["Si, el permiso tiene una letrita distinta. Error del ministerio, no mio."],
    "permit_id": ["Saque pasaporte nuevo hace poco. El permiso es del viejo, pero es igual."],
    "permit_expired": ["El permiso vencio hace poco, pero ya estoy aqui, no?"],
    "weight": ["He comido mucho ultimamente. O muy poco. Depende de la semana."],
    "seal": ["El sello me lo pusieron en una oficina... muy oficial. Con cortinas."],
    "wp_missing": ["Vengo a trabajar. Los papeles de trabajo los trae mi jefe. Despues."],
    "wp_name": ["El pase de trabajo es de mi hermano. Somos casi iguales."],
    "wp_expired": ["Mi pase de trabajo esta un poco vencido. Pero sigo sabiendo trabajar."],
    "vax_missing": ["Vacunas? Nunca me enfermo. Tengo buena sangre."],
    "vax_nopolio": ["Tengo todas las vacunas. Bueno, casi todas."],
    "vax_id": ["El certificado lo hizo una enfermera muy ocupada."],
    "vax_name": ["El certificado lo hizo una enfermera muy ocupada."],
    "wanted": ["Por que me mira asi? Nunca he estado en ningun lado. Nunca."],
    "banned": ["Se que mi pais esta en problemas. Por favor, yo no hice nada."],
}
REACT_APPROVED = ["Gracias.", "Gloria a Vostrokia!", "Por fin.", "Que tenga buen dia.",
                  "Gracias, camarada. Saludos a su camara."]
REACT_DENIED = ["Esto es injusto!", "Volvere con los papeles correctos.", "Mi familia me espera...",
                "Bah.", "Pero... vine desde tan lejos.", "Quiero hablar con su supervisor."]

# ---------------------------------------------------------------------------
# Salida / colores
# ---------------------------------------------------------------------------
class Cfg:
    color = True
    fast = False


CODES = dict(reset="0", bold="1", dim="2", red="31", green="32", yellow="33", blue="34",
             magenta="35", cyan="36", gray="90", bred="91", byellow="93", white="97")
LEVEL_STYLE = {"TRACE": ("gray",), "DEBUG": ("cyan",), "INFO": ("green",),
               "WARN": ("yellow",), "ERROR": ("red",), "FATAL": ("bred", "bold")}


def c(text, *styles):
    if not Cfg.color or not styles:
        return text
    return "".join(f"\033[{CODES[s]}m" for s in styles) + text + "\033[0m"


def pause(lo=0.01, hi=0.06):
    if not Cfg.fast:
        time.sleep(random.uniform(lo, hi))


def ts():
    now = dt.datetime.now()
    return now.strftime("%H:%M:%S.") + f"{now.microsecond // 1000:03d}"


def wrap(text, width):
    """Corta el texto en lineas de como maximo `width` caracteres."""
    return textwrap.wrap(text, width, break_on_hyphens=False) or [""]


def say(text, indent=2, style=None):
    """print() con salto de linea a LINE_WIDTH; las lineas de continuacion conservan la sangria."""
    lead = len(text) - len(text.lstrip(" "))
    pad = " " * (indent + lead)
    for ln in wrap(text.strip(" "), LINE_WIDTH - len(pad)):
        print(pad + (c(ln, *style) if style else ln))


def log(level, comp, msg, style=None):
    """Linea de log. Si el mensaje no cabe en LINE_WIDTH se parte y se alinea bajo la columna del mensaje."""
    comp_txt = f"[{comp}]".ljust(18)
    prefix = f"{c(ts(), 'gray')} {c(level.ljust(5), *LEVEL_STYLE[level])} {c(comp_txt, 'blue')} "
    indent = len(ts()) + 1 + 5 + 1 + len(comp_txt) + 1
    # Mensajes con colores incrustados se dejan intactos (son cortos y el ANCHO visible no coincide).
    lines = [msg] if "\033" in msg else wrap(msg, LINE_WIDTH - indent)
    for i, ln in enumerate(lines):
        ln = c(ln, *style) if style else ln
        print((prefix if i == 0 else " " * indent) + ln)
    pause()


NOISE = [
    ("INFO", "http.access", lambda: f"GET /api/v2/health 200 {random.randint(1, 9)}ms"),
    ("DEBUG", "jvm.gc", lambda: f"G1 Young pause {random.uniform(1, 9):.1f}ms heap={random.randint(180, 420)}MB"),
    ("TRACE", "kafka.consumer", lambda: f"commit partition={random.randint(0, 7)} offset={random.randint(10000, 99999)}"),
    ("INFO", "cache.redis", lambda: f"hit_ratio={random.uniform(0.85, 0.99):.2f} keys={random.randint(1000, 9000)}"),
    ("DEBUG", "db.pool", lambda: f"active={random.randint(1, 12)} idle={random.randint(0, 8)} waiting=0"),
    ("INFO", "http.access", lambda: f"POST /api/v2/ingress/events 202 {random.randint(4, 40)}ms"),
    ("TRACE", "scheduler", lambda: "heartbeat ok"),
    ("DEBUG", "metrics", lambda: f"flush series={random.randint(200, 900)} dur={random.randint(2, 30)}ms"),
    ("TRACE", "net.tls", lambda: f"session resumed peer=10.4.{random.randint(0, 255)}.{random.randint(1, 254)}"),
]


def noise(n=1):
    for _ in range(n):
        lvl, comp, fn = random.choice(NOISE)
        log(lvl, comp, fn())


def clear():
    os.system("cls" if WINDOWS else "clear")


def shell_path(cwd=()):
    if WINDOWS:
        return "C:\\dev\\ingress-svc" + "".join("\\" + p for p in cwd)
    return "~/ingress-svc" + "".join("/" + p for p in cwd)


def prompt_str(cwd=()):
    return f"PS {shell_path(cwd)}> " if WINDOWS else f"dev@ws-07:{shell_path(cwd)}$ "


def ask(text):
    try:
        return input(text)
    except EOFError:
        raise KeyboardInterrupt


def hhmm(minutes):
    m = int(minutes)
    return f"{m // 60:02d}:{m % 60:02d}"


# ---------------------------------------------------------------------------
# Emblema
# ---------------------------------------------------------------------------
# Aguila heraldica de perfil, en pleno vuelo: mira a la izquierda, alas desplegadas y garras al frente.
EAGLE = r"""
                                                                         ,
                                                                    _.-'/|
                                                               _.-'/// / |
                                                          _.-'//////  /  /
                                                     _.-'/////////   /  /
                                                _.-'////////////    /  /|
                                           _.-'///////////////     /  / |
                                      _.-'//////////////////      /  /  /
                                 _.-'/////////////////////       /  /  /
               ______       _.-'////////////////////////        /  /  /
           _.-'  ___ '-._.-'///////////////////////////        /  /  /
         .'    _(@)=-   \//////////////////////////////       /  /  /
      __/                \#############################.     /  /  /
     /__  ._              \################################._/  /  /
      \/   '--.__          '#########################################.___
                 '--.__     #############################################===---
                       '--. '#########################################////'''
                           \ '\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
                          /|\  '\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\.
                         //|\\   '\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\.
                                   '\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\.
                                     '\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\.
                                       '\\\\\\\\\\\\\  '\\\\\\\\\\\  '\\\\\\\\\\\.
"""


def eagle_lines():
    lines = EAGLE.strip("\n").split("\n")
    width = max(len(ln) for ln in lines)
    return [ln.ljust(width) for ln in lines]


def show_emblem():
    clear()
    width = len(eagle_lines()[0])
    print()
    for line in eagle_lines():
        print("  " + c(line, "red", "bold"))
        pause(0.03, 0.07)
    print()
    for text, style in [("*  *  *   GLORIA A VOSTROKIA   *  *  *", ("byellow", "bold")),
                        ("MINISTERIO DE ADMISION  -  PUESTO REMOTO WS-07", ("yellow",)),
                        (f"ingress-monitor v{VERSION}  (c) 1984 Directorio de Sistemas", ("gray",))]:
        print("  " + c(text.center(width), *style))
        pause(0.1, 0.2)
    print()
    boot = ["Mounted /mnt/ministerio", "Started ministry-vpn.service", "Reached target network-online",
            "Started ingress-monitor.service", "Loaded policy bundle (signed)", "Connected to border gateway WS-07"]
    for b in boot:
        print(f"[{c('  OK  ', 'green')}] {b}")
        pause(0.08, 0.25)
    print()


# ---------------------------------------------------------------------------
# Solicitantes
# ---------------------------------------------------------------------------
def rule(day, key):
    return day >= RULE_DAY[key]


def rand_person(sex=None):
    sex = sex or random.choice("MF")
    first = random.choice(FIRST_M if sex == "M" else FIRST_F)
    return f"{random.choice(LAST)}, {first}", sex


def make_pid(nation):
    code = NAT_CODE.get(nation, nation[:2].upper())
    return f"{code}-{random.randint(0, 0xFFFF):04X}-{random.randint(10, 99)}"


def future(today):
    return today + dt.timedelta(days=random.randint(3, 700))


def past(today):
    return today - dt.timedelta(days=random.randint(1, 60))


def mutate_name(name):
    last, first = name.split(", ")
    if random.random() < 0.5:
        i = random.randrange(1, len(last))
        last = last[:i] + random.choice([x for x in "AEIOUKLMNRSTVZ" if x != last[i]]) + last[i + 1:]
    else:
        pool = FIRST_M if first in FIRST_M else FIRST_F
        first = random.choice([f for f in pool if f != first])
    return f"{last}, {first}"


def mutate_pid(pid):
    chars = list(pid)
    i = random.choice([3, 4, 5, 6, 8, 9])
    pool = "0123456789" if i >= 8 else "0123456789ABCDEF"
    chars[i] = random.choice([x for x in pool if x != chars[i]])
    return "".join(chars)


class DayCtx:
    def __init__(self, day):
        self.day = day
        self.date = START_DATE + dt.timedelta(days=day - 1)
        self.banned = "Drovnia" if rule(day, "banned") else None
        self.wanted = [rand_person() for _ in range(3)] if rule(day, "wanted") else []


class Entrant:
    def __init__(self):
        self.sid = f"{random.randint(0, 0xFFFFFF):06x}"
        self.name = ""
        self.sex = "M"
        self.docs = {}
        self.scan_weight = None
        self.extra = []
        self.jorji = None
        self.bribe = 0
        self.flaw = None   # tipo de error inyectado (para que el dialogo pueda dar pistas)
        self.says = None   # lo que dice al llegar


def pick_dialogue(e):
    """Elige (o no) algo que el solicitante dice al llegar."""
    roll = random.random()
    if e.flaw in FLAW_LINES and roll < 0.35:
        return random.choice(FLAW_LINES[e.flaw])
    if roll < 0.45:
        return None
    p = e.docs.get("passport", {})
    pm = e.docs.get("permit")
    pools = [GREETINGS, SMALLTALK]
    if p.get("nation") == HOME:
        pools.append(HOME_LINES)
    if pm:
        pools.append(PURPOSE_LINES[pm["purpose"]])
    return random.choice(random.choice(pools))


def flaw_chance(day):
    return min(0.35 + 0.03 * day, 0.65)


def gen_entrant(ctx, force_valid=False, person=None, nation=None):
    day, today = ctx.day, ctx.date
    e = Entrant()
    e.name, e.sex = person or rand_person()
    while person is None and any(e.name == w[0] for w in ctx.wanted):
        e.name, e.sex = rand_person()
    if nation is None:
        home_p = 0.75 if day == 1 else 0.4
        pool = [n for n in FOREIGN if not (force_valid and n == ctx.banned)]
        nation = HOME if random.random() < home_p else random.choice(pool)
        if nation == ctx.banned and random.random() < 0.5:
            nation = random.choice([n for n in FOREIGN if n != ctx.banned])
    if force_valid and day == 1:
        nation = HOME
    dob = today - dt.timedelta(days=random.randint(18 * 365, 70 * 365))
    weight = random.randint(48, 110)
    pid = make_pid(nation)
    e.docs["passport"] = dict(name=e.name, sex=e.sex, dob=dob, nation=nation,
                              city=random.choice(NATIONS[nation]), pid=pid, exp=future(today))
    e.scan_weight = weight + random.randint(-1, 1)
    foreign = nation != HOME
    if foreign and rule(day, "foreigners"):
        purpose = random.choice(PURPOSES)
        e.docs["permit"] = dict(name=e.name, pid=pid, purpose=purpose, dur=random.choice(DURATIONS[purpose]),
                                exp=future(today), weight=weight, seal=random.choice(VALID_SEALS))
        if purpose == "WORK" and rule(day, "workpass"):
            e.docs["workpass"] = dict(name=e.name, field=random.choice(FIELDS), exp=future(today))
    if foreign and rule(day, "vaccine"):
        vax = ["POLIO"] + random.sample(VACCINES, k=random.randint(1, 2))
        random.shuffle(vax)
        e.docs["vaccine"] = dict(name=e.name, pid=pid, vax=vax)
    if not force_valid and random.random() < flaw_chance(day):
        inject_flaw(e, ctx)
    e.says = pick_dialogue(e)
    return e


def inject_flaw(e, ctx):
    day, today = ctx.day, ctx.date
    p = e.docs["passport"]
    opts = ["pass_expired"]
    if rule(day, "city"):
        opts.append("city")
    if rule(day, "wanted"):
        opts += ["wanted", "banned"]
    if "permit" in e.docs:
        opts += ["permit_missing", "permit_name", "permit_id", "permit_expired"]
        if rule(day, "weight"):
            opts += ["weight", "weight"]
        if rule(day, "seal"):
            opts += ["seal", "seal"]
    if "workpass" in e.docs:
        opts += ["wp_missing", "wp_name", "wp_expired"]
    if "vaccine" in e.docs:
        opts += ["vax_missing", "vax_nopolio", "vax_id", "vax_name"]
    kind = random.choice(opts)

    if kind == "pass_expired":
        p["exp"] = past(today)
    elif kind == "city":
        others = [ct for n, cs in NATIONS.items() if n != p["nation"] for ct in cs]
        p["city"] = random.choice(others + FAKE_CITIES)
    elif kind == "wanted":
        new = gen_entrant(ctx, force_valid=True, person=random.choice(ctx.wanted))
        e.__dict__.update(new.__dict__)
    elif kind == "banned":
        new = gen_entrant(ctx, force_valid=True, nation=ctx.banned)
        e.__dict__.update(new.__dict__)
    elif kind == "permit_missing":
        del e.docs["permit"]
        e.docs.pop("workpass", None)
    elif kind == "permit_name":
        e.docs["permit"]["name"] = mutate_name(e.name)
    elif kind == "permit_id":
        e.docs["permit"]["pid"] = mutate_pid(p["pid"])
    elif kind == "permit_expired":
        e.docs["permit"]["exp"] = past(today)
    elif kind == "weight":
        e.scan_weight = e.docs["permit"]["weight"] + random.choice([-1, 1]) * random.randint(5, 14)
    elif kind == "seal":
        e.docs["permit"]["seal"] = f"MX-{random.randint(1000, 9999)}"
        if e.docs["permit"]["seal"] in VALID_SEALS:
            e.docs["permit"]["seal"] = "MX-0013"
    elif kind == "wp_missing":
        del e.docs["workpass"]
    elif kind == "wp_name":
        e.docs["workpass"]["name"] = mutate_name(e.name)
    elif kind == "wp_expired":
        e.docs["workpass"]["exp"] = past(today)
    elif kind == "vax_missing":
        del e.docs["vaccine"]
    elif kind == "vax_nopolio":
        e.docs["vaccine"]["vax"] = random.sample(VACCINES, k=random.randint(1, 3))
    elif kind == "vax_id":
        e.docs["vaccine"]["pid"] = mutate_pid(p["pid"])
    elif kind == "vax_name":
        e.docs["vaccine"]["name"] = mutate_name(e.name)
    e.flaw = kind


def check(e, ctx):
    """Devuelve el conjunto de motivos de rechazo (vacio = solicitante valido)."""
    day, today = ctx.day, ctx.date
    r = set()
    p = e.docs.get("passport")
    if not p:
        return {"missing"}
    if p["exp"] < today:
        r.add("expired")
    if p["nation"] not in NATIONS:
        r.add("nation")
    elif rule(day, "city") and p["city"] not in NATIONS[p["nation"]]:
        r.add("city")
    foreign = p["nation"] != HOME
    if foreign and not rule(day, "foreigners"):
        r.add("nation")
    if foreign and ctx.banned and p["nation"] == ctx.banned:
        r.add("nation")
    if any(p["name"] == w[0] for w in ctx.wanted):
        r.add("wanted")
    if foreign and rule(day, "foreigners"):
        pm = e.docs.get("permit")
        if not pm:
            r.add("missing")
        else:
            if pm["name"] != p["name"]:
                r.add("name")
            if pm["pid"] != p["pid"]:
                r.add("id")
            if pm["exp"] < today:
                r.add("expired")
            if rule(day, "weight") and e.scan_weight is not None and abs(pm["weight"] - e.scan_weight) > 2:
                r.add("weight")
            if rule(day, "seal") and pm["seal"] not in VALID_SEALS:
                r.add("seal")
            if rule(day, "workpass") and pm["purpose"] == "WORK":
                wp = e.docs.get("workpass")
                if not wp:
                    r.add("missing")
                else:
                    if wp["name"] != p["name"]:
                        r.add("name")
                    if wp["exp"] < today:
                        r.add("expired")
        if rule(day, "vaccine"):
            vc = e.docs.get("vaccine")
            if not vc:
                r.add("missing")
            else:
                if vc["name"] != p["name"]:
                    r.add("name")
                if vc["pid"] != p["pid"]:
                    r.add("id")
                if "POLIO" not in vc["vax"]:
                    r.add("vaccine")
    return r


# ---------------------------------------------------------------------------
# Jorji Costava
# ---------------------------------------------------------------------------
JORJI = ("COSTAVA, Jorji", "M")
JORJI_DAYS = {1: "nodocs", 3: "cobrastan", 5: "crayon", 7: "legal", 9: "gift"}
JORJI_REPLY = {
    "nodocs": ("Gracias amigo! Jorji sabia que eras buena persona. Muy mala idea, pero buena persona.",
               "Esta bien, esta bien. Jorji vuelve pronto. Con papeles. Papeles muy buenos."),
    "cobrastan": ("Ja! Cobrastan es pais real. Muy real. Gracias por creer, amigo.",
                  "Cobrastan no existe? Pero Jorji estuvo ahi! ...en sueno. Volvere."),
    "crayon": ("Te dije que era oficial! Crayon de la mejor calidad.",
               "Que tiene de malo Jorjigrad? Hermosa ciudad. Poblacion: Jorji."),
    "legal": ("Jorji Costava ahora es visitante legal! Gran dia para Jorji! Gran dia para Vostrokia!",
              "Pero... pero todo estaba bien esta vez! Jorji hizo fila! Esto es injusticia, amigo."),
    "gift": ("Regalo para amigo. Jorji no olvida a los amigos. Nos vemos, amigo.",
             "No quieres regalo? Bueno. Jorji guarda regalo. Para otro amigo."),
}


def jorji_entrant(ctx):
    kind = JORJI_DAYS[ctx.day]
    today = ctx.date
    if kind in ("legal", "gift"):
        e = gen_entrant(ctx, force_valid=True, person=JORJI,
                        nation=random.choice([n for n in FOREIGN if n != ctx.banned]))
    else:
        e = Entrant()
        e.name, e.sex = JORJI
    e.jorji = kind
    if kind == "nodocs":
        e.says = "Hola, amigo! No traigo papeles, pero traigo buena voluntad. Sin problemas. Solo dejame pasar."
    elif kind == "cobrastan":
        pid = "CB-J0RJ-01"
        e.docs["passport"] = dict(name=e.name, sex="M", dob=dt.date(1947, 6, 1), nation="Cobrastan",
                                  city="Cobragrad", pid=pid, exp=future(today))
        e.extra = [("ERROR", "registry.lookup", "nation='Cobrastan' not found in registry (did you mean: nothing?)")]
        e.says = "Ahora tengo pasaporte! Hecho por las mejores manos de Cobrastan. Las mias."
    elif kind == "crayon":
        e.docs["passport"] = dict(name=e.name, sex="M", dob=dt.date(1947, 6, 1), nation=HOME,
                                  city="Jorjigrad", pid="VK-J0RJ-11", exp=future(today))
        e.extra = [("WARN", "ocr.engine", f"sid={e.sid} ink_type=CRAYON confidence=0.12 smell=strawberry")]
        e.says = "Pasaporte de Vostrokia. Muy oficial. Por favor no mires la ciudad."
    elif kind == "legal":
        e.says = "Esta vez todo legal! Jorji fue a oficina. Hizo fila. Fila muy larga. Mucho sufrimiento. Verifica, amigo!"
    elif kind == "gift":
        e.bribe = 15
        e.extra = [("INFO", "payment.gateway", 'pending transfer amount=15cr from=jcostava '
                                               'memo="para mi amigo, por ser amigo" (se acredita si approve)')]
        e.says = "Documentos en orden. Tambien regalo. Regalo no es soborno si se dice regalo."
    return e


# ---------------------------------------------------------------------------
# Documentos como carpetas navegables (./docs/<documento>)
# ---------------------------------------------------------------------------
DOC_DIR = {"passport": "passport", "permit": "entry_permit", "workpass": "work_pass", "vaccine": "vax_cert"}
DOC_ALIASES = {
    "passport": "passport", "pasaporte": "passport",
    "entry_permit": "entry_permit", "permit": "entry_permit", "permiso": "entry_permit",
    "work_pass": "work_pass", "workpass": "work_pass", "trabajo": "work_pass",
    "vax_cert": "vax_cert", "vaxcert": "vax_cert", "vaccine": "vax_cert", "vacuna": "vax_cert",
    "biometrics": "biometrics", "scale": "biometrics", "bascula": "biometrics",
}
FAKE_FILES = ["README.md", "pyproject.toml", "src/", "tests/", "docker-compose.yml"]


def doc_dirs(e):
    """Carpetas presentes en ./docs para este solicitante, en orden."""
    dirs = [DOC_DIR[k] for k in e.docs]
    p = e.docs.get("passport")
    if p and p["nation"] != HOME and e.scan_weight is not None:
        dirs.append("biometrics")
    return dirs


def doc_fields(e, dirname):
    rev = {v: k for k, v in DOC_DIR.items()}
    if dirname == "biometrics":
        return [("device", "SCALE-07B"), ("weight", f"{e.scan_weight} kg")]
    d = e.docs[rev[dirname]]
    if dirname == "passport":
        return [("name", d["name"]), ("sex", d["sex"]), ("dob", d["dob"]), ("nation", d["nation"]),
                ("issuer_city", d["city"]), ("pid", d["pid"]), ("exp", d["exp"])]
    if dirname == "entry_permit":
        return [("holder", d["name"]), ("pid_ref", d["pid"]), ("purpose", d["purpose"]),
                ("duration", d["dur"]), ("exp", d["exp"]), ("weight", f"{d['weight']} kg"), ("seal", d["seal"])]
    if dirname == "work_pass":
        return [("holder", d["name"]), ("field", d["field"]), ("exp", d["exp"])]
    return [("holder", d["name"]), ("pid_ref", d["pid"]), ("vaccines", ", ".join(d["vax"]))]


def show_doc(e, dirname):
    print(c(f"# docs/{dirname}/{dirname}.yaml   sid={e.sid}", "gray"))
    for key, value in doc_fields(e, dirname):
        print(f"  {c(key.ljust(12), 'cyan')}: {value}")


def show_listing(e, cwd):
    if not cwd:
        entries = [c("docs/", "blue", "bold")] + FAKE_FILES
    elif len(cwd) == 1:
        entries = [c(d + "/", "blue", "bold") for d in doc_dirs(e)]
    else:
        show_doc(e, cwd[1])
        return
    print("  ".join(entries) if entries else c("(vacio)", "gray"))


def resolve_doc(e, name):
    """Nombre de carpeta de documento a partir de lo que escribio el jugador (acepta alias y prefijos)."""
    name = name.lower()
    if name.endswith(".yaml"):
        name = name[:-5]
    if name in DOC_ALIASES:
        return DOC_ALIASES[name]
    matches = {d for alias, d in DOC_ALIASES.items() if alias.startswith(name)}
    return matches.pop() if len(matches) == 1 else None


def resolve_path(e, cwd, arg):
    """Devuelve la ruta destino (lista) o None si no existe."""
    arg = (arg or "").strip().strip('"').replace("\\", "/")
    if arg in ("", "~", "/"):
        return []
    path = list(cwd)
    for part in [p for p in arg.split("/") if p]:
        if part == ".":
            continue
        if part == "..":
            path = path[:-1]
        elif part.lower() == "docs" and not path:
            path = ["docs"]
        else:
            doc = resolve_doc(e, part)
            if doc is None or doc not in doc_dirs(e) or len(path) > 2:
                return None
            path = ["docs", doc]   # permite "cd passport" desde cualquier lugar
    return path


def path_error(cmd, cwd, arg):
    if WINDOWS:
        target = shell_path(cwd) + "\\" + arg.replace("/", "\\")
        say(f"{cmd} : Cannot find path '{target}' because it does not exist.", indent=0, style=("red",))
    else:
        print(f"bash: {cmd}: {arg}: No such file or directory")


def render(e, ctx, clock):
    """Llegada de un solicitante: solo el resumen; los documentos se revisan en ./docs."""
    log("INFO", "ingress.gateway", f"session opened sid={e.sid} booth=WS-07 ref_ts={ctx.date}T{hhmm(clock)}")
    noise(random.randint(0, 2))
    dirs = doc_dirs(e)
    log("DEBUG", "doc.manifest", f"sid={e.sid} mounted {len(dirs)} docs at ./docs: {', '.join(dirs) or '-'}")
    if e.says:
        log("INFO", "chat.relay", f'{e.name}: "{e.says}"', style=("magenta",) if e.jorji else ("white",))
    for ln in e.extra:
        log(*ln)
    log("INFO", "ingress.gateway", f"sid={e.sid} state=PENDING_REVIEW")


# ---------------------------------------------------------------------------
# Estado del jugador
# ---------------------------------------------------------------------------
def new_state():
    return dict(day=1, credits=0, total_ok=0, total_bad=0,
                family=[dict(name=n, hunger=0, cold=0, sick=False, sick_days=0, alive=True)
                        for n in ("ESPOSA", "HIJO", "SUEGRA", "TIO")])


def save(st):
    try:
        SAVE_PATH.write_text(json.dumps(st), encoding="utf-8")
    except OSError:
        pass


def load():
    try:
        return json.loads(SAVE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def delete_save():
    try:
        SAVE_PATH.unlink()
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Comandos auxiliares
# ---------------------------------------------------------------------------
def print_help():
    print(c("usage: ingress-svc <command> [args]", "white"))
    rows = [
        ("cd docs", "entrar a la carpeta de documentos del solicitante"),
        ("cd <documento>", "abrir un documento (passport, entry_permit, ...)"),
        ("cd .. | cd ~", "subir un nivel | volver a la raiz"),
        ("ls | dir", "listar la carpeta actual (o mostrar el documento)"),
        ("cat <documento>", "mostrar un documento sin entrar a el"),
        ("approve | a", "aprobar al solicitante actual"),
        ("deny | d [motivo]", "denegar (motivo correcto = bono)"),
        ("rules | r", "ver politica vigente (ciudades, sellos, buscados...)"),
        ("logs | l", "volver a mostrar la llegada del solicitante"),
        ("status | s", "creditos, citaciones, hora del turno"),
        ("boss | b", "PANICO: limpia pantalla y muestra un build falso"),
        ("clear | cls", "limpiar pantalla"),
        ("quit | exit", "guardar y salir"),
    ]
    for cmd, desc in rows:
        print(f"  {cmd.ljust(20)} {c(desc, 'gray')}")
    say("motivos: " + ", ".join(REASONS), indent=0, style=("gray",))


def print_rules(ctx):
    day = ctx.day
    L = []
    L.append(f"# policy.yaml  (ref_date: {ctx.date}, rev: {day})")
    L.append("admission:")
    L.append(f"  home_nation: {HOME}")
    L.append(f"  foreigners: {'allowed  # requires entry_permit' if rule(day, 'foreigners') else 'DENIED'}")
    L.append("  check_expiry: [passport" + (", entry_permit" if rule(day, "foreigners") else "")
             + (", work_pass" if rule(day, "workpass") else "") + "]")
    if rule(day, "foreigners"):
        L.append("  permit_must_match_passport: [holder, pid_ref]")
    if rule(day, "workpass"):
        L.append("  purpose_WORK_requires: work_pass  # holder == passport.name")
    if rule(day, "weight"):
        L.append("  scale_tolerance_kg: 2  # permit.wt vs biometrics.scale")
    if rule(day, "vaccine"):
        L.append("  foreigners_require: vax_cert  # must include POLIO; holder/pid_ref must match")
    if ctx.banned:
        L.append(f"  banned_nations: [{ctx.banned}]")
    if rule(day, "seal"):
        L.append(f"  valid_seals: [{', '.join(VALID_SEALS)}]")
    if ctx.wanted:
        L.append("  wanted:")
        for name, _ in ctx.wanted:
            L.append(f'    - "{name}"')
    if rule(day, "city"):
        L.append("issuer_cities:")
        for n, cities in NATIONS.items():
            L.append(f"  {n}: [{', '.join(cities)}]")
    L.append("deny_reasons: [" + ", ".join(REASONS) + "]")
    for ln in L:
        say(ln, indent=0, style=("yellow",) if ln.startswith("#") else None)


def boss_mode():
    clear()
    print(prompt_str() + "python -m pytest tests/ -q")
    time.sleep(0.4)
    print(c("============================= test session starts =============================", "bold"))
    print(f"platform {sys.platform} -- Python {sys.version.split()[0]}, pytest-8.3.4, pluggy-1.5.0")
    print("rootdir: C:\\dev\\ingress-svc" if WINDOWS else "rootdir: /home/dev/ingress-svc")
    print("collected 214 items\n")
    files = ["tests/test_gateway.py", "tests/test_parsers.py", "tests/test_policy.py",
             "tests/test_scheduler.py", "tests/test_metrics.py"]
    pct = 0
    for f in files:
        n = random.randint(30, 45)
        pct = min(100, pct + random.randint(18, 24)) if f != files[-1] else 100
        dots = ""
        for _ in range(n):
            dots += "."
            if not Cfg.fast:
                time.sleep(0.01)
        print(f"{f} {c(dots, 'green')} [{pct:3d}%]")
    print(c(f" 214 passed in {random.uniform(9, 16):.2f}s ".center(79, "="), "green"))


def fake_shell(cmd):
    """Respuestas creibles para comandos comunes, para no romper el disfraz."""
    base = cmd.split()[0].lower()
    if cmd.startswith("git status"):
        print("On branch main\nYour branch is up to date with 'origin/main'.\n\nnothing to commit, working tree clean")
    elif cmd.startswith("git"):
        print(c("Already up to date.", "gray"))
    elif WINDOWS:
        say(f"{base} : The term '{base}' is not recognized as the name of a cmdlet, function, "
            f"script file, or operable program.", indent=0, style=("red",))
    else:
        print(f"bash: {base}: command not found")


# ---------------------------------------------------------------------------
# Mensajes ambientales
# ---------------------------------------------------------------------------
def ambient_message():
    roll = random.random()
    if roll < 0.10:
        log("INFO", "chat.relay", f"msg from @jcostava: {random.choice(JORJI_CHAT)}", style=("magenta",))
    elif roll < 0.17:
        user, text = random.choice(COWORKER_MSGS)
        log("INFO", "chat.relay", f"msg from @{user}: {text}", style=("cyan",))
    elif roll < 0.21:
        log("INFO", "mail.daemon", f"new message from=familia: \"{random.choice(FAMILY_MSGS)}\"")
    elif roll < 0.25:
        log("WARN", "ministry.notice", random.choice(MINISTRY_MSGS))


# ---------------------------------------------------------------------------
# Decisiones
# ---------------------------------------------------------------------------
class Shift:
    def __init__(self):
        self.ok = 0
        self.bad = 0
        self.earned = 0
        self.fines = 0


def decide(action, reason, e, ctx, st, shift):
    truth = check(e, ctx)
    valid = not truth
    correct = valid if action == "approve" else not valid
    verdict = "APPROVED" if action == "approve" else "DENIED"
    log("INFO", "ingress.gateway", f"sid={e.sid} decision={verdict}" + (f" reason={reason}" if reason else ""))
    if correct:
        shift.ok += 1
        st["total_ok"] += 1
        pay = SALARY
        if action == "deny" and reason in truth:
            pay += REASON_BONUS
            log("DEBUG", "payroll", f"reason match bonus=+{REASON_BONUS}cr")
        shift.earned += pay
        st["credits"] += pay
        log("INFO", "payroll", f"sid={e.sid} processed ok credit=+{pay}cr")
    else:
        shift.bad += 1
        st["total_bad"] += 1
        if valid:
            detail = "el solicitante cumplia todos los requisitos"
        else:
            detail = "; ".join(REASONS[r] for r in sorted(truth))
        log("WARN", "audit.ministry", f"CITATION #{shift.bad} sid={e.sid} :: {detail}", style=("yellow",))
        if shift.bad > 2:
            shift.fines += CITATION_FINE
            st["credits"] -= CITATION_FINE
            log("WARN", "payroll", f"citation penalty=-{CITATION_FINE}cr")
        else:
            log("DEBUG", "audit.ministry", f"warning {shift.bad}/2 issued (sin multa)")
    if not e.jorji and random.random() < 0.35:
        reply = random.choice(REACT_APPROVED if action == "approve" else REACT_DENIED)
        log("INFO", "chat.relay", f'{e.name}: "{reply}"', style=("white",))
    if e.jorji:
        approve_msg, deny_msg = JORJI_REPLY[e.jorji]
        log("INFO", "chat.relay", f"msg from @jcostava: {approve_msg if action == 'approve' else deny_msg}",
            style=("magenta",))
        if action == "approve" and e.bribe:
            st["credits"] += e.bribe
            shift.earned += e.bribe
            log("INFO", "payment.gateway", f"transfer settled amount=+{e.bribe}cr from=jcostava")
    noise(random.randint(0, 2))


# ---------------------------------------------------------------------------
# Dia
# ---------------------------------------------------------------------------
def day_intro(ctx, st):
    log("INFO", "systemd", "Started ingress-monitor shift session")
    log("INFO", "scheduler", f"shift start ref_date={ctx.date} day={ctx.day}/{LAST_DAY} window=06:00-18:00")
    noise(2)
    if ctx.day == 1:
        for m in MINISTRY_INTRO:
            log("INFO", "ministry.mail", m)
    for news in POLICY_NEWS.get(ctx.day, []):
        log("WARN", "policy.update", news, style=("yellow",))
    if ctx.wanted:
        log("WARN", "policy.update", "wanted_list=[" + "; ".join(n for n, _ in ctx.wanted) + "]")
    sick = [m["name"] for m in st["family"] if m["alive"] and m["sick"]]
    if sick:
        log("WARN", "mail.daemon", f"new message from=familia: \"{', '.join(sick)} sigue(n) enfermo(s). "
                                   f"Necesitamos medicina.\"")
    log("DEBUG", "cli", "escribe 'help' para ver comandos, 'rules' para la politica vigente")
    log("DEBUG", "cli", "los documentos de cada solicitante se montan en ./docs "
                        "(cd docs, ls, cd passport, cd ..)")
    noise(1)


def play_day(st):
    ctx = DayCtx(st["day"])
    shift = Shift()
    day_intro(ctx, st)
    clock = float(SHIFT_START)
    n = 0
    jorji_pos = random.randint(2, 4) if ctx.day in JORJI_DAYS else None
    while clock < SHIFT_END:
        ambient_message()
        n += 1
        e = jorji_entrant(ctx) if n == jorji_pos else gen_entrant(ctx)
        render(e, ctx, clock)
        cwd = []
        t_last = time.monotonic()
        while True:
            raw = ask(prompt_str(cwd)).strip()
            now = time.monotonic()
            clock += min(now - t_last, MAX_IDLE) * REAL_TO_GAME
            t_last = now
            if not raw:
                continue
            parts = raw.split()
            cmd = parts[0].lower()
            arg = parts[1].lower() if len(parts) > 1 else None
            # "cd.." y "cd\" (sin espacio) tambien funcionan en Windows
            if cmd.startswith("cd") and len(cmd) > 2 and cmd[2] in "./\\":
                cmd, arg = "cd", cmd[2:]
            if cmd in ("cd", "set-location", "chdir"):
                target = resolve_path(e, cwd, arg)
                if target is None:
                    path_error("Set-Location" if WINDOWS else "cd", cwd, arg)
                elif target != cwd:
                    cwd = target
                    if cwd:
                        show_listing(e, cwd)
                continue
            if cmd in ("ls", "dir", "ll", "get-childitem"):
                target = resolve_path(e, cwd, arg) if arg else cwd
                if target is None:
                    path_error("Get-ChildItem" if WINDOWS else "ls", cwd, arg)
                else:
                    show_listing(e, target)
                continue
            if cmd in ("cat", "type", "more", "less", "get-content"):
                target = resolve_path(e, cwd, arg) if arg else cwd
                if target is None:
                    path_error("Get-Content" if WINDOWS else "cat", cwd, arg or "")
                elif len(target) == 2:
                    show_doc(e, target[1])
                else:
                    say(f"{cmd}: {arg or '.'}: Is a directory", indent=0, style=("red",))
                continue
            if cmd == "pwd":
                print(shell_path(cwd))
                continue
            if cmd in ("approve", "a", "ok"):
                decide("approve", None, e, ctx, st, shift)
                break
            if cmd in ("deny", "d", "reject"):
                if arg and arg not in REASONS:
                    print(c(f"error: motivo desconocido '{arg}'. validos: {', '.join(REASONS)}", "red"))
                    continue
                decide("deny", arg, e, ctx, st, shift)
                break
            if cmd in ("rules", "r"):
                print_rules(ctx)
            elif cmd in ("logs", "l"):
                render(e, ctx, clock)
            elif cmd in ("status", "s"):
                log("INFO", "status", f"ref_ts={ctx.date}T{hhmm(clock)} credits={st['credits']}cr "
                                      f"processed={shift.ok + shift.bad} citations={shift.bad}")
            elif cmd in ("help", "h", "?"):
                print_help()
            elif cmd in ("boss", "b"):
                boss_mode()
            elif cmd in ("clear", "cls"):
                clear()
            elif cmd in ("quit", "exit", "q"):
                raise KeyboardInterrupt
            else:
                fake_shell(raw)
        clock += random.randint(12, 25)
    log("INFO", "scheduler", f"shift window closed at {hhmm(SHIFT_END)} - booth WS-07 offline")
    return ctx, shift


def yes_no(text, default=True):
    suffix = "[Y/n]" if default else "[y/N]"
    ans = ask(f"  ? {text} {suffix}: ").strip().lower()
    return default if not ans else ans.startswith(("y", "s"))


def end_of_day(st, ctx, shift):
    print()
    log("INFO", "payroll", f"shift summary processed={shift.ok + shift.bad} ok={shift.ok} "
                           f"citations={shift.bad} earned={shift.earned}cr fines={shift.fines}cr")
    log("INFO", "billing.cron", f"balance={st['credits']}cr")
    st["credits"] -= RENT
    log("INFO", "billing.cron", f"invoice RENT amount={RENT}cr status=AUTO_DEBIT balance={st['credits']}cr")
    if st["credits"] < 0:
        return "evicted"

    alive = [m for m in st["family"] if m["alive"]]
    fed = heat = False
    if alive:
        if st["credits"] >= FOOD:
            fed = yes_no(f"pay invoice FOOD ({FOOD}cr, balance {st['credits']}cr)")
            if fed:
                st["credits"] -= FOOD
        else:
            log("WARN", "billing.cron", "insufficient funds for FOOD")
        if st["credits"] >= HEAT:
            heat = yes_no(f"pay invoice HEAT ({HEAT}cr, balance {st['credits']}cr)")
            if heat:
                st["credits"] -= HEAT
        else:
            log("WARN", "billing.cron", "insufficient funds for HEAT")
    medicated = set()
    for m in alive:
        if m["sick"]:
            if st["credits"] >= MEDICINE and yes_no(f"pay invoice MEDICINE for {m['name']} "
                                                     f"({MEDICINE}cr, balance {st['credits']}cr)"):
                st["credits"] -= MEDICINE
                medicated.add(m["name"])
            elif st["credits"] < MEDICINE:
                log("WARN", "billing.cron", f"insufficient funds for MEDICINE ({m['name']})")

    for m in alive:
        m["hunger"] = 0 if fed else m["hunger"] + 1
        m["cold"] = 0 if heat else m["cold"] + 1
        if m["sick"]:
            if m["name"] in medicated:
                m["sick"], m["sick_days"] = False, 0
            else:
                m["sick_days"] += 1
                if m["sick_days"] >= 2:
                    m["alive"] = False
        else:
            risk = m["hunger"] + m["cold"]
            if m["hunger"] >= 2 or m["cold"] >= 2 or (risk >= 1 and random.random() < 0.25):
                m["sick"] = True
        if m["hunger"] >= 3:
            m["alive"] = False

    for m in st["family"]:
        if not m["alive"]:
            state = c("FALLECIDO", "red")
        else:
            flags = [f for f, on in (("HAMBRE", m["hunger"]), ("FRIO", m["cold"]), ("ENFERMO", m["sick"])) if on]
            state = c(" ".join(flags), "yellow") if flags else c("OK", "green")
        log("INFO", "family.monitor", f"{m['name'].ljust(6)} status={state}")
    log("INFO", "billing.cron", f"final balance={st['credits']}cr")
    if not any(m["alive"] for m in st["family"]):
        return "family"
    return None


def game_over(reason, st):
    print()
    if reason == "evicted":
        log("FATAL", "ministry.notice", "Deuda con el Estado. Su apartamento clase 8 ha sido confiscado.")
        log("FATAL", "ministry.notice", "Usted y su familia seran reubicados. Gloria a Vostrokia.")
    elif reason == "family":
        log("FATAL", "ministry.notice", "No quedan miembros registrados en su unidad familiar.")
        log("FATAL", "ministry.notice", "Su puesto ha sido reasignado. Gloria a Vostrokia.")
    log("INFO", "chat.relay", "msg from @jcostava: Amigo... Jorji lo siente mucho. Si necesitas algo, "
                              "Jorji conoce a alguien. Siempre conoce a alguien.", style=("magenta",))
    log("ERROR", "systemd", "ingress-monitor.service: Main process exited, code=exited, status=1/FAILURE")
    delete_save()


def victory(st):
    print()
    alive = [m["name"] for m in st["family"] if m["alive"]]
    log("INFO", "ministry.mail", "Su periodo de servicio remoto ha concluido.")
    log("INFO", "ministry.mail", f"Aciertos: {st['total_ok']}  Citaciones: {st['total_bad']}  "
                                 f"Saldo: {st['credits']}cr")
    if st["total_bad"] <= st["total_ok"] // 5:
        log("INFO", "ministry.mail", "Desempeno EJEMPLAR. Ha sido promovido a 'Supervisor Remoto Senior'. "
                                     "Ahora puede usar pantalones opcionales.")
    else:
        log("INFO", "ministry.mail", "Desempeno ACEPTABLE. Su contrato remoto se renueva. Nadie esta sorprendido.")
    log("INFO", "family.monitor", f"familia presente: [{', '.join(alive) or 'nadie'}]")
    log("INFO", "chat.relay", "msg from @jcostava: Amigo! Jorji abre restaurante en Grestavo. Primera comida "
                              "gratis para ti. Segunda tambien. Tercera... hablamos.", style=("magenta",))
    print()
    print("  " + c("*  *  *   GLORIA A VOSTROKIA   *  *  *", "byellow", "bold"))
    print()
    log("INFO", "systemd", "ingress-monitor.service: Succeeded.")
    delete_save()


# ---------------------------------------------------------------------------
# Menu inicial
# ---------------------------------------------------------------------------
def read_key():
    """Lee una tecla sin esperar Enter. Devuelve 'up', 'down', 'enter' o el caracter."""
    if WINDOWS:
        import msvcrt
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            return {"H": "up", "P": "down"}.get(msvcrt.getwch(), "")
    else:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                return {"[A": "up", "[B": "down"}.get(sys.stdin.read(2), "")
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    if ch in ("\r", "\n"):
        return "enter"
    if ch == "\x03":
        raise KeyboardInterrupt
    return ch.lower()


def select(title, options, default=0):
    """Lista elegible con flechas (o w/s, j/k, numeros) + Enter. Devuelve el indice elegido."""
    print(f"{c('?', 'green')} {c(title, 'bold')} {c('(flechas + Enter)', 'gray')}")
    if not sys.stdin.isatty():
        for i, opt in enumerate(options, 1):
            print(f"  {i}) {opt}")
        while True:
            ans = ask("  > ").strip()
            if ans.isdigit() and 1 <= int(ans) <= len(options):
                return int(ans) - 1

    idx = default

    def draw(first):
        if not first:
            sys.stdout.write(f"\033[{len(options)}A")
        for i, opt in enumerate(options):
            line = c(f"> {opt}", "cyan", "bold") if i == idx else f"  {opt}"
            sys.stdout.write(f"\r\033[K  {line}\n")
        sys.stdout.flush()

    sys.stdout.write("\033[?25l")  # oculta el cursor
    try:
        draw(True)
        while True:
            key = read_key()
            if key in ("up", "w", "k"):
                idx = (idx - 1) % len(options)
            elif key in ("down", "s", "j"):
                idx = (idx + 1) % len(options)
            elif key.isdigit() and 1 <= int(key) <= len(options):
                idx = int(key) - 1
            elif key == "enter":
                return idx
            draw(False)
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


def print_howto():
    print()
    print(c("# COMO JUGAR", "yellow"))
    for ln in [
        "Cada solicitante llega como unas lineas de log. Sus documentos se montan como carpetas en ./docs:",
        "  cd docs        ver que documentos trae (ls para listar)",
        "  cd passport    abrir un documento; cd .. para regresar",
        "Compara los campos contra la politica del dia (comando 'rules') y decide:",
        "  a              aprobar",
        "  d <motivo>     denegar; si aciertas el motivo ganas +2cr de bono",
        f"  motivos:       {', '.join(REASONS)}",
        "Cada dia hay reglas nuevas. Si te equivocas recibes una citacion (las 2 primeras son gratis).",
        "Al final del turno pagas renta, comida, calefaccion y medicina para tu familia.",
        "Si alguien se acerca: 'b' limpia la pantalla y muestra un build falso. Luego 'logs' para volver.",
        "Escribe 'help' durante el juego para ver todos los comandos.",
    ]:
        say(ln)
    print()


def main_menu(args):
    """Devuelve el estado con el que se juega, o None si el jugador sale."""
    if args.new:
        return new_state()
    while True:
        saved = load()
        options, actions = [], []
        if saved:
            options.append(f"Continuar partida   (dia {saved['day']}/{LAST_DAY}, {saved['credits']}cr)")
            actions.append("continue")
        options += ["Nueva partida", "Como jugar", "Salir"]
        actions += ["new", "howto", "quit"]
        action = actions[select("ingress-monitor :: seleccione sesion", options)]
        print()
        if action == "continue":
            log("INFO", "state", f"session restored day={saved['day']}/{LAST_DAY} credits={saved['credits']}cr")
            return saved
        if action == "new":
            if saved and select("Hay una partida guardada. Sobrescribirla?", ["No", "Si, empezar de cero"]) == 0:
                print()
                continue
            return new_state()
        if action == "howto":
            print_howto()
            continue
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="ingress-monitor :: WS-07")
    ap.add_argument("--version", action="version", version=f"ingress-monitor {VERSION}")
    ap.add_argument("--new", action="store_true", help="empezar partida nueva")
    ap.add_argument("--no-color", action="store_true", help="sin colores ANSI")
    ap.add_argument("--no-banner", action="store_true", help="no mostrar el emblema al iniciar")
    ap.add_argument("--stealth", action="store_true", help="sin colores ni emblema")
    ap.add_argument("--fast", action="store_true", help="logs sin animacion")
    args = ap.parse_args()

    if WINDOWS:
        os.system("")  # activa secuencias ANSI en la consola de Windows
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    Cfg.color = not (args.no_color or args.stealth) and sys.stdout.isatty()
    Cfg.fast = args.fast

    if not (args.no_banner or args.stealth):
        show_emblem()

    try:
        st = main_menu(args)
    except KeyboardInterrupt:
        st = None
    if st is None:
        print()
        log("INFO", "systemd", "ingress-monitor.service: Stopped.")
        return

    try:
        while st["day"] <= LAST_DAY:
            save(st)
            ctx, shift = play_day(st)
            result = end_of_day(st, ctx, shift)
            if result:
                game_over(result, st)
                return
            st["day"] += 1
            if st["day"] <= LAST_DAY:
                save(st)
                ask(c("\n  -- presiona Enter para iniciar el siguiente turno --", "gray"))
                print()
        victory(st)
    except KeyboardInterrupt:
        print()
        log("INFO", "systemd", f"Stopping ingress-monitor.service (state saved: day {st['day']})")


if __name__ == "__main__":
    main()
